############################################################
########### BODY TRACK // SERVER // DATA // POSE ###########
############################################################
################### CLASS: PositionSide ####################
############################################################

###############
### IMPORTS ###
###############
from enum import Enum as enum
from typing import List
from Server.Data.Session.ExerciseType import ExerciseType

################################
### POSITION SIDE ENUM CLASS ###
################################
class PositionSide(enum):
    """
    ### Description:
    The `PositionSide` enum class represents the possible camera orientations
    for capturing exercise movements. It defines the sides from which the user
    can be viewed during different exercises.
    """
    UNKNOWN = "UNKNOWN"
    FRONT   = "FRONT"
    LEFT    = "LEFT"
    RIGHT   = "RIGHT"

    #####################
    ### ALLOWED SIDES ###
    #####################
    @classmethod
    def allowed_sides(cls, exercise_type:ExerciseType) -> List["PositionSide"]:
        """
        ### Brief:
        The `allowed_sides` class method returns a list of permissible
        `PositionSide` values based on the specified `ExerciseType`.

        ### Arguments:
        - exercise_type (ExerciseType): The type of exercise being performed.

        ### Returns:
        - List[PositionSide]: A list of allowed position sides for the given exercise type.
        """
        if   exercise_type is ExerciseType.BICEPS_CURL:   return [cls.LEFT, cls.RIGHT]
        elif exercise_type is ExerciseType.SQUAT:         return [cls.FRONT, cls.LEFT, cls.RIGHT]
        elif exercise_type is ExerciseType.LATERAL_RAISE: return [cls.FRONT, cls.LEFT, cls.RIGHT]
        else:                                             return [cls.FRONT, cls.LEFT, cls.RIGHT]