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

from Server.Utilities.Config.ConfigLoader     import ConfigLoader
from Server.Utilities.Config.ConfigParameters import ConfigParameters
from Server.Utilities.Logger                  import Logger
from Server.Data.Session.SessionData          import SessionData
from Server.Data.Error.DetectedErrorCode      import DetectedErrorCode
from Server.Data.Pose.PoseQuality             import PoseQuality
from Server.Data.Response.FeedbackResponse    import FeedbackCode
from Server.Data.Session                      import SessionData
from Server.Utilities.Error.ErrorHandler      import ErrorHandler
from Server.Utilities.Error.ErrorCode         import ErrorCode

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
        - `pose_quality_feedback_threshold` :
            Minimum number of consecutive bad frames before pose-quality feedback is allowed.

        - `biomechanical_feedback_threshold` :
            Minimum number of repetitions of a biomechanical error before feedback is allowed.

        - `cooldown_frames` :
            Cooldown interval between feedback messages to prevent over-alerting the user.
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

        ### Decision Process:
        1. Check whether the pose state is valid (`is_state_ok()`):
            - If **valid**, biomechanical feedback (errors in movement technique) is evaluated first.
            - If **invalid**, pose-quality feedback (visibility, distance, stability issues) is evaluated.

        2. If a feedback code is identified:
            - Return it **only** if the cooldown threshold is satisfied.
            - Otherwise return `FeedbackCode.SILENT`.

        3. If no feedback is required, return `FeedbackCode.SILENT`.

        ### Arguments:
        - `session` (SessionData): Contains all runtime session data including history.

        ### Returns:
        - `FeedbackCode`: A system, pose-quality, biomechanical, or silent feedback code.
        """
        try:
            history:HistoryData = session.history_data
            current_state_ok:bool = history.is_state_ok()  

            # Check biomechanical issues.
            if current_state_ok:
                biomechanical_feedback:FeedbackCode = self._select_biomechanical_feedback(history)
                if biomechanical_feedback is FeedbackCode.SILENT \
                    or biomechanical_feedback is FeedbackCode.VALID:
                    return biomechanical_feedback
                else:
                    if self._is_allowed_to_return_feedback(history): return biomechanical_feedback
                    else:                                            return FeedbackCode.SILENT
            else:
                pose_feedback:FeedbackCode = self._select_pose_quality_feedback(history)
                if pose_feedback is FeedbackCode.SILENT:
                    return pose_feedback
                else:
                    # Allow biomechanical feedback only if cooldown passed.
                    if self._is_allowed_to_return_feedback(history): return pose_feedback
                    else:                                            return FeedbackCode.SILENT
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.FEEDBACK_CONSTRUCTION_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception": type(e).__name__,
                    "Reason": "Unexpected failure in construct_feedback()"
                }
            )
            return FeedbackCode.SILENT
    ####################################
    ### SELECT POSE QUALITY FEEDBACK ###
    ####################################
    def _select_pose_quality_feedback(self, history:HistoryData) -> FeedbackCode:
        """
        ### Brief:
        The `_select_pose_quality_feedback` method determines whether pose-quality
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
                
            if history.is_state_ok(): return None

            frames_since_last_valid:int = history.get_frames_since_last_valid()
            if frames_since_last_valid < self.pose_quality_feedback_threshold:
                return FeedbackCode.SILENT
            else:
                bad_frame_streak:Dict[str, int] = history.get_bad_frame_streaks()
                worst_quality:PoseQuality = max(bad_frame_streak, key=bad_frame_streak.get)
                return FeedbackCode.from_pose_quality(worst_quality)        
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.POSE_QUALITY_FEEDBACK_SELECTION_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Method": "_select_pose_quality_feedback",
                    "Exception": type(e).__name__,
                    "Reason": "Unexpected failure during pose-quality feedback selection."
                }
            )
            return FeedbackCode.SILENT    
    #####################################
    ### SELECT BIOMECHANICAL FEEDBACK ###
    #####################################
    def _select_biomechanical_feedback(self, history:HistoryData) -> FeedbackCode:
        """
        ### Brief:
        The `_select_biomechanical_feedback` method determines whether
        biomechanical feedback should be issued.

        ### Logic:
        - If the state is not OK (pose-quality error exists) → biomechanical feedback is irrelevant.
        - Extract biomechanical error streaks (`get_error_streaks()`).
        - Find the most frequent biomechanical error.
        - If below biomechanical threshold → return `SILENT`.
        - Convert the selected error into a `FeedbackCode`.

        ### Arguments:
        - `history` (HistoryData): Provides biomechanical error streaks.

        ### Returns:
        - `FeedbackCode`: A biomechanical feedback code or `SILENT`.
        """
        try:
                
            if not history.is_state_ok(): return None
            
            biomechanical_streaks:Dict[str, int] = history.get_error_streaks()
            worst_error_streak:str = max(biomechanical_streaks, key=biomechanical_streaks.get)

            if biomechanical_streaks[worst_error_streak] < self.biomechanical_feedback_threshold:
                return FeedbackCode.SILENT
            else:
                detected_enum = DetectedErrorCode[worst_error_streak]
                return FeedbackCode.from_detected_error(detected_enum)
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.BIOMECHANICAL_FEEDBACK_SELECTION_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Method": "_select_biomechanical_feedback",
                    "Exception": type(e).__name__,
                    "Reason": "Unexpected failure during biomechanical feedback selection."
                }
            )
            return FeedbackCode.SILENT       
    #####################################
    ### IS ALLOWED TO RETURN FEEDBACK ###
    #####################################
    def _is_allowed_to_return_feedback(self, history:HistoryData) -> bool:
        """
        ### Brief:
        The `_is_allowed_to_return_feedback` method evaluates whether the
        cooldown period since the last feedback has passed.

        ### Arguments:
        - `history` (HistoryData): Holds cooldown counters.

        ### Returns:
        - `bool`: `True` if cooldown passed, otherwise `False`.
        """
        frames_since_last_feedback:int = history.get_frames_since_last_feedback()

        if frames_since_last_feedback >= self.cooldown_frames: return True
        else:                                                  return False
    
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
            self.cooldown_frames:int = ConfigLoader().get([
                ConfigParameters.Major.FEEDBACK,
                ConfigParameters.Minor.FEEDBACK_COOLDOWN_FRAMES
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