####################################################################
################# BODY TRACK // SERVER // PIPELINE #################
####################################################################
#################### CLASS: FeedbackFormatter ######################
####################################################################

###############
### IMPORTS ###
###############
from __future__ import annotations
from typing     import TYPE_CHECKING, Dict
import inspect

from Server.Utilities.Error.ErrorHandler      import ErrorHandler
from Server.Utilities.Error.ErrorCode         import ErrorCode
from Server.Utilities.Config.ConfigLoader     import ConfigLoader
from Server.Utilities.Config.ConfigParameters import ConfigParameters
from Server.Utilities.Logger                  import Logger
from Server.Data.Session.SessionData          import SessionData
from Server.Data.Error.DetectedErrorCode      import DetectedErrorCode
from Server.Data.Pose.PoseQuality             import PoseQuality
from Server.Data.Response.FeedbackResponse    import FeedbackCode
from Server.Data.Session                      import SessionData
from Server.Data.History.HistoryDictKey       import HistoryDictKey


if TYPE_CHECKING:
    from Server.Data.History.HistoryData import HistoryData

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
        Loads all feedback-related threshold values from the configuration.

        ### Thresholds Loaded:
        - Pose-quality feedback threshold (frames)
        - Biomechanical feedback threshold (frames)
        - Pose-quality cooldown frames
        - Biomechanical cooldown frames
        - VALID feedback cooldown frames
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
            history:HistoryData = session.get_history()
            current_state_ok:bool = history.is_state_ok()  

            # Check biomechanical issues.
            if not current_state_ok:
                return self._handle_pose_quality_feedback(history)
            else:
                return self._handle_biomechanical_feedback(history)
            
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
    def _handle_pose_quality_feedback(self, history:HistoryData) -> FeedbackCode:
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
        - `history` (HistoryData): Provides pose-quality streaks and state.

        ### Returns:
        - `FeedbackCode`: Pose-quality feedback or `SILENT`.
        """
        try:
            frames_since_last_valid:int = history.get_frames_since_last_valid()
            if frames_since_last_valid < self.pose_quality_feedback_threshold:
                return FeedbackCode.SILENT
            if not self._cooldown_passed(history):
                return FeedbackCode.SILENT
            
            
            bad_frame_streak:Dict[str, int] = history.get_bad_frame_streaks()

            worst_quality:PoseQuality = max(bad_frame_streak, key=bad_frame_streak.get)

            return FeedbackCode.from_pose_quality(worst_quality)        
        
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.POSE_QUALITY_FEEDBACK_SELECTION_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception": type(e).__name__,
                    "Reason": "Unexpected failure during pose-quality feedback selection."
                }
            )
            return FeedbackCode.SILENT    

    #####################################
    ### HANDLE BIOMECHANICAL FEEDBACK ###
    #####################################
    def _handle_biomechanical_feedback(self, history:HistoryData) -> FeedbackCode:
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
        - `history` (HistoryData): Provides biomechanical error streaks.

        ### Returns:
        - `FeedbackCode`: A biomechanical feedback code or `SILENT`.
        """
        try:            
            current_rep : dict[str, any] = history.get_current_rep()
            rep_errors:Dict[str, any] = current_rep[HistoryDictKey.CurrentRep.ERRORS]
            if not rep_errors:
                return FeedbackCode.VALID
            if not self._cooldown_passed(history):
                return FeedbackCode.SILENT
            
            biomechanical_streaks:Dict[str, int] = history.get_error_streaks()
            if not biomechanical_streaks: return FeedbackCode.SILENT
            worst_error_streak:str = max(biomechanical_streaks, key=biomechanical_streaks.get)
            
            if biomechanical_streaks[worst_error_streak] < self.biomechanical_feedback_threshold:
                return FeedbackCode.SILENT
                        
            
            detected_enum = DetectedErrorCode[worst_error_streak]
            notified_errors_in_rep : set[FeedbackCode] = current_rep[HistoryDictKey.CurrentRep.NOTIFIED_ERRORS]
            feedback_code = FeedbackCode.from_detected_error(detected_enum)
            if feedback_code in notified_errors_in_rep:
                return FeedbackCode.SILENT
            else:
                return feedback_code
        
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.BIOMECHANICAL_FEEDBACK_SELECTION_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception": type(e).__name__,
                    "Reason": "Unexpected failure during biomechanical feedback selection."
                }
            )
            return FeedbackCode.SILENT       


    ############################
    ### COOLDOWN EVALUATIONS ###
    ############################
    """
    ### Brief:
    The cooldown evaluation methods check whether enough frames have passed
    since the last feedback was issued, based on the configured cooldown frames.
    """
    def _cooldown_passed(self, history: HistoryData) -> bool:
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

            self.cooldown_frames: int = ConfigLoader.get([
            ConfigParameters.Major.FEEDBACK,
            ConfigParameters.Minor.COOLDOWN_FRAMES
            ])
            
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.FEEDBACK_CONFIG_RETRIEVAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception": type(e).__name__,
                    "Reason": "Failed loading feedback configuration thresholds."
                }
            )