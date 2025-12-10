############################################################
############# BODY TRACK SERVER // DATA // PHASE ###########
############################################################
################### CLASS: PhaseType #######################
############################################################

###############
### IMPORTS ###
###############
from __future__ import annotations
from enum import Enum as enum
from enum import auto
from Server.Data.Session.ExerciseType import ExerciseType
from Server.Utilities.Error.ErrorCode import ErrorCode

########################
### PHASE TYPE CLASS ###
########################
class PhaseType:
    """
    ### Description:
    The `PhaseType` class defines phase names (states) for each exercise type.
    Each nested enum represents the discrete states in a full repetition cycle.
    
    The class ensures that phase logic is clearly separated per exercise and 
    can be easily extended for new movements in the future.
    
    ### Example:
    - For Squats: DOWN → HOLD → UP → TOP
    - For Biceps Curl: LOWERING → HOLD → LIFTING → PEAK
    - For Lateral Raise: RAISING → HOLD → LOWERING → REST
    """
    #############
    ### SQUAT ###
    #############
    class Squat(enum):
        NONE = auto() # Initial state (no detection yet).
        DOWN = auto() # Descending phase (knees bending).
        HOLD = auto() # Bottom phase (pause at lowest point).
        UP   = auto() # Ascending phase (returning to standing).
        TOP  = auto() # Fully upright phase (ready/start position).

    ###################
    ### BICEPS CURL ###
    ###################
    class BicepsCurl(enum):
        NONE     = auto() # Initial state (no detection yet).
        LIFTING  = auto() # Curling the arm upward (elbow flexion).
        HOLD     = auto() # Peak of curl (elbow fully flexed).
        LOWERING = auto() # Extending the arm downward.
        REST     = auto() # Fully extended arm position.

    ##############################
    ### LATERAL SHOULDER RAISE ###
    ##############################
    class LateralRaise(enum):
        NONE     = auto() # Initial state (no detection yet).
        RAISING  = auto() # Lifting arms outward/upward.
        HOLD     = auto() # At top position (arms parallel to ground).
        LOWERING = auto() # Bringing arms back down.
        REST     = auto() # Arms fully down by sides.

    ######################
    ### GET PHASE ENUM ###
    ######################
    @staticmethod
    def get_phase_enum(exercise_type:ExerciseType) -> PhaseType | ErrorCode:
        """
        ### Brief:
        The `get_phase_enum` returns the corresponding `enum` class of phases for a given `ExerciseType`.

        ### Arguments:
        - `exercise_type`: The `ExerciseType` enum.

        ### Returns:
        - `PhaseType`: Corresponding phase enum class.
        - `ErrorCode.EXERCISE_TYPE_DOES_NOT_EXIST` if the exercise type is not recognized.
        """
        if   exercise_type == ExerciseType.SQUAT:         return PhaseType.Squat
        elif exercise_type == ExerciseType.BICEPS_CURL:   return PhaseType.BicepsCurl
        elif exercise_type == ExerciseType.LATERAL_RAISE: return PhaseType.LateralRaise
        else:                                             raise ValueError(f"Unsupported exercise: {exercise_type}")