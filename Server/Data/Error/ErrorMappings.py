################################################################
############# BODY TRACK // SERVER // DATA / ERROR #############
################################################################
#################### CLASS: ErrorMappings ######################
################################################################

###############
### IMPORTS ###
###############
from __future__ import annotations
from typing import Dict, Any

from Data.Session.ExerciseType     import ExerciseType
from Data.Phase.PhaseType          import PhaseType
from Data.Error.DetectedErrorCode  import DetectedErrorCode
from Data.Joints.JointAngle        import JointAngle

############################
### ERROR MAPPINGS CLASS ###
############################
class ErrorMappings:
    """
    The `ErrorMappings` class provides phase-aware mappings used by `ErrorDetector`.
    
    It maps: `(exercise_type, phase, angle_name, direction)` -> `DetectedErrorCode`
    """
    LOW  = "LOW"
    HIGH = "HIGH"

    #############################
    ### SQUAT PHASE-AWARE MAP ###
    #############################  
    SQUAT_MAP = {
        PhaseType.Squat.TOP: {
            JointAngle.Squat.TRUNK_TILT.name: {
                LOW:  DetectedErrorCode.SQUAT_TOP_TRUNK_TOO_FORWARD,
                HIGH: DetectedErrorCode.SQUAT_TOP_TRUNK_TOO_BACKWARD
            },
            JointAngle.Squat.HIP_LINE.name: {
                LOW:  DetectedErrorCode.SQUAT_TOP_HIP_LINE_UNBALANCED,
                HIGH: DetectedErrorCode.SQUAT_TOP_HIP_LINE_UNBALANCED
            }
        },
        PhaseType.Squat.DOWN: {
            JointAngle.Squat.LEFT_KNEE.name: {
                LOW:  DetectedErrorCode.SQUAT_DOWN_KNEE_TOO_STRAIGHT,
                HIGH: DetectedErrorCode.SQUAT_DOWN_KNEE_TOO_BENT
            },
            JointAngle.Squat.RIGHT_KNEE.name: {
                LOW:  DetectedErrorCode.SQUAT_DOWN_KNEE_TOO_STRAIGHT,
                HIGH: DetectedErrorCode.SQUAT_DOWN_KNEE_TOO_BENT
            },
            JointAngle.Squat.LEFT_HIP.name: {
                LOW:  DetectedErrorCode.SQUAT_DOWN_HIP_TOO_STRAIGHT,
                HIGH: DetectedErrorCode.SQUAT_DOWN_HIP_TOO_BENT
            },
            JointAngle.Squat.RIGHT_HIP.name: {
                LOW:  DetectedErrorCode.SQUAT_DOWN_HIP_TOO_STRAIGHT,
                HIGH: DetectedErrorCode.SQUAT_DOWN_HIP_TOO_BENT
            }
        },
        PhaseType.Squat.HOLD: {
            JointAngle.Squat.LEFT_HIP.name: {
                LOW:  DetectedErrorCode.SQUAT_HOLD_HIP_NOT_DEEP_ENOUGH,
                HIGH: DetectedErrorCode.SQUAT_HOLD_HIP_TOO_DEEP
            },
            JointAngle.Squat.RIGHT_HIP.name: {
                LOW:  DetectedErrorCode.SQUAT_HOLD_HIP_NOT_DEEP_ENOUGH,
                HIGH: DetectedErrorCode.SQUAT_HOLD_HIP_TOO_DEEP
            },
            JointAngle.Squat.KNEE_VALGUS.name: {
                LOW:  DetectedErrorCode.SQUAT_HOLD_KNEE_VALGUS,
                HIGH: DetectedErrorCode.SQUAT_HOLD_KNEE_VALGUS
            }
        },
        PhaseType.Squat.UP: {
            JointAngle.Squat.LEFT_KNEE.name: {
                LOW:  DetectedErrorCode.SQUAT_UP_KNEE_COLLAPSE,
                HIGH: DetectedErrorCode.SQUAT_UP_KNEE_COLLAPSE
            },
            JointAngle.Squat.RIGHT_KNEE.name: {
                LOW:  DetectedErrorCode.SQUAT_UP_KNEE_COLLAPSE,
                HIGH: DetectedErrorCode.SQUAT_UP_KNEE_COLLAPSE
            },
            JointAngle.Squat.TRUNK_TILT.name: {
                LOW:  DetectedErrorCode.SQUAT_UP_TRUNK_TOO_FORWARD,
                HIGH: DetectedErrorCode.SQUAT_UP_TRUNK_TOO_BACKWARD
            }
        }
    }

    ###################################
    ### BICEPS CURL PHASE-AWARE MAP ###
    ###################################
    BICEPS_CURL_MAP = {
        PhaseType.BicepsCurl.REST: {
            JointAngle.BicepsCurl.LEFT_ELBOW.name: {
                LOW:  DetectedErrorCode.CURL_REST_ELBOW_TOO_BENT,
                HIGH: DetectedErrorCode.CURL_REST_ELBOW_TOO_STRAIGHT,
            },
            JointAngle.BicepsCurl.RIGHT_ELBOW.name: {
                LOW:  DetectedErrorCode.CURL_REST_ELBOW_TOO_BENT,
                HIGH: DetectedErrorCode.CURL_REST_ELBOW_TOO_STRAIGHT,
            },
            JointAngle.BicepsCurl.LEFT_SHOULDER_FLEX.name: {
                LOW:  DetectedErrorCode.CURL_REST_SHOULDER_TOO_BACKWARD,
                HIGH: DetectedErrorCode.CURL_REST_SHOULDER_TOO_FORWARD,
            },
            JointAngle.BicepsCurl.RIGHT_SHOULDER_FLEX.name: {
                LOW:  DetectedErrorCode.CURL_REST_SHOULDER_TOO_BACKWARD,
                HIGH: DetectedErrorCode.CURL_REST_SHOULDER_TOO_FORWARD,
            },
        },
        PhaseType.BicepsCurl.LIFTING: {
            JointAngle.BicepsCurl.LEFT_ELBOW.name: {
                LOW:  DetectedErrorCode.CURL_LIFTING_ELBOW_TOO_STRAIGHT,
                HIGH: DetectedErrorCode.CURL_LIFTING_ELBOW_TOO_BENT,
            },
            JointAngle.BicepsCurl.RIGHT_ELBOW.name: {
                LOW:  DetectedErrorCode.CURL_LIFTING_ELBOW_TOO_STRAIGHT,
                HIGH: DetectedErrorCode.CURL_LIFTING_ELBOW_TOO_BENT,
            },
            JointAngle.BicepsCurl.LEFT_SHOULDER_FLEX.name: {
                LOW:  DetectedErrorCode.CURL_LIFTING_SHOULDER_TOO_BACKWARD,
                HIGH: DetectedErrorCode.CURL_LIFTING_SHOULDER_TOO_FORWARD,
            },
            JointAngle.BicepsCurl.RIGHT_SHOULDER_FLEX.name: {
                LOW:  DetectedErrorCode.CURL_LIFTING_SHOULDER_TOO_BACKWARD,
                HIGH: DetectedErrorCode.CURL_LIFTING_SHOULDER_TOO_FORWARD,
            },
        },
        PhaseType.BicepsCurl.HOLD: {
            JointAngle.BicepsCurl.LEFT_ELBOW.name: {
                LOW:  DetectedErrorCode.CURL_HOLD_ELBOW_TOO_CLOSED,
                HIGH: DetectedErrorCode.CURL_HOLD_ELBOW_TOO_OPEN,
            },
            JointAngle.BicepsCurl.RIGHT_ELBOW.name: {
                LOW:  DetectedErrorCode.CURL_HOLD_ELBOW_TOO_CLOSED,
                HIGH: DetectedErrorCode.CURL_HOLD_ELBOW_TOO_OPEN,
            },
            JointAngle.BicepsCurl.LEFT_WRIST.name: {
                LOW:  DetectedErrorCode.CURL_HOLD_WRIST_TOO_FLEXED,
                HIGH: DetectedErrorCode.CURL_HOLD_WRIST_TOO_EXTENDED,
            },
            JointAngle.BicepsCurl.RIGHT_WRIST.name: {
                LOW:  DetectedErrorCode.CURL_HOLD_WRIST_TOO_FLEXED,
                HIGH: DetectedErrorCode.CURL_HOLD_WRIST_TOO_EXTENDED,
            },
        },
        PhaseType.BicepsCurl.LOWERING: {
            JointAngle.BicepsCurl.LEFT_ELBOW.name: {
                LOW:  DetectedErrorCode.CURL_LOWERING_ELBOW_TOO_STRAIGHT,
                HIGH: DetectedErrorCode.CURL_LOWERING_ELBOW_TOO_BENT,
            },
            JointAngle.BicepsCurl.RIGHT_ELBOW.name: {
                LOW:  DetectedErrorCode.CURL_LOWERING_ELBOW_TOO_STRAIGHT,
                HIGH: DetectedErrorCode.CURL_LOWERING_ELBOW_TOO_BENT,
            },
            JointAngle.BicepsCurl.LEFT_SHOULDER_FLEX.name: {
                LOW:  DetectedErrorCode.CURL_LOWERING_SHOULDER_TOO_BACKWARD,
                HIGH: DetectedErrorCode.CURL_LOWERING_SHOULDER_TOO_FORWARD,
            },
            JointAngle.BicepsCurl.RIGHT_SHOULDER_FLEX.name: {
                LOW:  DetectedErrorCode.CURL_LOWERING_SHOULDER_TOO_BACKWARD,
                HIGH: DetectedErrorCode.CURL_LOWERING_SHOULDER_TOO_FORWARD,
            },
        }
    }

    ##############################################
    ### MASTER MAP (ExerciseType -> Phase Map) ###
    ##############################################
    """
    The `MASTER_MAP` dictionary maps ExerciseType to its phase-aware error map.
    """
    MASTER_MAP: Dict[ExerciseType, Dict[Any, Dict[str, Dict[str, DetectedErrorCode]]]] = {
        ExerciseType.SQUAT:         SQUAT_MAP,
        ExerciseType.BICEPS_CURL:   BICEPS_CURL_MAP,
    }

    #################
    ### GET ERROR ###
    #################
    @classmethod
    def get_error(cls, exercise_type:ExerciseType, phase:PhaseType, angle_name:str, is_high:bool) -> DetectedErrorCode | None:
        """
        ### Brief:
        The `get_error` method retrieves the corresponding `DetectedErrorCode` based on the
        provided parameters.

        ### Arguments:
        - `exercise_type` (ExerciseType): The type of exercise being performed.
        - `phase` (PhaseType): The current phase of the exercise.
        - `angle_name` (str): The name of the joint angle being evaluated.
        - `is_high` (bool): A boolean indicating whether to look for a HIGH or LOW error condition.

        ### Returns:
        - `DetectedErrorCode | None`: The corresponding `DetectedErrorCode` if found; otherwise, `None`.
        """
        # Determine direction string based on is_high boolean.
        direction:str = cls.HIGH if is_high else cls.LOW

        # Navigate through the nested dictionaries to find the error code.
        exercise_map:Dict[PhaseType, Dict] = cls.MASTER_MAP.get(exercise_type)
        if not exercise_map: return None
        phase_map:Dict[str, Dict] = exercise_map.get(phase)
        if not phase_map: return None
        angle_map:Dict[str, DetectedErrorCode] = phase_map.get(angle_name)
        if not angle_map: return None

        # Return the DetectedErrorCode based on the direction.
        return angle_map.get(direction, None)