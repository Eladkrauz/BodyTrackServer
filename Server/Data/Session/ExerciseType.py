###############################################################
############ BODY TRACK // SERVER // DATA // SESSION ##########
###############################################################
##################### CLASS: ExerciseType #####################
###############################################################

###############
### IMPORTS ###
###############
from enum import Enum as enum

#####################
### EXERCISE TYPE ###
#####################
class ExerciseType(enum):
    SQUAT           = "squat"
    BICEPS_CURL     = "biceps_curl"

    ###########
    ### GET ###
    ###########
    @staticmethod
    def get(exercise_type: str) -> 'ExerciseType':
        """
        ### Brief:
        The `get` method converts a string into an `ExerciseType` enum value.

        ### Arguments:
        - `exercise_type` (str): The exercise name, case-insensitive.

        ### Returns:
        - `ExerciseType`: The corresponding enum value.

        ### Raises:
        - `ValueError`: If the provided exercise type is unsupported.
        """
        if not isinstance(exercise_type, str):
            raise TypeError("Expected a string for exercise_type.")

        normalized = exercise_type.strip().lower()
        for et in ExerciseType:
            if et.value == normalized:
                return et

        raise ValueError(f"Unsupported exercise: {exercise_type}")