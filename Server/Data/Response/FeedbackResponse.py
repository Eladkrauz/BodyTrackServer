############################################################
######### BODY TRACK // SERVER // DATA // RESPONSE #########
############################################################
################## CLASS: FeedbackResponse #################
############################################################

###############
### IMPORTS ###
###############
from enum import Enum as enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
from Server.Data.Pose.PoseQuality import PoseQuality
from Server.Data.Error.DetectedErrorCode import DetectedErrorCode


####################################
### FEEDBACK RESPONSE DICT ALIAS ###
####################################
FeedbackResponseDict = Dict[str, Any]

################################
### FEEDBACK CODE ENUM CLASS ###
################################
class FeedbackCode(enum):
    """
    ### Description:
    The `FeedbackCode` enum class represents all possible feedback codes
    that can be returned by the system during exercise analysis.

    Each feedback code is associated with a unique integer code and a descriptive message.

    ### Categories:
    1. System States: General system states such as VALID and SILENT.
    2. Pose Quality Errors: Issues related to the quality of the detected pose.
    3. Squat Errors: Specific errors related to squat exercise form.
    4. Biceps Curl Errors: Specific errors related to biceps curl exercise form.
    5. Lateral Raise Errors: Specific errors related to lateral raise exercise form.
    """
    #####################
    ### SYSTEM STATES ###
    #####################
    VALID                           = (0,   "")
    SILENT                          = (1,   "")

    ###########################
    ### POSE QUALITY ERRORS ###
    ###########################
    NO_PERSON                       = (100, "I can't see you — please step into the frame.")
    LOW_VISIBILITY                  = (101, "The camera can't see you clearly — improve lighting.")
    PARTIAL_BODY                    = (102, "Move back a bit — I need to see your full body.")
    TOO_FAR                         = (103, "You're too far away — step closer.")
    TOO_CLOSE                       = (104, "You're too close — please take a small step back.")
    UNSTABLE                        = (105, "The camera view is unstable — try holding your position.")

    ####################
    ### SQUAT ERRORS ###
    ####################
    SQUAT_NOT_DEEP_ENOUGH           = (3000, "Go a bit deeper in your squat.")
    SQUAT_TOO_DEEP                  = (3001, "You're going too deep — rise slightly.")
    SQUAT_KNEES_INWARD              = (3002, "Keep your knees from collapsing inward.")
    SQUAT_KNEES_OUTWARD             = (3003, "Don't push your knees too far outward.")
    SQUAT_HEELS_OFF_GROUND          = (3004, "Keep your heels down during the squat.")
    SQUAT_WEIGHT_FORWARD            = (3005, "Shift your weight backward — avoid leaning forward.")
    SQUAT_CHEST_LEAN_FORWARD        = (3006, "Keep your chest more upright.")
    SQUAT_BACK_ROUNDED              = (3007, "Straighten your back — avoid rounding.")
    SQUAT_HIP_SHIFT_LEFT            = (3008, "Your hips are shifting left — keep centered.")
    SQUAT_HIP_SHIFT_RIGHT           = (3009, "Your hips are shifting right — keep centered.")

    ##########################
    ### BICEPS CURL ERRORS ###
    ##########################
    CURL_TOO_SHORT_TOP              = (3100, "Lift a bit higher to complete the curl.")
    CURL_NOT_FULL_FLEXION           = (3101, "Curl your arm fully at the top of the movement.")
    CURL_ELBOWS_MOVING_FORWARD      = (3102, "Keep your elbows close — don't swing them forward.")
    CURL_ELBOWS_MOVING_BACKWARD     = (3103, "Your elbows are drifting back — keep them stable.")
    CURL_LEANING_FORWARD            = (3104, "Stand upright — avoid leaning forward.")
    CURL_LEANING_BACKWARD           = (3105, "Don't lean backward — keep your core stable.")
    CURL_WRIST_NOT_NEUTRAL          = (3106, "Keep your wrists straight during the curl.")

    ############################
    ### LATERAL RAISE ERRORS ###
    ############################
    LATERAL_ARMS_TOO_LOW            = (3200, "Lift your arms a bit higher.")
    LATERAL_ARMS_TOO_HIGH           = (3201, "Don't raise your arms too high — stay in control.")
    LATERAL_ELBOWS_BENT_TOO_MUCH    = (3202, "Straighten your elbows slightly.")
    LATERAL_TORSO_SWAYING           = (3203, "Keep your torso stable — avoid swaying.")
    LATERAL_PARTIAL_REP             = (3204, "Complete the full range of motion for best results.")
    
    ###########
    ### NEW ###
    ###########
    def __new__(cls, code, description):
        obj = object.__new__(cls)
        obj._value_ = code
        obj.description = description
        return obj
    
    #########################
    ### FROM POSE QUALITY ###
    #########################
    @staticmethod
    def from_pose_quality(pose_quality:PoseQuality) -> 'FeedbackCode':
        mapping = {
            PoseQuality.NO_PERSON:      FeedbackCode.NO_PERSON,
            PoseQuality.LOW_VISIBILITY: FeedbackCode.LOW_VISIBILITY,
            PoseQuality.PARTIAL_BODY:   FeedbackCode.PARTIAL_BODY,
            PoseQuality.TOO_FAR:        FeedbackCode.TOO_FAR,
            PoseQuality.TOO_CLOSE:      FeedbackCode.TOO_CLOSE,
            PoseQuality.UNSTABLE:       FeedbackCode.UNSTABLE
        }
        return mapping.get(pose_quality, FeedbackCode.SILENT)
    
    ###########################
    ### FROM DETECTED ERROR ###
    ###########################
    @staticmethod
    def from_detected_error(detected_error:DetectedErrorCode) -> 'FeedbackCode':
        try:
            if detected_error.name is DetectedErrorCode.NO_BIOMECHANICAL_ERROR.name:
                return FeedbackCode.VALID
            if detected_error.name is DetectedErrorCode.NOT_READY_FOR_ANALYSIS.name:
                return FeedbackCode.SILENT
            return FeedbackCode[detected_error.name]
        except KeyError:
            return FeedbackCode.SILENT

@dataclass
###############################
### FEEDBACK RESPONSE CLASS ###
###############################
class FeedbackResponse:
    """
    ### Description:
    The `FeedbackResponse` class represents the feedback provided by the system
    during exercise analysis. It includes a feedback code indicating the type of feedback
    and an optional dictionary for any additional information.
    """
    # Class fields.
    feedback_code:FeedbackCode
    extra_info:Optional[Dict[str, Any]] = None

    ###############
    ### TO DICT ###
    ###############
    def to_dict(self) -> FeedbackResponseDict:
        """
        ### Brief:
        The `to_dict` method converts the FeedbackResponse instance into a dictionary format.

        ### Returns:
        - FeedbackResponseDict: A dictionary containing the feedback code, description,
          and any extra information if available.
        """
        return_dict = {
            "code":        self.feedback_code.value,
            "description": self.feedback_code.description
        }
        if self.extra_info: return_dict["extra_info"] = self.extra_info
        return return_dict