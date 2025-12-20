###############
### IMPORTS ###
###############
from enum import Enum

#################################
### DETECTED ERROR CODE CLASS ###
#################################
class DetectedErrorCode(Enum):
    """
    The `DetectedErrorCode` class is pure biomechanical error codes detected strictly by ErrorDetector.
    No text strings are included here — only numeric codes.
    FeedbackFormatter decides how to phrase the user-facing message.
    """

    ########################
    ### SQUAT (3000–3012)###
    ########################

    SQUAT_TOP_TRUNK_TOO_FORWARD        = 3000
    SQUAT_TOP_TRUNK_TOO_BACKWARD       = 3001
    SQUAT_TOP_HIP_LINE_UNBALANCED      = 3002

    SQUAT_DOWN_KNEE_TOO_STRAIGHT       = 3003
    SQUAT_DOWN_KNEE_TOO_BENT           = 3004
    SQUAT_DOWN_HIP_TOO_STRAIGHT        = 3005
    SQUAT_DOWN_HIP_TOO_BENT            = 3006

    SQUAT_HOLD_HIP_NOT_DEEP_ENOUGH     = 3007
    SQUAT_HOLD_HIP_TOO_DEEP            = 3008
    SQUAT_HOLD_KNEE_VALGUS             = 3009

    SQUAT_UP_KNEE_COLLAPSE             = 3010
    SQUAT_UP_TRUNK_TOO_FORWARD         = 3011
    SQUAT_UP_TRUNK_TOO_BACKWARD        = 3012


    ###############################
    ### BICEPS CURL (3100–3115) ###
    ###############################

    CURL_REST_ELBOW_TOO_BENT            = 3100
    CURL_REST_ELBOW_TOO_STRAIGHT        = 3101
    CURL_REST_SHOULDER_TOO_FORWARD      = 3102
    CURL_REST_SHOULDER_TOO_BACKWARD     = 3103

    CURL_LIFTING_ELBOW_TOO_STRAIGHT     = 3104
    CURL_LIFTING_ELBOW_TOO_BENT         = 3105
    CURL_LIFTING_SHOULDER_TOO_FORWARD   = 3106
    CURL_LIFTING_SHOULDER_TOO_BACKWARD  = 3107

    CURL_HOLD_ELBOW_TOO_OPEN            = 3108
    CURL_HOLD_ELBOW_TOO_CLOSED          = 3109
    CURL_HOLD_WRIST_TOO_FLEXED          = 3110
    CURL_HOLD_WRIST_TOO_EXTENDED        = 3111

    CURL_LOWERING_ELBOW_TOO_STRAIGHT    = 3112
    CURL_LOWERING_ELBOW_TOO_BENT        = 3113
    CURL_LOWERING_SHOULDER_TOO_FORWARD  = 3114
    CURL_LOWERING_SHOULDER_TOO_BACKWARD = 3115

    #################################
    ### LATERAL RAISE (3200–3211) ###
    #################################

    LATERAL_REST_ARM_TOO_HIGH           = 3200
    LATERAL_REST_ARM_TOO_LOW            = 3201
    LATERAL_REST_TORSO_TILT_LEFT_RIGHT  = 3202

    LATERAL_RAISE_ARM_TOO_LOW           = 3203
    LATERAL_RAISE_ARM_TOO_HIGH          = 3204
    LATERAL_RAISE_ELBOW_TOO_BENT        = 3205

    LATERAL_HOLD_ARM_TOO_LOW            = 3206
    LATERAL_HOLD_ARM_TOO_HIGH           = 3207
    LATERAL_HOLD_TORSO_TILT_LEFT_RIGHT  = 3208

    LATERAL_LOWER_ARM_TOO_LOW           = 3209
    LATERAL_LOWER_ARM_TOO_HIGH          = 3210
    LATERAL_LOWER_ELBOW_TOO_BENT        = 3211

    ##############
    ### SYSTEM ###
    ##############
    NO_BIOMECHANICAL_ERROR        = 3999
    NOT_READY_FOR_ANALYSIS        = 4000
