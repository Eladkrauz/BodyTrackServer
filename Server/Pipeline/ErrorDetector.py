################################################################
############### BODY TRACK // SERVER // PIPELINE ###############
################################################################
#################### CLASS: ErrorDetector ######################
################################################################

###############
### IMPORTS ###
###############
from __future__ import annotations
from typing import Dict, TYPE_CHECKING
from math import isnan
import inspect

from Server.Data.Phase.PhaseType import PhaseType
from Server.Data.Session.ExerciseType import ExerciseType
from Server.Utilities.Config.ConfigLoader import ConfigLoader
from Server.Utilities.Config.ConfigParameters import ConfigParameters
from Server.Utilities.Error.ErrorHandler import ErrorHandler
from Server.Utilities.Error.ErrorCode import ErrorCode
from Server.Data.Session.SessionData import SessionData
from Server.Data.Error.ErrorMappings import ErrorMappings
from Server.Data.Error.DetectedErrorCode import DetectedErrorCode

if TYPE_CHECKING:
    from Server.Data.History.HistoryData import HistoryData
    from Server.Data.History.HistoryDictKey import HistoryDictKey
############################
### ERROR DETECTOR CLASS ###
############################
class ErrorDetector:
    """
    The `ErrorDetector` is responsible for **biomechanical validation**.
    It compares joint-angle values (computed by `JointAnalyzer`) against
    exercise-specific threshold ranges loaded from the configuration `JSON`.

    For every frame, the class:
    1. Receives `exercise_name`, current `phase`, and all joint `angles`.
    2. Locates the threshold ranges for this exercise + phase.
    3. Iterates through the angles **in JSON order** (this defines priority).
    4. For each angle:
         - Validates that the angle exists and is numeric.
         - Compares value to the allowed min/max.
         - If out of bounds → maps the angle to a biomechanical error code.
    5. Stops at the **first detected error**.

    • Returns a `DetectedErrorCode` (enum) indicating biomechanical error.
    • Returns None if:
        - All joints were valid.
        - No biomechanical error was detected.
        - Exercise/phase is unsupported.
    """

    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self):
        """
        ### Brief:
        The `__init__` method initializes the `ErrorDetector` instance.
        Loads all exercise thresholds from configuration.
        Uses ErrorHandler on failure and initializes with empty thresholds.
        """
        self.thresholds = ConfigLoader.get(
            key=None,
            different_file="Server/Files/Config/ExerciseThresholds.JSON",
            read_all=True
        )

    #####################
    ### DETECT ERRORS ###
    #####################
    def detect_errors(self, session: SessionData) -> DetectedErrorCode | None:
        """
        ### Brief:
        The `detect_errors` method detects biomechanical validation based on the current session state.

        ### Arguments:
        - `session` (SessionData):
            The current session container, which must provide:
            - `exercise_type` (ExerciseType)
            - `history_data` (HistoryData) with:
                - `get_current_phase() -> PhaseType | None`
                - `get_current_angles() -> dict[str, float] | None`

        ### Returns:
        - `DetectedErrorCode` if a biomechanical error is detected.
        - `None` if:
            - No errors detected.
            - Exercise/phase unsupported.
            - Missing phase/angles/history.
        """
        #load history data from session object
        # Ensure last frame is valid.
        history:HistoryData = session.history_data
        if not history.is_last_frame_actually_valid(): return # Do nothing.
        
        exercise_type : ExerciseType = session.exercise_type
        exercise_name = exercise_type.value
        phase:PhaseType = history.get_phase_state()
        angles:Dict[str, float] = history.history[HistoryDictKey.LAST_VALID_FRAME][HistoryDictKey.Frame.JOINTS]

        # Unknown exercise (misconfigured or unsupported).
        if exercise_name not in self.thresholds:
            ErrorHandler.handle(
                error=ErrorCode.ERROR_DETECTOR_UNSUPPORTED_EXERCISE,
                origin=inspect.currentframe(),
                extra_info={"exercise": exercise_name}
            )
            return ErrorCode.ERROR_DETECTOR_UNSUPPORTED_EXERCISE

        phase_thresholds = self.thresholds[exercise_name].get(phase.name)

        # A valid exercise may lack thresholds for this specific phase.
        if not phase_thresholds:
            return ErrorCode.ERROR_DETECTOR_UNSUPPORTED_PHASE

        # Iterate angles in the exact order defined in JSON.
        for angle_name, rules in phase_thresholds.items():

            # Angle missing from JointAnalyzer output.
            if angle_name not in angles:
                ErrorHandler.handle(
                    error=ErrorCode.ERROR_DETECTOR_INVALID_ANGLE,
                    origin=inspect.currentframe(),
                    extra_info={"angle": angle_name}
                )
                continue

            value = angles[angle_name]

            # Invalid numeric value.
            if value is None or isnan(value):
                ErrorHandler.handle(
                    error=ErrorCode.ERROR_DETECTOR_INVALID_ANGLE,
                    origin=inspect.currentframe(),
                    extra_info={"angle": angle_name, "value": str(value)}
                )
                continue

            # Below MINIMUM.
            if value < rules["min"]:
                mapped = self._map_angle_to_error_low(exercise_name, angle_name)
                if mapped is None:
                    # Mapping missing for valid angle.
                    ErrorHandler.handle(
                        error=ErrorCode.ERROR_DETECTOR_MAPPING_NOT_FOUND,
                        origin=inspect.currentframe(),
                        extra_info={"angle": angle_name}
                    )
                return mapped

            # Above MAXIMUM.
            if value > rules["max"]:
                mapped = self._map_angle_to_error_high(exercise_name, angle_name)
                if mapped is None:
                    ErrorHandler.handle(
                        error=ErrorCode.ERROR_DETECTOR_MAPPING_NOT_FOUND,
                        origin=inspect.currentframe(),
                        extra_info={"angle": angle_name}
                    )
                return mapped

        # No biomechanical issues detected.
        return None

    ##############################
    ### MAP ANGLE TO ERROR LOW ###
    ##############################
    def _map_angle_to_error_low(self, exercise: str, angle_name: str):
        """
        ### Brief:
        The `_map_angle_to_error_low` method maps an angle (below minimum range) to a biomechanical DetectedErrorCode.

        ### Arguments:
        - `exercise` (str): The exercise being performed.
        - `angle_name` (str): The name of the joint angle.

        ### Returns:
        - `DetectedErrorCode` (enum) if mapping exists.
        - `None` if no mapping exists.
        """
        if   exercise is ExerciseType.SQUAT:         return ErrorMappings.SQUAT_ERROR_MAP_LOW.get(angle_name)
        elif exercise is ExerciseType.BICEPS_CURL:   return ErrorMappings.BICEPS_CURL_ERROR_MAP_LOW.get(angle_name)
        elif exercise is ExerciseType.LATERAL_RAISE: return ErrorMappings.LATERAL_RAISE_ERROR_MAP_LOW.get(angle_name)
        else:                                        return None

    ###############################
    ### MAP ANGLE TO ERROR HIGH ###
    ###############################
    def _map_angle_to_error_high(self, exercise: str, angle_name: str):
        """
        ### Brief:
        The `_map_angle_to_error_high` method maps an angle (above maximum range) to a biomechanical DetectedErrorCode.

        ### Arguments:
        - `exercise` (str): The exercise being performed.
        - `angle_name` (str): The name of the joint angle.

        ### Returns:
        - `DetectedErrorCode` (enum) if mapping exists.
        - `None` if no mapping exists.
        """
        if   exercise is ExerciseType.SQUAT:         return ErrorMappings.SQUAT_ERROR_MAP_HIGH.get(angle_name)
        elif exercise is ExerciseType.BICEPS_CURL:   return ErrorMappings.BICEPS_CURL_ERROR_MAP_HIGH.get(angle_name)
        elif exercise is ExerciseType.LATERAL_RAISE: return ErrorMappings.LATERAL_RAISE_ERROR_MAP_HIGH.get(angle_name)
        else:                                        return None