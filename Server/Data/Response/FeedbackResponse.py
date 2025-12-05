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

####################################
### FEEDBACK RESPONSE DICT ALIAS ###
####################################
FeedbackResponseDict = Dict[str, Any]

################################
### FEEDBACK CODE ENUM CLASS ###
################################
class FeedbackCode(enum):
    ############################
    ### SYSTEM STATES (0–99) ###
    ############################

    VALID            = (0,   "")
    SILENT           = (1,   "")   # Returned when no feedback should be displayed


    ##############################
    ### POSE QUALITY (100–199) ###
    ##############################

    NO_PERSON        = (100, "I can't see you — please step into the frame.")
    LOW_VISIBILITY   = (101, "The camera can’t see you clearly — improve lighting.")
    PARTIAL_BODY     = (102, "Move back a bit — I need to see your full body.")
    TOO_FAR          = (103, "You're too far away — step closer.")
    TOO_CLOSE        = (104, "You're too close — please take a small step back.")
    UNSTABLE         = (105, "The camera view is unstable — try holding your position.")


    ################################
    ### SQUAT ERRORS (3000–3099) ###
    ################################

    SQUAT_NOT_DEEP_ENOUGH      = (3000, "Go a bit deeper in your squat.")
    SQUAT_TOO_DEEP             = (3001, "You’re going too deep — rise slightly.")
    SQUAT_KNEES_INWARD         = (3002, "Keep your knees from collapsing inward.")
    SQUAT_KNEES_OUTWARD        = (3003, "Don’t push your knees too far outward.")
    SQUAT_HEELS_OFF_GROUND     = (3004, "Keep your heels down during the squat.")
    SQUAT_WEIGHT_FORWARD       = (3005, "Shift your weight backward — avoid leaning forward.")
    SQUAT_CHEST_LEAN_FORWARD   = (3006, "Keep your chest more upright.")
    SQUAT_BACK_ROUNDED         = (3007, "Straighten your back — avoid rounding.")
    SQUAT_HIP_SHIFT_LEFT       = (3008, "Your hips are shifting left — keep centered.")
    SQUAT_HIP_SHIFT_RIGHT      = (3009, "Your hips are shifting right — keep centered.")


    ######################################
    ### BICEPS CURL ERRORS (3100–3199) ###
    ######################################

    CURL_TOO_SHORT_TOP         = (3100, "Lift a bit higher to complete the curl.")
    CURL_NOT_FULL_FLEXION      = (3101, "Curl your arm fully at the top of the movement.")
    CURL_ELBOWS_MOVING_FORWARD = (3102, "Keep your elbows close — don’t swing them forward.")
    CURL_ELBOWS_MOVING_BACKWARD= (3103, "Your elbows are drifting back — keep them stable.")
    CURL_LEANING_FORWARD       = (3104, "Stand upright — avoid leaning forward.")
    CURL_LEANING_BACKWARD      = (3105, "Don't lean backward — keep your core stable.")
    CURL_WRIST_NOT_NEUTRAL     = (3106, "Keep your wrists straight during the curl.")


    ###################################
    ### LATERAL RAISE ERRORS (3200–3299)
    ###################################

    LATERAL_ARMS_TOO_LOW        = (3200, "Lift your arms a bit higher.")
    LATERAL_ARMS_TOO_HIGH       = (3201, "Don't raise your arms too high — stay in control.")
    LATERAL_ELBOWS_BENT_TOO_MUCH= (3202, "Straighten your elbows slightly.")
    LATERAL_TORSO_SWAYING       = (3203, "Keep your torso stable — avoid swaying.")
    LATERAL_PARTIAL_REP         = (3204, "Complete the full range of motion for best results.")
    
    
    def __new__(cls, code, description):
        obj = object.__new__(cls)
        obj._value_ = code
        obj.description = description
        return obj

@dataclass
###############################
### FEEDBACK RESPONSE CLASS ###
###############################
class FeedbackResponse:
    # Class fields.
    feedback_code:FeedbackCode
    extra_info:Optional[Dict[str, Any]] = None

    ###############
    ### TO DICT ###
    ###############
    def to_dict(self) -> FeedbackResponseDict:
        return_dict = {
            "code":        self.feedback_code.value,
            "description": self.feedback_code.description
        }
        if self.extra_info: return_dict["extra_info"] = return_dict
        return return_dict