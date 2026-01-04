############################################################
######### BODY TRACK // SERVER // DATA // RESPONSE #########
############################################################
################## CLASS: FeedbackResponse #################
############################################################

###############
### IMPORTS ###
###############
from enum import IntEnum
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
class FeedbackCode(IntEnum):
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
    VALID                               = auto()
    SILENT                              = auto()

    ###########################
    ### POSE QUALITY ERRORS ###
    ###########################
    NO_PERSON                           = auto()
    PARTIAL_BODY                        = auto()
    TOO_FAR                             = auto()
    UNSTABLE                            = auto()

    ####################
    ### SQUAT ERRORS ###
    ####################
    SQUAT_TOP_TRUNK_TOO_FORWARD         = auto()
    SQUAT_TOP_TRUNK_TOO_BACKWARD        = auto()
    SQUAT_TOP_HIP_LINE_UNBALANCED       = auto()

    SQUAT_DOWN_KNEE_TOO_STRAIGHT        = auto()
    SQUAT_DOWN_KNEE_TOO_BENT            = auto()
    SQUAT_DOWN_HIP_TOO_STRAIGHT         = auto()
    SQUAT_DOWN_HIP_TOO_BENT             = auto()

    SQUAT_HOLD_HIP_NOT_DEEP_ENOUGH      = auto()
    SQUAT_HOLD_HIP_TOO_DEEP             = auto()
    SQUAT_HOLD_KNEE_VALGUS              = auto()

    SQUAT_UP_KNEE_COLLAPSE              = auto()
    SQUAT_UP_TRUNK_TOO_FORWARD          = auto()
    SQUAT_UP_TRUNK_TOO_BACKWARD         = auto()

    ##########################
    ### BICEPS CURL ERRORS ###
    ##########################
    CURL_REST_ELBOW_TOO_BENT            = auto()
    CURL_REST_ELBOW_TOO_STRAIGHT        = auto()
    CURL_REST_SHOULDER_TOO_FORWARD      = auto()
    CURL_REST_SHOULDER_TOO_BACKWARD     = auto()

    CURL_LIFTING_ELBOW_TOO_STRAIGHT     = auto()
    CURL_LIFTING_ELBOW_TOO_BENT         = auto()
    CURL_LIFTING_SHOULDER_TOO_FORWARD   = auto()
    CURL_LIFTING_SHOULDER_TOO_BACKWARD  = auto()

    CURL_HOLD_ELBOW_TOO_OPEN            = auto()
    CURL_HOLD_ELBOW_TOO_CLOSED          = auto()
    CURL_HOLD_WRIST_TOO_FLEXED          = auto()    
    CURL_HOLD_WRIST_TOO_EXTENDED        = auto()    

    CURL_LOWERING_ELBOW_TOO_STRAIGHT    = auto()
    CURL_LOWERING_ELBOW_TOO_BENT        = auto()
    CURL_LOWERING_SHOULDER_TOO_FORWARD  = auto()
    CURL_LOWERING_SHOULDER_TOO_BACKWARD = auto()

    #################
    ### MESSAGE ###
    #################
    @property
    def description(self) -> str:
        return {
            # System states
            FeedbackCode.VALID:                                 "",
            FeedbackCode.SILENT:                                "",

            # Pose quality
            FeedbackCode.NO_PERSON:                             "I can't see you please step into the frame.",
            FeedbackCode.PARTIAL_BODY:                          "Move back a bit. I need to see your full body.",
            FeedbackCode.TOO_FAR:                               "You're too far away step closer.",
            FeedbackCode.UNSTABLE:                              "The camera view is unstable try holding your position.",

            # Squat
            FeedbackCode.SQUAT_TOP_TRUNK_TOO_FORWARD:           "Keep your chest more upright at the top.",
            FeedbackCode.SQUAT_TOP_TRUNK_TOO_BACKWARD:          "Avoid leaning backward at the top.",
            FeedbackCode.SQUAT_TOP_HIP_LINE_UNBALANCED:         "Keep your hips level.",

            FeedbackCode.SQUAT_DOWN_KNEE_TOO_STRAIGHT:          "Bend your knees more as you go down.",
            FeedbackCode.SQUAT_DOWN_KNEE_TOO_BENT:              "Don't bend your knees too much on the way down.",
            FeedbackCode.SQUAT_DOWN_HIP_TOO_STRAIGHT:           "Sit back more into the squat.",
            FeedbackCode.SQUAT_DOWN_HIP_TOO_BENT:               "Don't drop too quickly into the squat.",

            FeedbackCode.SQUAT_HOLD_HIP_NOT_DEEP_ENOUGH:        "Go a bit deeper in the squat.",
            FeedbackCode.SQUAT_HOLD_HIP_TOO_DEEP:               "You're going too deep rise slightly.",
            FeedbackCode.SQUAT_HOLD_KNEE_VALGUS:                "Keep your knees aligned over your toes.",

            FeedbackCode.SQUAT_UP_KNEE_COLLAPSE:                "Avoid letting your knees collapse inward.",
            FeedbackCode.SQUAT_UP_TRUNK_TOO_FORWARD:            "Lift your chest as you stand up.",
            FeedbackCode.SQUAT_UP_TRUNK_TOO_BACKWARD:           "Don't lean backward as you rise.",

            # Biceps curl
            FeedbackCode.CURL_REST_ELBOW_TOO_BENT:              "Fully extend your arms at the bottom.",
            FeedbackCode.CURL_REST_ELBOW_TOO_STRAIGHT:          "Maintain slight tension don't lock out.",
            FeedbackCode.CURL_REST_SHOULDER_TOO_FORWARD:        "Relax your shoulders don't push them forward.",
            FeedbackCode.CURL_REST_SHOULDER_TOO_BACKWARD:       "Keep your shoulders neutral.",

            FeedbackCode.CURL_LIFTING_ELBOW_TOO_STRAIGHT:       "Bend your elbows more as you lift.",
            FeedbackCode.CURL_LIFTING_ELBOW_TOO_BENT:           "Control the lift avoid over-bending.",
            FeedbackCode.CURL_LIFTING_SHOULDER_TOO_FORWARD:     "Don't swing your shoulders forward.",
            FeedbackCode.CURL_LIFTING_SHOULDER_TOO_BACKWARD:    "Avoid leaning back during the curl.",
            
            FeedbackCode.CURL_HOLD_ELBOW_TOO_OPEN:              "Bend your elbows a bit more at the top.",
            FeedbackCode.CURL_HOLD_ELBOW_TOO_CLOSED:            "Open your elbows slightly at the top.",
            FeedbackCode.CURL_HOLD_WRIST_TOO_FLEXED:            "Keep your wrists neutral.",
            FeedbackCode.CURL_HOLD_WRIST_TOO_EXTENDED:          "Avoid bending your wrists backward.",
            
            FeedbackCode.CURL_LOWERING_ELBOW_TOO_STRAIGHT:      "Lower the weight with control.",
            FeedbackCode.CURL_LOWERING_ELBOW_TOO_BENT:          "Extend your arms more as you lower.",
            FeedbackCode.CURL_LOWERING_SHOULDER_TOO_FORWARD:    "Don't lean forward while lowering.",
            FeedbackCode.CURL_LOWERING_SHOULDER_TOO_BACKWARD:   "Control your posture on the way down.",
        }[self]

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