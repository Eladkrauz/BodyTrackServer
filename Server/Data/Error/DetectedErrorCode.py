###############################################################
############# BODY TRACK // SERVER // DATA // ERROR ###########
###############################################################
################### CLASS: DetectedErrorCode ##################
###############################################################
 
###############
### IMPORTS ###
###############
from enum import Enum
from enum import auto

#################################
### DETECTED ERROR CODE CLASS ###
#################################
class DetectedErrorCode(Enum):
    """
    The `DetectedErrorCode` class is pure biomechanical error codes detected strictly by ErrorDetector.
    No text strings are included here — only numeric codes.
    `FeedbackFormatter` decides how to phrase the user-facing message.
    """

    ##################################
    ### SQUAT DETECTED ERROR CODES ###
    ##################################
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

    ########################################
    ### BICEPS CURL DETECTED ERROR CODES ###
    ########################################
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

    ##############
    ### SYSTEM ###
    ##############
    NO_BIOMECHANICAL_ERROR              = auto()
    NOT_READY_FOR_ANALYSIS              = auto()