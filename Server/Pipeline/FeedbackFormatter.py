####################################################################
################# BODY TRACK // SERVER // PIPELINE #################
####################################################################
#################### CLASS: FeesbackFormatter ######################
####################################################################

###############
### IMPORTS ###
###############

from __future__ import annotations
from typing import Dict, TYPE_CHECKING
import inspect
from Server.Data.Session import SessionData
from Server.Utilities.Config.ConfigLoader import ConfigLoader
from Server.Utilities.Config.ConfigParameters import ConfigParameters
from Server.Utilities.Error.ErrorHandler import ErrorHandler
from Server.Utilities.Error.ErrorCode import ErrorCode
from Server.Data.Session.SessionData import SessionData
from Server.Data.Error.DetectedErrorCode import DetectedErrorCode
from Server.Data.Pose.PoseQuality import PoseQuality
from Server.Data.Response.FeedbackResponse import FeedbackCode
if TYPE_CHECKING:
    from Server.Data.History.HistoryData import HistoryData
    from Server.Data.History.HistoryDictKey import HistoryDictKey

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
        - `PoseQualityFeedbackThreshold` :
            Minimum number of consecutive bad frames before pose-quality feedback is allowed.

        - `biomechanicalFeedbackThreshold` :
            Minimum number of repetitions of a biomechanical error before feedback is allowed.

        - `COOLDOWN_FRAMES` :
            Cooldown interval between feedback messages to prevent over-alerting the user.
        """
        self.PoseQualityFeedbackThreshold:int = ConfigLoader().get([
            ConfigParameters.Major.FEEDBACK, ConfigParameters.Minor.POSE_QUALITY_FEEDBACK_THRESHOLD])
        self.biomechanicalFeedbackThreshold:int = ConfigLoader().get([
            ConfigParameters.Major.FEEDBACK, ConfigParameters.Minor.BIO_FEEDBACK_THRESHOLD])
        self.COOLDOWN_FRAMES:int = ConfigLoader().get([
            ConfigParameters.Major.FEEDBACK, ConfigParameters.Minor.FEEDBACK_COOLDOWN_FRAMES])

    ####################################
    ### SELECT FEEDBACK MESSAGE TYPE ###
    ####################################
    def select_feedback_message(self, session:SessionData) -> FeedbackCode:
        """
        ### Brief:
        Determines which feedback message should be returned for the current frame.

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
        history:HistoryData = session.history_data
        current_state_ok:bool = history.is_state_ok()   
        #Check biomechanical issues
        if current_state_ok :
            biomechanical_feedback:FeedbackCode = self._select_biomechanical_feedback(history)
            if biomechanical_feedback is FeedbackCode.SILENT or biomechanical_feedback is FeedbackCode.VALID:
                return biomechanical_feedback
            else:
                if self._is_allowed_to_return_feedback(history): return biomechanical_feedback
                else: return FeedbackCode.SILENT
        else :
            pose_feedback:FeedbackCode = self._select_pose_quality_feedback(history)
            if pose_feedback is FeedbackCode.SILENT :
                return pose_feedback
            else:
                # Allow biomechanical feedback only if cooldown passed
                if self._is_allowed_to_return_feedback(history): return pose_feedback
                else: return FeedbackCode.SILENT
        
    ####################################
    ### SELECT POSE QUALITY FEEDBACK ###
    ####################################
    def _select_pose_quality_feedback(self, history:HistoryData) -> FeedbackCode:
        """
        ### Brief:
        Determines whether pose-quality feedback should be issued.

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
        if history.is_state_ok():
            return None
        frames_since_last_valid:int = history.get_frames_since_last_valid()
        if frames_since_last_valid < self.PoseQualityFeedbackThreshold:
            return FeedbackCode.SILENT
        bad_frame_streak:dict[str, int] = history.get_bad_frame_streaks()
        worst_quality:PoseQuality = max(bad_frame_streak, key=bad_frame_streak.get)
        return FeedbackCode.from_pose_quality(worst_quality)        
    
    #####################################
    ### SELECT BIOMECHANICAL FEEDBACK ###
    #####################################
    def _select_biomechanical_feedback(self, history:HistoryData) -> FeedbackCode:
        """
        ### Brief:
        Determines whether biomechanical feedback should be issued.

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
        if not history.is_state_ok():
            return None
        biomechanical_streaks:dict[str, int] = history.get_error_streaks()
        worst_error_streak = max(biomechanical_streaks, key=biomechanical_streaks.get)

        if biomechanical_streaks[worst_error_streak] < self.biomechanicalFeedbackThreshold:
            return FeedbackCode.SILENT
        detected_enum = DetectedErrorCode[worst_error_streak]
        return FeedbackCode.from_detected_error(detected_enum)
    
    #####################################
    ### IS ALLOWED TO RETURN FEEDBACK ###
    #####################################
    def _is_allowed_to_return_feedback(self, history: HistoryData) -> bool:
        """
        ### Brief:
        Evaluates whether the cooldown period since the last feedback has passed.

        ### Logic:
        Uses the history-managed counter `get_frames_since_last_feedback()`.

        ### Arguments:
        - `history` (HistoryData): Holds cooldown counters.

        ### Returns:
        - `bool`: `True` if cooldown passed, otherwise `False`.
        """
        frames_since_last_feedback = history.get_frames_since_last_feedback()
        if frames_since_last_feedback >= self.COOLDOWN_FRAMES:
            return True
        else:
            return False