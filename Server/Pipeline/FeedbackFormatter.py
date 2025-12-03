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
from Server.Data.Phase.PhaseType import PhaseType
from Server.Data.Session import SessionData
from Server.Data.Session.ExerciseType import ExerciseType
from Server.Utilities.Config.ConfigLoader import ConfigLoader
from Server.Utilities.Config.ConfigParameters import ConfigParameters
from Server.Utilities.Error.ErrorHandler import ErrorHandler
from Server.Utilities.Error.ErrorCode import ErrorCode
from Server.Data.Session.SessionData import SessionData
from Server.Data.Error.ErrorMappings import ErrorMappings
from Server.Data.Error.DetectedErrorCode import DetectedErrorCode
from Server.Data.Pose.PoseQuality import PoseQuality
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

    ####################################
    ### SELECT FEEDBACK MESSAGE TYPE ###
    ####################################
    def select_feedback_message(session : SessionData) -> PoseQuality | DetectedErrorCode | ErrorCode:
        """
        ### Brief:
        The `select_feedback_message` method determines the feedback message to provide-
        based on the session history. It prioritizes feedback in the following order:
            1. PoseQuality problems
            2. Biomechanical errors
            3. No feedback

        ### Args:
        - `history` (HistoryData): The session's history data.

        ### Returns:
        - `PoseQuality | DetectedErrorCode | ErrorCode`: The selected feedback message type.

        """
        history:HistoryData = session.history_data
        if not history.is_state_ok():
            frames_since_last_valid : int = history.get_frames_since_last_valid()
            if frames_since_last_valid >= self.PoseQualityFeedbackThreshold:
                bad_frame_streak : dict[str, int] = history.get_bad_frame_streak()
                worst_quality : PoseQuality = max(bad_frame_streak, key=bad_frame_streak.get)
                return worst_quality
            else:
                return FeedbackMessageType.NO_FEEDBACK
        elif 


