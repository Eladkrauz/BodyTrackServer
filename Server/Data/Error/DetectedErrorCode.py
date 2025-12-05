####################################################################
############### BODY TRACK // SERVER // DATA // ERROR ##############
####################################################################
################ ENUM: DetectedErrorCode ###########################
####################################################################

###############
### IMPORTS ###
###############
from enum import Enum

######################################
### DETECTED ERROR CODE ENUM CLASS ###
######################################
class DetectedErrorCode(Enum):
    """
    The `DetectedErrorCode` class is pure biomechanical error codes detected strictly by ErrorDetector.
    No text strings are included here — only numeric codes.
    FeedbackFormatter decides how to phrase the user-facing message.
    """

    ##############################
    ### SQUAT ERRORS 3000–3020 ###
    ##############################
    SQUAT_NOT_DEEP_ENOUGH        = 3000   # hip/knee angle too high
    SQUAT_TOO_DEEP               = 3001   # hip/knee angle too low
    SQUAT_KNEES_INWARD           = 3002   # valgus
    SQUAT_KNEES_OUTWARD          = 3003   # varus (new)
    SQUAT_HEELS_OFF_GROUND       = 3004   # ankle too low
    SQUAT_WEIGHT_FORWARD         = 3005   # ankle too high
    SQUAT_CHEST_LEAN_FORWARD     = 3006   # trunk tilt too low
    SQUAT_BACK_ROUNDED           = 3007   # trunk tilt too high
    SQUAT_HIP_SHIFT_LEFT         = 3008
    SQUAT_HIP_SHIFT_RIGHT        = 3009

    ####################################
    ### BICEPS CURL ERRORS 3100–3110 ###
    ####################################
    CURL_TOO_SHORT_TOP             = 3100   # elbow too low angle
    CURL_NOT_FULL_FLEXION          = 3101   # elbow too high angle
    CURL_ELBOWS_MOVING_FORWARD     = 3102   # shoulder flexion too high
    CURL_ELBOWS_MOVING_BACKWARD    = 3103   # shoulder flexion too low
    CURL_LEANING_FORWARD           = 3104   # torso angle too low
    CURL_LEANING_BACKWARD          = 3105   # torso angle too high
    CURL_WRIST_NOT_NEUTRAL         = 3106   # wrist too low/high

    ######################################
    ### LATERAL RAISE ERRORS 3200–3210 ###
    ######################################
    LATERAL_ARMS_TOO_LOW           = 3200   # ABD too low
    LATERAL_ARMS_TOO_HIGH          = 3201   # ABD too high
    LATERAL_ELBOWS_BENT_TOO_MUCH   = 3202   # elbow_set too low
    LATERAL_TORSO_SWAYING          = 3203   # torso tilt low/high
    LATERAL_PARTIAL_REP            = 3204   # elbow_set or shoulder_line too high/low

    ######################
    ### NO ERROR FOUND ###
    ######################
    NO_BIOMECHANICAL_ERROR         = 3999
    NOT_READY_FOR_ANALYSIS         = 4000