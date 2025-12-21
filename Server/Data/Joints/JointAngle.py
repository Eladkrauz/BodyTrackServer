############################################################
########## BODY TRACK // SERVER // DATA // JOINTS ##########
############################################################
################### CLASS: JointAngle ######################
############################################################

###############
### IMPORTS ###
###############
from dataclasses import dataclass

from Server.Data.Pose.PoseLandmarks   import PoseLandmark
from Server.Data.Session.ExerciseType import ExerciseType
from Server.Data.Pose.PositionSide    import PositionSide

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
    dimension: bool # True for 3D, False for 2D.
    
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
        LEFT_KNEE   = Joint("left_knee_angle",   (PoseLandmark.LEFT_HIP.value,       PoseLandmark.LEFT_KNEE.value,     PoseLandmark.LEFT_ANKLE.value),          False)
        RIGHT_KNEE  = Joint("right_knee_angle",  (PoseLandmark.RIGHT_HIP.value,      PoseLandmark.RIGHT_KNEE.value,    PoseLandmark.RIGHT_ANKLE.value),         False)
        LEFT_HIP    = Joint("left_hip_angle",    (PoseLandmark.LEFT_SHOULDER.value,  PoseLandmark.LEFT_HIP.value,      PoseLandmark.LEFT_KNEE.value),           False)
        RIGHT_HIP   = Joint("right_hip_angle",   (PoseLandmark.RIGHT_SHOULDER.value, PoseLandmark.RIGHT_HIP.value,     PoseLandmark.RIGHT_KNEE.value),          False)
        TRUNK_TILT  = Joint("trunk_tilt_angle",  (PoseLandmark.LEFT_HIP.value,       PoseLandmark.LEFT_SHOULDER.value, PoseLandmark.LEFT_EAR.value),            False)
        LEFT_CORE   = [LEFT_KNEE, LEFT_HIP, TRUNK_TILT]
        RIGHT_CORE  = [RIGHT_KNEE, RIGHT_HIP, TRUNK_TILT]
        CORE        = [LEFT_KNEE, RIGHT_KNEE, LEFT_HIP, RIGHT_HIP, TRUNK_TILT]

        # Extended joints (optional).
        LEFT_ANKLE     = Joint("left_ankle_angle",  (PoseLandmark.LEFT_KNEE.value,      PoseLandmark.LEFT_ANKLE.value,    PoseLandmark.LEFT_FOOT_INDEX.value),  False)
        RIGHT_ANKLE    = Joint("right_ankle_angle", (PoseLandmark.RIGHT_KNEE.value,     PoseLandmark.RIGHT_ANKLE.value,   PoseLandmark.RIGHT_FOOT_INDEX.value), False)
        KNEE_VALGUS    = Joint("knee_valgus_angle", (PoseLandmark.LEFT_HIP.value,       PoseLandmark.LEFT_KNEE.value,     PoseLandmark.LEFT_ANKLE.value),       False)
        HIP_LINE       = Joint("hip_line_angle",    (PoseLandmark.LEFT_HIP.value,       PoseLandmark.RIGHT_HIP.value),                                          False)
        LEFT_EXTENDED  = [LEFT_ANKLE, KNEE_VALGUS, HIP_LINE]
        RIGHT_EXTENDED = [RIGHT_ANKLE, KNEE_VALGUS, HIP_LINE]
        EXTENDED       = [LEFT_ANKLE, RIGHT_ANKLE, KNEE_VALGUS, HIP_LINE]

    ###################
    ### BICEPS CURL ###
    ###################
    class BicepsCurl:
        # Core joints
        LEFT_ELBOW           = Joint("left_elbow_angle",             (PoseLandmark.LEFT_SHOULDER.value,  PoseLandmark.LEFT_ELBOW.value,     PoseLandmark.LEFT_WRIST.value),  False)
        RIGHT_ELBOW          = Joint("right_elbow_angle",            (PoseLandmark.RIGHT_SHOULDER.value, PoseLandmark.RIGHT_ELBOW.value,    PoseLandmark.RIGHT_WRIST.value), False)
        LEFT_SHOULDER_FLEX   = Joint("left_shoulder_flexion_angle",  (PoseLandmark.LEFT_HIP.value,       PoseLandmark.LEFT_SHOULDER.value,  PoseLandmark.LEFT_ELBOW.value),  False)
        RIGHT_SHOULDER_FLEX  = Joint("right_shoulder_flexion_angle", (PoseLandmark.RIGHT_HIP.value,      PoseLandmark.RIGHT_SHOULDER.value, PoseLandmark.RIGHT_ELBOW.value), False)
        LEFT_CORE            = [LEFT_ELBOW, LEFT_SHOULDER_FLEX]
        RIGHT_CORE           = [RIGHT_ELBOW, RIGHT_SHOULDER_FLEX]
        CORE                 = [LEFT_ELBOW, RIGHT_ELBOW, LEFT_SHOULDER_FLEX, RIGHT_SHOULDER_FLEX]

        # Extended joints
        LEFT_SHOULDER_TORSO  = Joint("left_shoulder_torso_angle",    (PoseLandmark.LEFT_HIP.value,       PoseLandmark.LEFT_SHOULDER.value,  PoseLandmark.LEFT_EAR.value),    False)
        RIGHT_SHOULDER_TORSO = Joint("right_shoulder_torso_angle",   (PoseLandmark.RIGHT_HIP.value,      PoseLandmark.RIGHT_SHOULDER.value, PoseLandmark.RIGHT_EAR.value),   False)
        LEFT_WRIST           = Joint("left_wrist_angle",             (PoseLandmark.LEFT_ELBOW.value,     PoseLandmark.LEFT_WRIST.value,     PoseLandmark.LEFT_INDEX.value),  False)
        RIGHT_WRIST          = Joint("right_wrist_angle",            (PoseLandmark.RIGHT_ELBOW.value,    PoseLandmark.RIGHT_WRIST.value,    PoseLandmark.RIGHT_INDEX.value), False)
        LEFT_EXTENDED        = [LEFT_SHOULDER_TORSO, LEFT_WRIST]
        RIGHT_EXTENDED       = [RIGHT_SHOULDER_TORSO, RIGHT_WRIST]
        EXTENDED             = [LEFT_SHOULDER_TORSO, RIGHT_SHOULDER_TORSO, LEFT_WRIST, RIGHT_WRIST]

    ###################################
    ### EXERCISE TYPE TO JOINT TYPE ###
    ###################################
    @classmethod
    def exercise_type_to_joint_type(cls, exercise_type:ExerciseType) -> Squat | BicepsCurl | None:
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
        else:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            import inspect
            ErrorHandler.handle(error=ErrorCode.EXERCISE_TYPE_DOES_NOT_EXIST, origin=inspect.currentframe())
        return None
    
    ################
    ### GET CORE ###
    ################
    @classmethod
    def _get_core(
            cls,
            cls_name:Squat | BicepsCurl,
            position_side:PositionSide
        ) -> list[Joint]:
        """
        ### Brief:
        The `_get_core` method retrieves the core joints based on the specified position side.

        ### Arguments:
        - `cls_name` (Squat | BicepsCurl): The joint angle class to retrieve joints from.
        - `position_side` (PositionSide): The side of the body (LEFT, RIGHT, or BOTH).

        ### Returns:
        A `list` of core joints corresponding to the specified position side.
        """
        if   position_side.is_left():    return cls_name.LEFT_CORE
        elif position_side.is_right():   return cls_name.RIGHT_CORE
        elif position_side.is_front():   return cls_name.CORE
        elif position_side.is_unkwown(): return cls_name.CORE
        else:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            import inspect
            ErrorHandler.handle(error=ErrorCode.POSITION_SIDE_DOES_NOT_EXIST, origin=inspect.currentframe())
        return []
    
    ####################
    ### GET EXTENDED ###
    ####################
    @classmethod
    def _get_extended(
            cls,
            cls_name:Squat | BicepsCurl,
            position_side:PositionSide
        ) -> list[Joint]:
        """
        ### Brief:
        The `_get_extended` method retrieves the extended joints based on the specified position side.

        ### Arguments:
        - `cls_name` (Squat | BicepsCurl): The joint angle class to retrieve joints from.
        - `position_side` (PositionSide): The side of the body (LEFT, RIGHT, or BOTH).

        ### Returns:
        A `list` of extended joints corresponding to the specified position side.
        """
        if   position_side.is_left():    return cls_name.LEFT_EXTENDED
        elif position_side.is_right():   return cls_name.RIGHT_EXTENDED
        elif position_side.is_front():   return cls_name.EXTENDED
        elif position_side.is_unkwown(): return []
        else:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            import inspect
            ErrorHandler.handle(error=ErrorCode.POSITION_SIDE_DOES_NOT_EXIST, origin=inspect.currentframe())
        return []
    
    ######################
    ### GET ALL JOINTS ###
    ######################
    @classmethod
    def get_all_joints(
            cls,
            cls_name:Squat | BicepsCurl,
            position_side:PositionSide,
            extended_evaluation:bool
        ) -> list[Joint]:
        """
        ### Brief:
        The `get_all_joints` method retrieves all joints (core and optionally extended)
        based on the specified position side.

        ### Arguments:
        - `cls_name` (Squat | BicepsCurl): The joint angle class to retrieve joints from.
        - `position_side` (PositionSide): The side of the body (LEFT, RIGHT, or BOTH).
        - `extended_evaluation` (bool): Whether to include extended joints.

        ### Returns:
        A `list` of joints corresponding to the specified position side and evaluation type.
        """
        if extended_evaluation: return cls._get_core(cls_name, position_side) + cls._get_extended(cls_name, position_side)
        else:                   return cls._get_core(cls_name, position_side)