####################################################################
################# BODY TRACK // SERVER // PIPELINE #################
####################################################################
#################### CLASS: FeedbackFormatter ######################
####################################################################

###############
### IMPORTS ###
###############
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Set, Any, List
import inspect

from Utilities.Error.ErrorHandler      import ErrorHandler
from Utilities.Error.ErrorCode         import ErrorCode
from Utilities.Config.ConfigLoader     import ConfigLoader
from Utilities.Config.ConfigParameters import ConfigParameters
from Utilities.Logger                  import Logger
from Data.Session.SessionData          import SessionData
from Data.Error.DetectedErrorCode      import DetectedErrorCode
from Data.Pose.PoseQuality             import PoseQuality
from Data.Response.FeedbackResponse    import FeedbackCode
from Data.Session                      import SessionData
from Data.History.HistoryDictKey       import HistoryDictKey

if TYPE_CHECKING:
    from Data.History.HistoryData import HistoryData

################################
### FEEDBACK FORMATTER CLASS ###
################################
class FeedbackFormatter:
    """
    ### Description:
    The `FeedbackFormatter` encapsulates all high-level logic for deciding **which
    feedback message** should be sent to the client for the current frame.

    This class merges:
        - Pose-quality feedback (tracked by `PoseQualityManager`)
        - Biomechanical feedback (tracked by `ErrorDetector`)
        - Cooldown logic (managed inside `HistoryData`)

    ### Notes:
    - The formatter is **stateless** — all temporal state is pulled from `HistoryData`.
    - Always returns a `FeedbackCode` (never `None`).
    - The client decides whether to display the message.
    """
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self):
        """
        ### Brief:
        The `__init__` method initializes the `FeedbackFormatter` instance
        by loading all feedback-related threshold values from the configuration.
     """
        try:
            self.retrieve_configurations()
            Logger.info("FeedbackFormatter initialized successfully.")
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.FEEDBACK_FORMATTER_INIT_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception": type(e).__name__,
                    "Reason": "Failed loading configuration thresholds."
                }
            )

    ##########################
    ### CONSTRUCT FEEDBACK ###
    ##########################
    def construct_feedback(self, session:SessionData) -> FeedbackCode:
        """
        ### Brief:
        The `construct_feedback` methoddetermines which feedback message
        should be returned for the current frame.

        ### Decision Pipeline:
        1. Validate history state
        2. Check pose-quality feedback (highest priority)
        3. Check biomechanical feedback
        4. Check positive reinforcement (VALID)
        5. Otherwise return SILENT
        
        ### Arguments:
        - `session` (SessionData): Contains all runtime session data including history.

        ### Returns:
        - `FeedbackCode`: A system, pose-quality, biomechanical, or silent feedback code.
        """
        try:
            current_state_ok:bool = session.get_history().is_state_ok()  

            # Check biomechanical issues.
            if not current_state_ok:
                return self._handle_pose_quality_feedback(session)
            else:
                return self._handle_biomechanical_feedback(session)
            
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.FEEDBACK_CONSTRUCTION_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception": type(e).__name__,
                    "Reason": str(e)
                }
            )

    ####################################
    ### HANDLE POSE QUALITY FEEDBACK ###
    ####################################
    def _handle_pose_quality_feedback(self, session:SessionData) -> FeedbackCode:
        """
        ### Brief:
        The `_handle_pose_quality_feedback` method determines whether pose-quality
        feedback should be issued.

        ### Logic:
        - If the pose is currently OK return `None` (indicates biomechanical stage should run).
        - Otherwise:
            1. Count how many consecutive bad frames have occurred (`get_frames_since_last_valid()`).
            2. If below threshold return `FeedbackCode.SILENT`.
            3. Identify the most frequent pose-quality issue in the streak.
            4. Convert that issue to the matching `FeedbackCode`.

        ### Arguments:
        - `session` (SessionData): Provides history data for pose-quality evaluation.

        ### Returns:
        - `FeedbackCode`: Pose-quality feedback or `SILENT`.
        """
        try:
            try:
                history:HistoryData = session.get_history()
            except Exception as e:
                ErrorHandler.handle(
                    error=ErrorCode.POSE_QUALITY_FEEDBACK_SELECTION_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Exception": type(e).__name__,
                        "Reason": "Failed retrieving HistoryData from SessionData."
                    }
                )
                return FeedbackCode.SILENT

            try:
                # Check if pose is currently valid.
                frames_since_last_valid:int = history.get_frames_since_last_valid()
                if frames_since_last_valid < self.pose_quality_feedback_threshold:
                    session.get_last_frame_trace().add_event(
                        stage="FeedbackFormatter",
                        success=True,
                        result_type="Not Enough Valid Frames Sent So Far",
                        result={"Frames Since Last Valid": frames_since_last_valid, "Threshold": self.pose_quality_feedback_threshold}
                    )
                    return FeedbackCode.SILENT
            except Exception as e:
                ErrorHandler.handle(
                    error=ErrorCode.POSE_QUALITY_FEEDBACK_SELECTION_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Exception": type(e).__name__,
                        "Reason": "Failed retrieving frames since last valid from HistoryData."
                    }
                )
                return FeedbackCode.SILENT
            try:
                # If cooldown not passed, return SILENT.
                if not self._is_cooldown_passed(history):
                    session.get_last_frame_trace().add_event(
                        stage="FeedbackFormatter",
                        success=True,
                        result_type="Cooldown Not Passed",
                        result={"Frames Since Last Feedback": history.get_frames_since_last_feedback(), "Cooldown Frames": self.cooldown_frames}
                    )
                    return FeedbackCode.SILENT
            except Exception as e:
                ErrorHandler.handle(
                    error=ErrorCode.POSE_QUALITY_FEEDBACK_SELECTION_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Exception": type(e).__name__,
                        "Reason": "Failed retrieving frames since last feedback from HistoryData."
                    }
                )
                return FeedbackCode.SILENT
            
            try:
                # Select worst pose-quality issue.
                bad_frame_streak:Dict[str, int] = history.get_bad_frame_streaks()
                worst_quality:str = max(bad_frame_streak, key=bad_frame_streak.get)
            except Exception as e:
                ErrorHandler.handle(
                    error=ErrorCode.POSE_QUALITY_FEEDBACK_SELECTION_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Exception": type(e).__name__,
                        "Reason": "Failed retrieving bad frame streaks from HistoryData."
                    }
                )
                return FeedbackCode.SILENT
            
            # Convert to FeedbackCode and return it.
            session.get_last_frame_trace().add_event(
                stage="FeedbackFormatter",
                success=True,
                result_type="Pose Quality Feedback Selected",
                result={"Worst Pose Quality": worst_quality, "Streak Length": bad_frame_streak[worst_quality]}
            )
            return FeedbackCode.from_pose_quality(worst_quality)        
        
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.POSE_QUALITY_FEEDBACK_SELECTION_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception": type(e).__name__,
                    "Reason": str(e)
                }
            )
            return FeedbackCode.SILENT    

    #####################################
    ### HANDLE BIOMECHANICAL FEEDBACK ###
    #####################################
    def _handle_biomechanical_feedback(self, session:SessionData) -> FeedbackCode:
        """
        ### Brief:
        The `_handle_biomechanical_feedback` method determines whether
        biomechanical feedback should be issued.

        ### Logic:
        - If the state is not OK (pose-quality error exists) → biomechanical feedback is irrelevant.
        - Extract biomechanical error streaks (`get_error_streaks()`).
        - Find the most frequent biomechanical error.
        - If below biomechanical threshold → return `SILENT`.
        - Convert the selected error into a `FeedbackCode`.
        - If that feedback code has already been issued in the current rep → return `SILENT`.
        - Otherwise, return the feedback code.

        ### Arguments:
        - `session` (SessionData): Provides history data for biomechanical evaluation.

        ### Returns:
        - `FeedbackCode`: A biomechanical feedback code or `SILENT`.
        """
        try:
            try:
                history:HistoryData = session.get_history()
            except Exception as e:
                ErrorHandler.handle(
                    error=ErrorCode.BIOMECHANICAL_FEEDBACK_SELECTION_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Exception": type(e).__name__,
                        "Reason": "Failed retrieving HistoryData from SessionData."
                    }
                )
                return FeedbackCode.SILENT
            try:
                # Get current rep data.
                current_rep:Dict[str, Any] = history.get_current_rep()
                if not current_rep:
                    session.get_last_frame_trace().add_event(
                        stage="FeedbackFormatter",
                        success=True,
                        result_type="No Current Rep Data",
                        result=None
                    )
                    return FeedbackCode.SILENT
            except Exception as e:
                ErrorHandler.handle(
                    error=ErrorCode.BIOMECHANICAL_FEEDBACK_SELECTION_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Exception": type(e).__name__,
                        "Reason": "Failed retrieving current rep data from HistoryData."
                    }
                )
                return FeedbackCode.SILENT         
            try:
                # Get biomechanical errors in current rep.
                rep_errors:List[str] = current_rep[HistoryDictKey.CurrentRep.ERRORS]
            except Exception as e:
                ErrorHandler.handle(
                    error=ErrorCode.BIOMECHANICAL_FEEDBACK_SELECTION_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Exception": type(e).__name__,
                        "Reason": "Failed retrieving biomechanical errors from current rep data."
                    }
                )
                return FeedbackCode.SILENT
            
            # If no biomechanical errors, return VALID.
            if not rep_errors:
                session.get_last_frame_trace().add_event(
                    stage="FeedbackFormatter",
                    success=True,
                    result_type="No Biomechanical Errors Detected",
                    result=None
                )
                return FeedbackCode.VALID
            # If there are errors but cooldown not passed, return SILENT.
            if not self._is_cooldown_passed(history):
                session.get_last_frame_trace().add_event(
                    stage="FeedbackFormatter",
                    success=True,
                    result_type="Cooldown Not Passed",
                    result={"Frames Since Last Feedback": history.get_frames_since_last_feedback(), "Cooldown Frames": self.cooldown_frames}
                )
                return FeedbackCode.SILENT
            try:
                # Select worst biomechanical error.
                biomechanical_streaks:Dict[str, int] = history.get_error_streaks()
                if not biomechanical_streaks:
                    session.get_last_frame_trace().add_event(
                        stage="FeedbackFormatter",
                        success=True,
                        result_type="No Biomechanical Error Streaks Found",
                        result=None
                    )
                    return FeedbackCode.SILENT
                worst_error_streak:str = max(biomechanical_streaks, key=biomechanical_streaks.get)
            except Exception as e:
                ErrorHandler.handle(
                    error=ErrorCode.BIOMECHANICAL_FEEDBACK_SELECTION_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Exception": type(e).__name__,
                        "Reason": "Failed retrieving biomechanical error streaks from HistoryData."
                    }
                )
                return FeedbackCode.SILENT
            try:
                # If below threshold, return SILENT.
                if biomechanical_streaks[worst_error_streak] < self.biomechanical_feedback_threshold:
                    session.get_last_frame_trace().add_event(
                        stage="FeedbackFormatter",
                        success=True,
                        result_type="Biomechanical Error Streak Below Threshold",
                        result={"Worst Error": worst_error_streak, "Streak Length": biomechanical_streaks[worst_error_streak], "Threshold": self.biomechanical_feedback_threshold}
                    )
                    return FeedbackCode.SILENT
            except Exception as e:
                ErrorHandler.handle(
                    error=ErrorCode.BIOMECHANICAL_FEEDBACK_SELECTION_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Exception": type(e).__name__,
                        "Reason": "Failed retrieving biomechanical error streak length from HistoryData."
                    }
                )
                return FeedbackCode.SILENT
            # Convert to FeedbackCode and check if already notified in rep.
            detected_enum = DetectedErrorCode[worst_error_streak]
            try:
                notified_errors_in_rep:Set[FeedbackCode] = current_rep[HistoryDictKey.CurrentRep.NOTIFIED]
            except Exception as e:
                ErrorHandler.handle(
                    error=ErrorCode.BIOMECHANICAL_FEEDBACK_SELECTION_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Exception": type(e).__name__,
                        "Reason": "Failed retrieving notified errors in rep from current rep data."
                    }
                )
                return FeedbackCode.SILENT
            try:
                feedback_code = FeedbackCode.from_detected_error(detected_enum)
            except Exception as e:
                ErrorHandler.handle(
                    error=ErrorCode.BIOMECHANICAL_FEEDBACK_SELECTION_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Exception": type(e).__name__,
                        "Reason": "Failed converting DetectedErrorCode to FeedbackCode."
                    }
                )
                return FeedbackCode.SILENT
            # If already notified in rep, return SILENT.
            if feedback_code in notified_errors_in_rep:
                session.get_last_frame_trace().add_event(
                    stage="FeedbackFormatter",
                    success=True,
                    result_type="Biomechanical Feedback Already Notified in Rep",
                    result={"Feedback Code": feedback_code.name}
                )
                return FeedbackCode.SILENT
            # Otherwise, return the feedback code.
            else:
                session.get_last_frame_trace().add_event(
                    stage="FeedbackFormatter",
                    success=True,
                    result_type="Biomechanical Feedback Selected",
                    result={"Worst Biomechanical Error": worst_error_streak, "Streak Length": biomechanical_streaks[worst_error_streak]}
                )
                return feedback_code
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.BIOMECHANICAL_FEEDBACK_SELECTION_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception": type(e).__name__,
                    "Reason": str(e)
                }
            )
            session.get_last_frame_trace().add_event(
                stage="FeedbackFormatter",
                success=False,
                result_type="Biomechanical Feedback Selection Error",
                result={"Exception": type(e).__name__, "Message": str(e)}
            )
            return FeedbackCode.SILENT       

    ##########################
    ### IS COOLDOWN PASSED ###
    ##########################
    def _is_cooldown_passed(self, history:HistoryData) -> bool:
        """
        The `_is_cooldown_passed` method checks if the cooldown period has passed
        since the last feedback was issued.

        ### Arguments:
        - `history` (HistoryData): Provides frame count since last feedback.

        ### Returns:
        - `bool`: `True` if cooldown period has passed, `False` otherwise.
        """
        return history.get_frames_since_last_feedback() >= self.cooldown_frames
    
    ###############################
    ### RETRIEVE CONFIGURATIONS ###
    ###############################
    def retrieve_configurations(self) -> None:
        """
        ### Brief:
        The `retrieve_configurations` method loads all feedback-related
        threshold values from the configuration file.
        """
        try:
            self.pose_quality_feedback_threshold:int = ConfigLoader().get([
                ConfigParameters.Major.FEEDBACK,
                ConfigParameters.Minor.POSE_QUALITY_FEEDBACK_THRESHOLD
            ])
            self.biomechanical_feedback_threshold:int = ConfigLoader().get([
                ConfigParameters.Major.FEEDBACK,
                ConfigParameters.Minor.BIO_FEEDBACK_THRESHOLD
            ])

            self.cooldown_frames:int = ConfigLoader.get([
            ConfigParameters.Major.FEEDBACK,
            ConfigParameters.Minor.FEEDBACK_COOLDOWN_FRAMES
            ])
            Logger.info("Retrieved configurations successfully")
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.FEEDBACK_CONFIG_RETRIEVAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception": type(e).__name__,
                    "Reason": "Failed loading feedback configuration thresholds."
                }
            )