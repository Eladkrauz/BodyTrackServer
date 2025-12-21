############################################################
######### BODY TRACK // SERVER // DATA // RESPONSE #########
############################################################
################## CLASS: FeedbackResponse #################
############################################################

###############
### IMPORTS ###
###############
from enum import Enum as enum
from enum import auto
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
    """
    #####################
    ### SYSTEM STATES ###
    #####################
    VALID                           = auto(), ""
    SILENT                          = auto(), ""

    ###########################
    ### POSE QUALITY ERRORS ###
    ###########################
    NO_PERSON                       = auto(), "I can't see you - please step into the frame."
    LOW_VISIBILITY                  = auto(), "The camera can't see you clearly - improve lighting."
    PARTIAL_BODY                    = auto(), "Move back a bit - I need to see your full body."
    TOO_FAR                         = auto(), "You're too far away - step closer."
    TOO_CLOSE                       = auto(), "You're too close - please take a small step back."
    UNSTABLE                        = auto(), "The camera view is unstable - try holding your position."

    ####################
    ### SQUAT ERRORS ###
    ####################
    SQUAT_NOT_DEEP_ENOUGH           = auto(), "Go a bit deeper in your squat."
    SQUAT_TOO_DEEP                  = auto(), "You're going too deep - rise slightly."
    SQUAT_KNEES_INWARD              = auto(), "Keep your knees from collapsing inward."
    SQUAT_KNEES_OUTWARD             = auto(), "Don't push your knees too far outward."
    SQUAT_HEELS_OFF_GROUND          = auto(), "Keep your heels down during the squat."
    SQUAT_WEIGHT_FORWARD            = auto(), "Shift your weight backward - avoid leaning forward."
    SQUAT_CHEST_LEAN_FORWARD        = auto(), "Keep your chest more upright."
    SQUAT_BACK_ROUNDED              = auto(), "Straighten your back - avoid rounding."
    SQUAT_HIP_SHIFT_LEFT            = auto(), "Your hips are shifting left - keep centered."
    SQUAT_HIP_SHIFT_RIGHT           = auto(), "Your hips are shifting right - keep centered."

    ##########################
    ### BICEPS CURL ERRORS ###
    ##########################
    CURL_TOO_SHORT_TOP              = auto(), "Lift a bit higher to complete the curl."
    CURL_NOT_FULL_FLEXION           = auto(), "Curl your arm fully at the top of the movement."
    CURL_ELBOWS_MOVING_FORWARD      = auto(), "Keep your elbows close - don't swing them forward."
    CURL_ELBOWS_MOVING_BACKWARD     = auto(), "Your elbows are drifting back - keep them stable."
    CURL_LEANING_FORWARD            = auto(), "Stand upright - avoid leaning forward."
    CURL_LEANING_BACKWARD           = auto(), "Don't lean backward - keep your core stable."
    CURL_WRIST_NOT_NEUTRAL          = auto(), "Keep your wrists straight during the curl."
    
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
        """
        ### Brief:
        The `from_pose_quality` static method maps a `PoseQuality` value
        to its corresponding `FeedbackCode`.

        ### Arguments:
        - `pose_quality` (PoseQuality): The quality of the detected pose.

        ### Returns:
        - `FeedbackCode`: The corresponding feedback code for the given pose quality.
        """
        mapping = {
            PoseQuality.NO_PERSON:      FeedbackCode.NO_PERSON,
            PoseQuality.PARTIAL_BODY:   FeedbackCode.PARTIAL_BODY,
            PoseQuality.TOO_FAR:        FeedbackCode.TOO_FAR,
            PoseQuality.UNSTABLE:       FeedbackCode.UNSTABLE
        }

        if isinstance(pose_quality, str): pose_quality = PoseQuality[pose_quality]
        return mapping.get(pose_quality, FeedbackCode.SILENT)
    
    ###########################
    ### FROM DETECTED ERROR ###
    ###########################
    @staticmethod
    def from_detected_error(detected_error:DetectedErrorCode) -> 'FeedbackCode':
        """
        ### Brief:
        The `from_detected_error` static method maps a `DetectedErrorCode` value
        to its corresponding `FeedbackCode`.

        ### Arguments:
        - `detected_error` (DetectedErrorCode): The detected error code.
        ### Returns:
        - `FeedbackCode`: The corresponding feedback code for the given detected error.
        """
        try:
            # Convert string to DetectedErrorCode if necessary.
            if isinstance(detected_error, str):
                detected_error:DetectedErrorCode = DetectedErrorCode[detected_error]

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