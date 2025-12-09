# ####################################################################
# ################# BODY TRACK // SERVER // PIPELINE #################
# ####################################################################
# #################### CLASS: FeesbackFormatter ######################
# ####################################################################

# ###############
# ### IMPORTS ###
# ###############

# from __future__ import annotations
# from typing import Dict, TYPE_CHECKING
# import inspect
# from Server.Data.Session import SessionData
# from Server.Utilities.Config.ConfigLoader import ConfigLoader
# from Server.Utilities.Config.ConfigParameters import ConfigParameters
# from Server.Utilities.Error.ErrorHandler import ErrorHandler
# from Server.Utilities.Error.ErrorCode import ErrorCode
# from Server.Data.Session.SessionData import SessionData
# from Server.Data.Error.DetectedErrorCode import DetectedErrorCode
# from Server.Data.Pose.PoseQuality import PoseQuality
# from Server.Data.Response.FeedbackResponse import FeedbackCode
# if TYPE_CHECKING:
#     from Server.Data.History.HistoryData import HistoryData
#     from Server.Data.History.HistoryDictKey import HistoryDictKey



# ################################
# ### FEEDBACK FORMATTER CLASS ###
# ################################

# class FeedbackFormatter:
#     """
#     """

#     #########################
#     ### CLASS CONSTRUCTOR ###
#     #########################

#     def __init__(self):
#         """
#         ### Brief:
#         The `__init__` method initializes the `FeedbackFormatter` instance.
#         ### Args:
#         """
#         self.PoseQualityFeedbackThreshold : int = ConfigLoader().get([
#             ConfigParameters.Major.POSE_QUALITY_FEEDBACK_THRESHOLD, ConfigParameters.Minor.VALUE])
#         self.PoseQualityFeedbackThreshold : int = ConfigLoader().get([
#             ConfigParameters.Major.DETECTED_ERROR_FEEDBACK_THRESHOLD, ConfigParameters.Minor.VALUE])
#         self.COOLDOWN_FRAMES : int = ConfigLoader().get([
#             ConfigParameters.Major.FEEDBACK_COOLDOWN_FRAMES, ConfigParameters.Minor.VALUE])

#     ####################################
#     ### SELECT FEEDBACK MESSAGE TYPE ###
#     ####################################
#     def select_feedback_message(session : SessionData) -> FeedbackCode:
#         """
#         """
#         history:HistoryData = session.history_data
#         current_state_ok : bool = history.is_state_ok()   
#         if current_state_ok :
#             biomechanical_feedback : FeedbackCode = self._select_biomechanical_feedback(history)
#             if biomechanical_feedback == FeedbackCode.SILENT 
#                 return biomechanical_feedback
            
#         # 1. Check for PoseQuality problems
#         pose_feedback : FeedbackCode = self._select_pose_quality_feedback(history)
#         if pose_feedback is not None :
#             return self._apply_cooldown(history, pose_feedback)
        
#         # 2. Check for Biomechanical errors
#         biomechanical_feedback : FeedbackCode = self._select_biomechanical_feedback(history)
#         if biomechanical_feedback is not None :
#             return self._apply_cooldown(history, biomechanical_feedback)

#         # 3. If no issues detected, return VALID feedback
#         return self._apply_cooldown(history, FeedbackCode.VALID)
    
#     ####################################
#     ### SELECT POSE QUALITY FEEDBACK ###
#     ####################################
#     def _select_pose_quality_feedback(self, history : HistoryData) -> FeedbackCode:
#         """
#         """
#         if history.is_state_ok():
#             return None
#         frames_since_last_valid : int = history.get_frames_since_last_valid()
#         if frames_since_last_valid < self.PoseQualityFeedbackThreshold:
#             return FeedbackCode.SILENT
#         bad_frame_streak : dict[str, int] = history.get_bad_frame_streak()
#         worst_quality : PoseQuality = max(bad_frame_streak, key=bad_frame_streak.get)
#         return FeedbackCode.from_pose_quality(worst_quality)        
    
#     #####################################
#     ### SELECT BIOMECHANICAL FEEDBACK ###
#     #####################################
#     def _select_biomechanical_feedback(self, history : HistoryData) -> FeedbackCode:
#         """
#         """
#         if not history.is_state_ok():
#             return None
#         counters : dict[str, int] = history.get_error_counters()
#         if not counters:
#             return FeedbackCode.SILENT
#         worst_error_streak = max(counters, key=counters.get)
#         detected_enum = DetectedErrorCode[worst_error]
#         return FeedbackCode.from_detected_error(detected_enum)
    
#     ######################
#     ### APPLY COOLDOWN ###
#     ######################
#     def _apply_cooldown(self, history: HistoryData, new_code: FeedbackCode) -> FeedbackCode:
#         """
#         Ensures feedback is not shown too frequently.
#         Uses history-data for per-session state.
#         Always returns a FeedbackCode (including SILENT).
#         """

#         last_code = history.history.last_feedback_code
#         frames_since = history.history.frames_since_last_feedback

#         # If new feedback is different — show immediately
#         if new_code != last_code:
#             history.history.last_feedback_code = new_code
#             history.history.frames_since_last_feedback = 0
#             return new_code

#         # If same feedback but cooldown passed → return again
#         if frames_since >= self.COOLDOWN_FRAMES:
#             history.history.frames_since_last_feedback = 0
#             return new_code

#         # Otherwise, still in cooldown → return SILENT
#         return FeedbackCode.SILENT
        
             


























# frames_since_last_valid : int = history.get_frames_since_last_valid()
#             if frames_since_last_valid >= self.PoseQualityFeedbackThreshold:
#                 bad_frame_streak : dict[str, int] = history.get_bad_frame_streak()
#                 worst_quality : PoseQuality = max(bad_frame_streak, key=bad_frame_streak.get)
#                 return worst_quality
#             else:
#                 return FeedbackMessageType.NO_FEEDBACK

