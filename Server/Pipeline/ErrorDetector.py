################################################################
############### BODY TRACK // SERVER // PIPELINE ###############
################################################################
#################### CLASS: ErrorDetector ######################
################################################################

###############
### IMPORTS ###
###############
from __future__ import annotations
from typing import Dict, TYPE_CHECKING, Any
from math import isnan
import inspect

from Server.Data.Phase.PhaseType            import PhaseType
from Server.Data.Session.ExerciseType       import ExerciseType
from Server.Utilities.Error.ErrorHandler    import ErrorHandler
from Server.Utilities.Error.ErrorCode       import ErrorCode
from Server.Utilities.Logger                import Logger
from Server.Data.Session.SessionData        import SessionData
from Server.Data.Error.ErrorMappings        import ErrorMappings
from Server.Data.Error.DetectedErrorCode    import DetectedErrorCode
from Server.Data.History.HistoryData        import HistoryData
from Server.Data.History.HistoryDictKey     import HistoryDictKey
    
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
    • Returns ErrorCodes for invalid states.
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
        try:
            self.retrieve_configurations()
            Logger.info("Initialized successfully.")
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.ERROR_DETECTOR_INIT_ERROR,
                origin=inspect.currentframe(),
                extra_info={"Exception": type(e).__name__, "Reason": str(e)}
            )

    #####################
    ### DETECT ERRORS ###
    #####################
    def detect_errors(self, session:SessionData) -> DetectedErrorCode:
        """
        ### Brief:
        The `detect_errors` method detects biomechanical validation based on the current session state.

        ### Arguments:
        - `session` (SessionData): The current session container.

        ### Returns:
        - `DetectedErrorCode`
        """
        # Ensure last frame is valid.
        history:HistoryData = session.get_history()

        if not history.is_state_ok():
            Logger.debug("History state not OK.")
            return DetectedErrorCode.NOT_READY_FOR_ANALYSIS

        if not history.is_last_frame_actually_valid():
            Logger.debug("Last frame not actually valid.")
            return DetectedErrorCode.NOT_READY_FOR_ANALYSIS
                
        phase:PhaseType = history.get_phase_state() 
        if phase is None:
            ErrorHandler.handle(
                error=ErrorCode.ERROR_DETECTOR_CONFIG_ERROR,
                origin=inspect.currentframe(),
                extra_info={"reason": "Phase is None"}
            )
            return ErrorCode.ERROR_DETECTOR_CONFIG_ERROR
        
        angles:Dict[str, float] = history.get_last_valid_frame().get(HistoryDictKey.Frame.JOINTS)
        if not angles:
            ErrorHandler.handle(
                error=ErrorCode.ERROR_DETECTOR_CONFIG_ERROR,
                origin=inspect.currentframe(),
                extra_info={"reason": "Angles dictionary is empty"}
            )
            return ErrorCode.ERROR_DETECTOR_CONFIG_ERROR
        
        exercise_type:ExerciseType = session.get_exercise_type()
        
        exercise_name = exercise_type.value
        exercise_block = self.thresholds.get(exercise_name)
        if not isinstance(exercise_block, dict):
            ErrorHandler.handle(
                error=ErrorCode.ERROR_DETECTOR_CONFIG_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "exercise": exercise_name,
                    "reason": "Exercise config missing or invalid"
                }
            )
            return ErrorCode.ERROR_DETECTOR_CONFIG_ERROR


        phase_thresholds: Dict[str,Dict[str, Any]] = exercise_block.get(phase.name)
        # A valid exercise may lack thresholds for this specific phase.
        if not phase_thresholds:
            ErrorHandler.handle(
                error=ErrorCode.ERROR_DETECTOR_UNSUPPORTED_PHASE,
                origin=inspect.currentframe(),
                extra_info={"phase": phase.name}
            )
            return ErrorCode.ERROR_DETECTOR_UNSUPPORTED_PHASE
        
        # Iterate angles in the exact order defined in JSON.
        for angle_name, rules in phase_thresholds.items():
            # Angle missing from JointAnalyzer output.
            if angle_name not in angles:
                continue
            value = angles[angle_name]

            # Invalid numeric value.
            if not isinstance(value, (int, float)) or isnan(value):
                ErrorHandler.handle(
                    error=ErrorCode.ERROR_DETECTOR_INVALID_ANGLE,
                    origin=inspect.currentframe(),
                    extra_info={"angle": angle_name, "value": str(value)}
                )
                continue

            # Below MINIMUM.
            if value < rules["min"]:
                mapped = ErrorMappings.get_error(
                    exercise_type=exercise_type,
                    phase=phase,
                    angle_name=angle_name,
                    is_high=False
                )
                if mapped is None:
                    # Mapping missing for valid angle.
                    ErrorHandler.handle(
                        error=ErrorCode.ERROR_DETECTOR_MAPPING_NOT_FOUND,
                        origin=inspect.currentframe(),
                        extra_info={"angle": angle_name,
                                    "reason": "No mapping for low value"}
                    )
                return ErrorCode.ERROR_DETECTOR_MAPPING_NOT_FOUND if mapped is None else mapped

            # Above MAXIMUM.
            if value > rules["max"]:
                mapped = ErrorMappings.get_error(
                    exercise_type=exercise_type,
                    phase=phase,
                    angle_name=angle_name,
                    is_high=True
                )
                if mapped is None:
                    ErrorHandler.handle(
                        error=ErrorCode.ERROR_DETECTOR_MAPPING_NOT_FOUND,
                        origin=inspect.currentframe(),
                        extra_info={"angle": angle_name,
                                    "reason": "No mapping for high value"}
                    )
                return ErrorCode.ERROR_DETECTOR_MAPPING_NOT_FOUND if mapped is None else mapped

        # No biomechanical issues detected.
        return DetectedErrorCode.NO_BIOMECHANICAL_ERROR
        
    ###############################
    ### RETRIEVE CONFIGURATIONS ###
    ###############################
    def retrieve_configurations(self) -> None:
        """
        ### Brief:
        The `retrieve_configurations` method gets the updated configurations from the
        configuration file.
        """
        from Server.Utilities.Config.ConfigLoader import ConfigLoader
        from Server.Utilities.Config.ConfigParameters import ConfigParameters

        self.config_file_path = ConfigLoader.get(
            key=[
                ConfigParameters.Major.ERROR,
                ConfigParameters.Minor.ERROR_DETECTOR_CONFIG_FILE
            ]
        )

        self.thresholds:Dict[str, Any] = ConfigLoader.get(
            key=None,
            different_file=self.config_file_path,
            read_all=True
        )
