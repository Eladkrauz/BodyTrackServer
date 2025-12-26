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
from Data.Pose.PoseQuality import PoseQuality
from Data.Error.DetectedErrorCode import DetectedErrorCode


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
    NO_PERSON                       = auto(), "I can't see you please step into the frame."
    PARTIAL_BODY                    = auto(), "Move back a bit. I need to see your full body."
    TOO_FAR                         = auto(), "You're too far away step closer."
    UNSTABLE                        = auto(), "The camera view is unstable try holding your position."

    ####################
    ### SQUAT ERRORS ###
    ####################
    SQUAT_TOP_TRUNK_TOO_FORWARD        = auto(), "Keep your chest more upright at the top."
    SQUAT_TOP_TRUNK_TOO_BACKWARD       = auto(), "Avoid leaning backward at the top."
    SQUAT_TOP_HIP_LINE_UNBALANCED      = auto(), "Keep your hips level."

    SQUAT_DOWN_KNEE_TOO_STRAIGHT       = auto(), "Bend your knees more as you go down."
    SQUAT_DOWN_KNEE_TOO_BENT           = auto(), "Don't bend your knees too much on the way down."
    SQUAT_DOWN_HIP_TOO_STRAIGHT        = auto(), "Sit back more into the squat."
    SQUAT_DOWN_HIP_TOO_BENT            = auto(), "Don't drop too quickly into the squat."

    SQUAT_HOLD_HIP_NOT_DEEP_ENOUGH     = auto(), "Go a bit deeper in the squat."
    SQUAT_HOLD_HIP_TOO_DEEP            = auto(), "You're going too deep rise slightly."
    SQUAT_HOLD_KNEE_VALGUS             = auto(), "Keep your knees aligned over your toes."

    SQUAT_UP_KNEE_COLLAPSE             = auto(), "Avoid letting your knees collapse inward."
    SQUAT_UP_TRUNK_TOO_FORWARD         = auto(), "Lift your chest as you stand up."
    SQUAT_UP_TRUNK_TOO_BACKWARD        = auto(), "Don't lean backward as you rise."


    ##########################
    ### BICEPS CURL ERRORS ###
    ##########################
    CURL_REST_ELBOW_TOO_BENT            = auto(), "Fully extend your arms at the bottom."
    CURL_REST_ELBOW_TOO_STRAIGHT        = auto(), "Maintain slight tension don't lock out."
    CURL_REST_SHOULDER_TOO_FORWARD      = auto(), "Relax your shoulders don't push them forward."
    CURL_REST_SHOULDER_TOO_BACKWARD     = auto(), "Keep your shoulders neutral."

    CURL_LIFTING_ELBOW_TOO_STRAIGHT     = auto(), "Bend your elbows more as you lift."
    CURL_LIFTING_ELBOW_TOO_BENT         = auto(), "Control the lift avoid over-bending."
    CURL_LIFTING_SHOULDER_TOO_FORWARD   = auto(), "Don't swing your shoulders forward."
    CURL_LIFTING_SHOULDER_TOO_BACKWARD  = auto(), "Avoid leaning back during the curl."

    CURL_HOLD_ELBOW_TOO_OPEN            = auto(), "Bring your elbows in slightly."
    CURL_HOLD_ELBOW_TOO_CLOSED          = auto(), "Open your elbows slightly at the top."
    CURL_HOLD_WRIST_TOO_FLEXED          = auto(), "Keep your wrists neutral."
    CURL_HOLD_WRIST_TOO_EXTENDED        = auto(), "Avoid bending your wrists backward."

    CURL_LOWERING_ELBOW_TOO_STRAIGHT    = auto(), "Lower the weight with control."
    CURL_LOWERING_ELBOW_TOO_BENT        = auto(), "Extend your arms more as you lower."
    CURL_LOWERING_SHOULDER_TOO_FORWARD  = auto(), "Don't lean forward while lowering."
    CURL_LOWERING_SHOULDER_TOO_BACKWARD = auto(), "Control your posture on the way down."

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

            if detected_error == DetectedErrorCode.NO_BIOMECHANICAL_ERROR:
                return FeedbackCode.VALID
            if detected_error == DetectedErrorCode.NOT_READY_FOR_ANALYSIS:
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