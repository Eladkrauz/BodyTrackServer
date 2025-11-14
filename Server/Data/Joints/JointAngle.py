############################################################
########## BODY TRACK // SERVER // DATA // JOINTS ##########
############################################################
################### CLASS: JointAngle ######################
############################################################

###############
### IMPORTS ###
###############
from dataclasses import dataclass
from Server.Data.Pose.PoseLandmarks import PoseLandmark
from Server.Data.Session.ExerciseType import ExerciseType

########################
### JOINT DATA CLASS ###
########################
@dataclass(frozen=True)
class Joint:
    """
    ### Description:
    The `Joint` data class represents a single joint definition.

    ### Attributes:
    - `name`: `str` identifier for logs / JSON / reports.
    - `landmarks`: `tuple` of `PoseLandmark` used to compute the angle.

    ### Notes:
    - For 3-point joints: used with `_calculate_angle()`
    - For 2-point joints: used with `_line_against_horizontal_angle()`
    """
    name:      str
    landmarks: tuple[PoseLandmark, PoseLandmark] | tuple[PoseLandmark, PoseLandmark, PoseLandmark]
    
###################
### JOINT ANGLE ###
###################
class JointAngle:
    """
    ### Description:
    The `JointAngle` class groups constants for joint angle identifiers, organized by exercise type.
    """
    TWO_POINT_JOINT   = 2
    THREE_POINT_JOINT = 3

    #############
    ### SQUAT ###
    #############
    class Squat:
        # Core joints (always calculated).
        LEFT_KNEE   = Joint("left_knee_angle",   (PoseLandmark.LEFT_HIP,       PoseLandmark.LEFT_KNEE,     PoseLandmark.LEFT_ANKLE))
        RIGHT_KNEE  = Joint("right_knee_angle",  (PoseLandmark.RIGHT_HIP,      PoseLandmark.RIGHT_KNEE,    PoseLandmark.RIGHT_ANKLE))
        LEFT_HIP    = Joint("left_hip_angle",    (PoseLandmark.LEFT_SHOULDER,  PoseLandmark.LEFT_HIP,      PoseLandmark.LEFT_KNEE))
        RIGHT_HIP   = Joint("right_hip_angle",   (PoseLandmark.RIGHT_SHOULDER, PoseLandmark.RIGHT_HIP,     PoseLandmark.RIGHT_KNEE))
        TRUNK_TILT  = Joint("trunk_tilt_angle",  (PoseLandmark.LEFT_HIP,       PoseLandmark.LEFT_SHOULDER, PoseLandmark.LEFT_EAR))
        CORE        = [LEFT_KNEE, RIGHT_KNEE, LEFT_HIP, RIGHT_HIP, TRUNK_TILT]

        # Extended joints (optional).
        LEFT_ANKLE  = Joint("left_ankle_angle",  (PoseLandmark.LEFT_KNEE,      PoseLandmark.LEFT_ANKLE,    PoseLandmark.LEFT_FOOT_INDEX))
        RIGHT_ANKLE = Joint("right_ankle_angle", (PoseLandmark.RIGHT_KNEE,     PoseLandmark.RIGHT_ANKLE,   PoseLandmark.RIGHT_FOOT_INDEX))
        KNEE_VALGUS = Joint("knee_valgus_angle", (PoseLandmark.LEFT_HIP,       PoseLandmark.LEFT_KNEE,     PoseLandmark.LEFT_ANKLE))
        HIP_LINE    = Joint("hip_line_angle",    (PoseLandmark.LEFT_HIP,       PoseLandmark.RIGHT_HIP))
        EXTENDED    = [LEFT_ANKLE, RIGHT_ANKLE, KNEE_VALGUS, HIP_LINE]

    ###################
    ### BICEPS CURL ###
    ###################
    class BicepsCurl:
        # Core joints
        LEFT_ELBOW           = Joint("left_elbow_angle",             (PoseLandmark.LEFT_SHOULDER,  PoseLandmark.LEFT_ELBOW,     PoseLandmark.LEFT_WRIST))
        RIGHT_ELBOW          = Joint("right_elbow_angle",            (PoseLandmark.RIGHT_SHOULDER, PoseLandmark.RIGHT_ELBOW,    PoseLandmark.RIGHT_WRIST))
        LEFT_SHOULDER_FLEX   = Joint("left_shoulder_flexion_angle",  (PoseLandmark.LEFT_HIP,       PoseLandmark.LEFT_SHOULDER,  PoseLandmark.LEFT_ELBOW))
        RIGHT_SHOULDER_FLEX  = Joint("right_shoulder_flexion_angle", (PoseLandmark.RIGHT_HIP,      PoseLandmark.RIGHT_SHOULDER, PoseLandmark.RIGHT_ELBOW))
        CORE                 = [LEFT_ELBOW, RIGHT_ELBOW, LEFT_SHOULDER_FLEX, RIGHT_SHOULDER_FLEX]

        # Extended joints
        LEFT_SHOULDER_TORSO  = Joint("left_shoulder_torso_angle",    (PoseLandmark.LEFT_HIP,       PoseLandmark.LEFT_SHOULDER,  PoseLandmark.LEFT_EAR))
        RIGHT_SHOULDER_TORSO = Joint("right_shoulder_torso_angle",   (PoseLandmark.RIGHT_HIP,      PoseLandmark.RIGHT_SHOULDER, PoseLandmark.RIGHT_EAR))
        LEFT_WRIST           = Joint("left_wrist_angle",             (PoseLandmark.LEFT_ELBOW,     PoseLandmark.LEFT_WRIST,     PoseLandmark.LEFT_INDEX))
        RIGHT_WRIST          = Joint("right_wrist_angle",            (PoseLandmark.RIGHT_ELBOW,    PoseLandmark.RIGHT_WRIST,    PoseLandmark.RIGHT_INDEX))
        EXTENDED             = [LEFT_SHOULDER_TORSO, RIGHT_SHOULDER_TORSO, LEFT_WRIST, RIGHT_WRIST]

    #####################
    ### LATERAL RAISE ###
    #####################
    class LateralRaise:
        # Core joints
        LEFT_SHOULDER_ABD  = Joint("left_shoulder_abduction_angle",  (PoseLandmark.LEFT_HIP,       PoseLandmark.LEFT_SHOULDER,  PoseLandmark.LEFT_ELBOW))
        RIGHT_SHOULDER_ABD = Joint("right_shoulder_abduction_angle", (PoseLandmark.RIGHT_HIP,      PoseLandmark.RIGHT_SHOULDER, PoseLandmark.RIGHT_ELBOW))
        LEFT_ELBOW_SET     = Joint("left_elbow_set_angle",           (PoseLandmark.LEFT_SHOULDER,  PoseLandmark.LEFT_ELBOW,     PoseLandmark.LEFT_WRIST))
        RIGHT_ELBOW_SET    = Joint("right_elbow_set_angle",          (PoseLandmark.RIGHT_SHOULDER, PoseLandmark.RIGHT_ELBOW,    PoseLandmark.RIGHT_WRIST))
        CORE               = [LEFT_SHOULDER_ABD, RIGHT_SHOULDER_ABD, LEFT_ELBOW_SET, RIGHT_ELBOW_SET]

        # Extended joints
        TORSO_TILT         = Joint("torso_lateral_tilt_angle",       (PoseLandmark.LEFT_HIP,       PoseLandmark.LEFT_SHOULDER,  PoseLandmark.LEFT_EAR))
        SHOULDER_LINE      = Joint("shoulder_line_angle",            (PoseLandmark.LEFT_SHOULDER,  PoseLandmark.RIGHT_SHOULDER))
        EXTENDED           = [TORSO_TILT, SHOULDER_LINE]

    ###################################
    ### EXERCISE TYPE TO JOINT TYPE ###
    ###################################
    def exercise_type_to_joint_type(exercise_type:ExerciseType) -> 'JointAngle':
        """
        ### Brief:
        The `exercise_type_to_joint_type` method converts an `ExerciseType` object to a `JointAngle` object.

        ### Arguments:
        `exercise_type` (ExerciseType): The exercise type to be converted.

        ### Returns:
        The converted `exercise_type` as a `JointAngle` object.
        """
        if exercise_type is ExerciseType.SQUAT:         return JointAngle.Squat
        if exercise_type is ExerciseType.BICEPS_CURL:   return JointAngle.BicepsCurl
        if exercise_type is ExerciseType.LATERAL_RAISE: return JointAngle.LateralRaise
        else:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            import inspect
            ErrorHandler.handle(error=ErrorCode.EXERCISE_TYPE_DOES_NOT_EXIST, origin=inspect.currentframe())
        return None