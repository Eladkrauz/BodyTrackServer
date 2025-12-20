############################################################
############ BODY TRACK / SERVER / DATA / ERROR ############
############################################################
##################### CLASS: ErrorMappings #################
############################################################

###############
### IMPORTS ###
###############
from __future__ import annotations
from typing import Dict, Optional, Any

from Server.Data.Session.ExerciseType     import ExerciseType
from Server.Data.Phase.PhaseType          import PhaseType
from Server.Data.Error.DetectedErrorCode  import DetectedErrorCode


############################
### ERROR MAPPINGS CLASS ###
############################
class ErrorMappings:
    """
    The `ErrorMappings` class provides phase-aware mappings used by ErrorDetector.

    Maps:
        (exercise_type, phase, angle_name, direction) -> DetectedErrorCode

    direction is "LOW" / "HIGH" (violation below min / above max).
    """

    LOW  = "LOW"
    HIGH = "HIGH"

    #############################
    ### SQUAT PHASE-AWARE MAP ###
    #############################  
    SQUAT_MAP = {

        PhaseType.Squat.TOP: {
            "trunk_tilt_angle": {
                LOW:  DetectedErrorCode.SQUAT_TOP_TRUNK_TOO_FORWARD,
                HIGH: DetectedErrorCode.SQUAT_TOP_TRUNK_TOO_BACKWARD
            },
            "hip_line_angle": {
                LOW:  DetectedErrorCode.SQUAT_TOP_HIP_LINE_UNBALANCED,
                HIGH: DetectedErrorCode.SQUAT_TOP_HIP_LINE_UNBALANCED
            }
        },

        PhaseType.Squat.DOWN: {
            "left_knee_angle": {
                LOW:  DetectedErrorCode.SQUAT_DOWN_KNEE_TOO_STRAIGHT,
                HIGH: DetectedErrorCode.SQUAT_DOWN_KNEE_TOO_BENT
            },
            "right_knee_angle": {
                LOW:  DetectedErrorCode.SQUAT_DOWN_KNEE_TOO_STRAIGHT,
                HIGH: DetectedErrorCode.SQUAT_DOWN_KNEE_TOO_BENT
            },
            "left_hip_angle": {
                LOW:  DetectedErrorCode.SQUAT_DOWN_HIP_TOO_STRAIGHT,
                HIGH: DetectedErrorCode.SQUAT_DOWN_HIP_TOO_BENT
            },
            "right_hip_angle": {
                LOW:  DetectedErrorCode.SQUAT_DOWN_HIP_TOO_STRAIGHT,
                HIGH: DetectedErrorCode.SQUAT_DOWN_HIP_TOO_BENT
            }
        },

        PhaseType.Squat.HOLD: {
            "left_hip_angle": {
                LOW:  DetectedErrorCode.SQUAT_HOLD_HIP_NOT_DEEP_ENOUGH,
                HIGH: DetectedErrorCode.SQUAT_HOLD_HIP_TOO_DEEP
            },
            "right_hip_angle": {
                LOW:  DetectedErrorCode.SQUAT_HOLD_HIP_NOT_DEEP_ENOUGH,
                HIGH: DetectedErrorCode.SQUAT_HOLD_HIP_TOO_DEEP
            },
            "knee_valgus_angle": {
                LOW:  DetectedErrorCode.SQUAT_HOLD_KNEE_VALGUS,
                HIGH: DetectedErrorCode.SQUAT_HOLD_KNEE_VALGUS
            }
        },

        PhaseType.Squat.UP: {
            "left_knee_angle": {
                LOW:  DetectedErrorCode.SQUAT_UP_KNEE_COLLAPSE,
                HIGH: DetectedErrorCode.SQUAT_UP_KNEE_COLLAPSE
            },
            "right_knee_angle": {
                LOW:  DetectedErrorCode.SQUAT_UP_KNEE_COLLAPSE,
                HIGH: DetectedErrorCode.SQUAT_UP_KNEE_COLLAPSE
            },
            "trunk_tilt_angle": {
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

            "left_elbow_angle": {
                LOW:  DetectedErrorCode.CURL_REST_ELBOW_TOO_BENT,
                HIGH: DetectedErrorCode.CURL_REST_ELBOW_TOO_STRAIGHT,
            },
            "right_elbow_angle": {
                LOW:  DetectedErrorCode.CURL_REST_ELBOW_TOO_BENT,
                HIGH: DetectedErrorCode.CURL_REST_ELBOW_TOO_STRAIGHT,
            },

            "left_shoulder_flexion_angle": {
                LOW:  DetectedErrorCode.CURL_REST_SHOULDER_TOO_BACKWARD,
                HIGH: DetectedErrorCode.CURL_REST_SHOULDER_TOO_FORWARD,
            },
            "right_shoulder_flexion_angle": {
                LOW:  DetectedErrorCode.CURL_REST_SHOULDER_TOO_BACKWARD,
                HIGH: DetectedErrorCode.CURL_REST_SHOULDER_TOO_FORWARD,
            },
        },

        PhaseType.BicepsCurl.LIFTING: {

            "left_elbow_angle": {
                LOW:  DetectedErrorCode.CURL_LIFTING_ELBOW_TOO_STRAIGHT,
                HIGH: DetectedErrorCode.CURL_LIFTING_ELBOW_TOO_BENT,
            },
            "right_elbow_angle": {
                LOW:  DetectedErrorCode.CURL_LIFTING_ELBOW_TOO_STRAIGHT,
                HIGH: DetectedErrorCode.CURL_LIFTING_ELBOW_TOO_BENT,
            },

            "left_shoulder_flexion_angle": {
                LOW:  DetectedErrorCode.CURL_LIFTING_SHOULDER_TOO_BACKWARD,
                HIGH: DetectedErrorCode.CURL_LIFTING_SHOULDER_TOO_FORWARD,
            },
            "right_shoulder_flexion_angle": {
                LOW:  DetectedErrorCode.CURL_LIFTING_SHOULDER_TOO_BACKWARD,
                HIGH: DetectedErrorCode.CURL_LIFTING_SHOULDER_TOO_FORWARD,
            },
        },

        PhaseType.BicepsCurl.HOLD: {

            "left_elbow_angle": {
                LOW:  DetectedErrorCode.CURL_HOLD_ELBOW_TOO_OPEN,
                HIGH: DetectedErrorCode.CURL_HOLD_ELBOW_TOO_CLOSED,
            },
            "right_elbow_angle": {
                LOW:  DetectedErrorCode.CURL_HOLD_ELBOW_TOO_OPEN,
                HIGH: DetectedErrorCode.CURL_HOLD_ELBOW_TOO_CLOSED,
            },

            "left_wrist_angle": {
                LOW:  DetectedErrorCode.CURL_HOLD_WRIST_TOO_FLEXED,
                HIGH: DetectedErrorCode.CURL_HOLD_WRIST_TOO_EXTENDED,
            },
            "right_wrist_angle": {
                LOW:  DetectedErrorCode.CURL_HOLD_WRIST_TOO_FLEXED,
                HIGH: DetectedErrorCode.CURL_HOLD_WRIST_TOO_EXTENDED,
            },
        },

        PhaseType.BicepsCurl.LOWERING: {

            "left_elbow_angle": {
                LOW:  DetectedErrorCode.CURL_LOWERING_ELBOW_TOO_STRAIGHT,
                HIGH: DetectedErrorCode.CURL_LOWERING_ELBOW_TOO_BENT,
            },
            "right_elbow_angle": {
                LOW:  DetectedErrorCode.CURL_LOWERING_ELBOW_TOO_STRAIGHT,
                HIGH: DetectedErrorCode.CURL_LOWERING_ELBOW_TOO_BENT,
            },

            "left_shoulder_flexion_angle": {
                LOW:  DetectedErrorCode.CURL_LOWERING_SHOULDER_TOO_BACKWARD,
                HIGH: DetectedErrorCode.CURL_LOWERING_SHOULDER_TOO_FORWARD,
            },
            "right_shoulder_flexion_angle": {
                LOW:  DetectedErrorCode.CURL_LOWERING_SHOULDER_TOO_BACKWARD,
                HIGH: DetectedErrorCode.CURL_LOWERING_SHOULDER_TOO_FORWARD,
            },
        }
    }


    #####################################
    ### LATERAL RAISE PHASE-AWARE MAP ###
    #####################################
    LATERAL_RAISE_MAP = {

        PhaseType.LateralRaise.REST: {

            "left_shoulder_abduction_angle": {
                LOW:  DetectedErrorCode.LATERAL_REST_ARM_TOO_LOW,
                HIGH: DetectedErrorCode.LATERAL_REST_ARM_TOO_HIGH,
            },
            "right_shoulder_abduction_angle": {
                LOW:  DetectedErrorCode.LATERAL_REST_ARM_TOO_LOW,
                HIGH: DetectedErrorCode.LATERAL_REST_ARM_TOO_HIGH,
            },

            "torso_lateral_tilt_angle": {
                LOW:  DetectedErrorCode.LATERAL_REST_TORSO_TILT_LEFT_RIGHT,
                HIGH: DetectedErrorCode.LATERAL_REST_TORSO_TILT_LEFT_RIGHT,
            },
        },

        PhaseType.LateralRaise.RAISING: {

            "left_shoulder_abduction_angle": {
                LOW:  DetectedErrorCode.LATERAL_RAISE_ARM_TOO_LOW,
                HIGH: DetectedErrorCode.LATERAL_RAISE_ARM_TOO_HIGH,
            },
            "right_shoulder_abduction_angle": {
                LOW:  DetectedErrorCode.LATERAL_RAISE_ARM_TOO_LOW,
                HIGH: DetectedErrorCode.LATERAL_RAISE_ARM_TOO_HIGH,
            },

            "left_elbow_set_angle": {
                LOW:  DetectedErrorCode.LATERAL_RAISE_ELBOW_TOO_BENT,
                HIGH: DetectedErrorCode.LATERAL_RAISE_ELBOW_TOO_BENT,
            },
            "right_elbow_set_angle": {
                LOW:  DetectedErrorCode.LATERAL_RAISE_ELBOW_TOO_BENT,
                HIGH: DetectedErrorCode.LATERAL_RAISE_ELBOW_TOO_BENT,
            },
        },

        PhaseType.LateralRaise.HOLD: {

            "left_shoulder_abduction_angle": {
                LOW:  DetectedErrorCode.LATERAL_HOLD_ARM_TOO_LOW,
                HIGH: DetectedErrorCode.LATERAL_HOLD_ARM_TOO_HIGH,
            },
            "right_shoulder_abduction_angle": {
                LOW:  DetectedErrorCode.LATERAL_HOLD_ARM_TOO_LOW,
                HIGH: DetectedErrorCode.LATERAL_HOLD_ARM_TOO_HIGH,
            },

            "torso_lateral_tilt_angle": {
                LOW:  DetectedErrorCode.LATERAL_HOLD_TORSO_TILT_LEFT_RIGHT,
                HIGH: DetectedErrorCode.LATERAL_HOLD_TORSO_TILT_LEFT_RIGHT,
            },
        },

        PhaseType.LateralRaise.LOWERING: {

            "left_shoulder_abduction_angle": {
                LOW:  DetectedErrorCode.LATERAL_LOWER_ARM_TOO_LOW,
                HIGH: DetectedErrorCode.LATERAL_LOWER_ARM_TOO_HIGH,
            },
            "right_shoulder_abduction_angle": {
                LOW:  DetectedErrorCode.LATERAL_LOWER_ARM_TOO_LOW,
                HIGH: DetectedErrorCode.LATERAL_LOWER_ARM_TOO_HIGH,
            },

            "left_elbow_set_angle": {
                LOW:  DetectedErrorCode.LATERAL_LOWER_ELBOW_TOO_BENT,
                HIGH: DetectedErrorCode.LATERAL_LOWER_ELBOW_TOO_BENT,
            },
            "right_elbow_set_angle": {
                LOW:  DetectedErrorCode.LATERAL_LOWER_ELBOW_TOO_BENT,
                HIGH: DetectedErrorCode.LATERAL_LOWER_ELBOW_TOO_BENT,
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
        ExerciseType.LATERAL_RAISE: LATERAL_RAISE_MAP
    }

    ##################
    ### PUBLIC API ###
    ##################
    @classmethod
    def get_error(
        cls,
        exercise_type: ExerciseType,
        phase: Any,
        angle_name: str,
        is_high: bool
    ) -> Optional[DetectedErrorCode]:
        """
        The `get_error` method returns a DetectedErrorCode for (exercise, phase, angle, direction).
        If no mapping exists -> returns None (caller may continue safely).
        """
        direction = cls.HIGH if is_high else cls.LOW

        exercise_map = cls.MASTER_MAP.get(exercise_type)
        if not exercise_map:
            return None

        phase_map = exercise_map.get(phase)
        if not phase_map:
            return None

        angle_map = phase_map.get(angle_name)
        if not angle_map:
            return None

        return angle_map.get(direction)
