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
    """

    #########################
    ### CLASS CONSTRUCTOR ###
    #########################

    def __init__(self):
        """
        ### Brief:
        The `__init__` method initializes the `FeedbackFormatter` instance.
        ### Args:
        """
        self.PoseQualityFeedbackThreshold : int = ConfigLoader().get([
            ConfigParameters.Major.POSE_QUALITY_FEEDBACK_THRESHOLD, ConfigParameters.Minor.VALUE])
        self.COOLDOWN_FRAMES : int = ConfigLoader().get([
            ConfigParameters.Major.FEEDBACK_COOLDOWN_FRAMES, ConfigParameters.Minor.VALUE])

    ####################################
    ### SELECT FEEDBACK MESSAGE TYPE ###
    ####################################
    def select_feedback_message(self, session : SessionData) -> FeedbackCode:
        """
        """
        history:HistoryData = session.history_data
        current_state_ok : bool = history.is_state_ok()   
        if current_state_ok :
            biomechanical_feedback : FeedbackCode = self._select_biomechanical_feedback(history)
            if biomechanical_feedback is FeedbackCode.SILENT or biomechanical_feedback is FeedbackCode.VALID:
                return biomechanical_feedback
            else:
                if self._is_allowed_to_return_feedback(history): return biomechanical_feedback
                else: return FeedbackCode.SILENT
        else :
            pose_feedback : FeedbackCode = self._select_pose_quality_feedback(history)
            if pose_feedback is FeedbackCode.SILENT :
                return pose_feedback
            else:
                if self._is_allowed_to_return_feedback(history): return pose_feedback
                else: return FeedbackCode.SILENT
        
    ####################################
    ### SELECT POSE QUALITY FEEDBACK ###
    ####################################
    def _select_pose_quality_feedback(self, history : HistoryData) -> FeedbackCode:
        """
        """
        if history.is_state_ok():
            return None
        frames_since_last_valid : int = history.get_frames_since_last_valid()
        if frames_since_last_valid < self.PoseQualityFeedbackThreshold:
            return FeedbackCode.SILENT
        bad_frame_streak : dict[str, int] = history.get_bad_frame_streak()
        worst_quality : PoseQuality = max(bad_frame_streak, key=bad_frame_streak.get)
        return FeedbackCode.from_pose_quality(worst_quality)        
    
    #####################################
    ### SELECT BIOMECHANICAL FEEDBACK ###
    #####################################
    def _select_biomechanical_feedback(self, history : HistoryData) -> FeedbackCode:
        """
        """
        if not history.is_state_ok():
            return None
        biomechanical_streaks : dict[str, int] = history.get_error_streaks()
        worst_error_streak = max(biomechanical_streaks, key=biomechanical_streaks.get)

        if biomechanical_streaks[worst_error_streak] < self.PoseQualityFeedbackThreshold:
            return FeedbackCode.SILENT
        detected_enum = DetectedErrorCode[worst_error_streak]
        return FeedbackCode.from_detected_error(detected_enum)
    
    #####################################
    ### IS ALLOWED TO RETURN FEEDBACK ###
    #####################################
    def _is_allowed_to_return_feedback(self, history: HistoryData) -> bool:
        """
        """
        frames_since_last_feedback = history.get_frames_since_last_feedback()
        if frames_since_last_feedback >= self.COOLDOWN_FRAMES:
            return True
        else:
            return False

        
             

























