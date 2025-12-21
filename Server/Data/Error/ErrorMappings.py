############################################################
############ BODY TRACK / SERVER / DATA / ERROR ############
############################################################
##################### CLASS: ErrorMappings #################
############################################################

###############
### IMPORTS ###
###############
from Server.Data.Joints.JointAngle import JointAngle
from Server.Data.Error.DetectedErrorCode import DetectedErrorCode

############################
### ERROR MAPPINGS CLASS ###
############################
class ErrorMappings:
    """
    The `ErrorMappings` method holds all angle-to-error dictionaries used by ErrorDetector.
    Maps each joint angle name (LOW/HIGH violation) to a DetectedErrorCode.
    Exercise-specific, semantic mappings only.
    """

    ###########################
    ### SQUAT ERROR MAP LOW ###
    ###########################
    """
    ### Description:
    Low-angle violations for squat exercise           
    """
    SQUAT_ERROR_MAP_LOW = {
        JointAngle.Squat.TRUNK_TILT.name:   DetectedErrorCode.SQUAT_CHEST_LEAN_FORWARD,
        JointAngle.Squat.HIP_LINE.name:     DetectedErrorCode.SQUAT_NOT_DEEP_ENOUGH,
        JointAngle.Squat.LEFT_HIP.name:     DetectedErrorCode.SQUAT_NOT_DEEP_ENOUGH,
        JointAngle.Squat.RIGHT_HIP.name:    DetectedErrorCode.SQUAT_NOT_DEEP_ENOUGH,
        JointAngle.Squat.LEFT_KNEE.name:    DetectedErrorCode.SQUAT_NOT_DEEP_ENOUGH,
        JointAngle.Squat.RIGHT_KNEE.name:   DetectedErrorCode.SQUAT_NOT_DEEP_ENOUGH,
        JointAngle.Squat.LEFT_ANKLE.name:   DetectedErrorCode.SQUAT_HEELS_OFF_GROUND,
        JointAngle.Squat.RIGHT_ANKLE.name:  DetectedErrorCode.SQUAT_HEELS_OFF_GROUND,
        JointAngle.Squat.KNEE_VALGUS.name:  DetectedErrorCode.SQUAT_KNEES_INWARD,
    }

    ############################
    ### SQUAT ERROR MAP HIGH ###
    ############################
    """
    ### Description:
    High-angle violations for squat exercise           
    """
    SQUAT_ERROR_MAP_HIGH = {
        JointAngle.Squat.TRUNK_TILT.name:   DetectedErrorCode.SQUAT_BACK_ROUNDED,
        JointAngle.Squat.HIP_LINE.name:     DetectedErrorCode.SQUAT_TOO_DEEP,
        JointAngle.Squat.LEFT_HIP.name:     DetectedErrorCode.SQUAT_NOT_DEEP_ENOUGH,
        JointAngle.Squat.RIGHT_HIP.name:    DetectedErrorCode.SQUAT_NOT_DEEP_ENOUGH,
        JointAngle.Squat.LEFT_KNEE.name:    DetectedErrorCode.SQUAT_KNEES_INWARD,
        JointAngle.Squat.RIGHT_KNEE.name:   DetectedErrorCode.SQUAT_KNEES_INWARD,
        JointAngle.Squat.LEFT_ANKLE.name:   DetectedErrorCode.SQUAT_WEIGHT_FORWARD,
        JointAngle.Squat.RIGHT_ANKLE.name:  DetectedErrorCode.SQUAT_WEIGHT_FORWARD,
        JointAngle.Squat.KNEE_VALGUS.name:  DetectedErrorCode.SQUAT_KNEES_INWARD,
    }

    #################################
    ### BICEPS CURL ERROR MAP LOW ###
    #################################
    """
    ### Description:
    Low-angle violations for biceps curl exercise           
    """
    BICEPS_CURL_ERROR_MAP_LOW = {
        JointAngle.BicepsCurl.LEFT_ELBOW.name:            DetectedErrorCode.CURL_TOO_SHORT_TOP,
        JointAngle.BicepsCurl.RIGHT_ELBOW.name:           DetectedErrorCode.CURL_TOO_SHORT_TOP,
        JointAngle.BicepsCurl.LEFT_SHOULDER_FLEX.name:    DetectedErrorCode.CURL_ELBOWS_MOVING_BACKWARD,
        JointAngle.BicepsCurl.RIGHT_SHOULDER_FLEX.name:   DetectedErrorCode.CURL_ELBOWS_MOVING_BACKWARD,
        JointAngle.BicepsCurl.LEFT_SHOULDER_TORSO.name:   DetectedErrorCode.CURL_LEANING_FORWARD,
        JointAngle.BicepsCurl.RIGHT_SHOULDER_TORSO.name:  DetectedErrorCode.CURL_LEANING_FORWARD,
        JointAngle.BicepsCurl.LEFT_WRIST.name:            DetectedErrorCode.CURL_WRIST_NOT_NEUTRAL,
        JointAngle.BicepsCurl.RIGHT_WRIST.name:           DetectedErrorCode.CURL_WRIST_NOT_NEUTRAL,
    }

    ##################################
    ### BICEPS CURL ERROR MAP HIGH ###
    ##################################
    """
    ### Description:
    High-angle violations for biceps curl exercise           
    """
    BICEPS_CURL_ERROR_MAP_HIGH = {
        JointAngle.BicepsCurl.LEFT_ELBOW.name:            DetectedErrorCode.CURL_NOT_FULL_FLEXION,
        JointAngle.BicepsCurl.RIGHT_ELBOW.name:           DetectedErrorCode.CURL_NOT_FULL_FLEXION,
        JointAngle.BicepsCurl.LEFT_SHOULDER_FLEX.name:    DetectedErrorCode.CURL_ELBOWS_MOVING_FORWARD,
        JointAngle.BicepsCurl.RIGHT_SHOULDER_FLEX.name:   DetectedErrorCode.CURL_ELBOWS_MOVING_FORWARD,
        JointAngle.BicepsCurl.LEFT_SHOULDER_TORSO.name:   DetectedErrorCode.CURL_LEANING_BACKWARD,
        JointAngle.BicepsCurl.RIGHT_SHOULDER_TORSO.name:  DetectedErrorCode.CURL_LEANING_BACKWARD,
        JointAngle.BicepsCurl.LEFT_WRIST.name:            DetectedErrorCode.CURL_WRIST_NOT_NEUTRAL,
        JointAngle.BicepsCurl.RIGHT_WRIST.name:           DetectedErrorCode.CURL_WRIST_NOT_NEUTRAL,
    }