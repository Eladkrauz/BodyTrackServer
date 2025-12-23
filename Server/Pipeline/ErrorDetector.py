####################################################################
################# BODY TRACK // SERVER // PIPELINE #################
####################################################################
###################### CLASS: ErrorDetector ########################
####################################################################

###############
### IMPORTS ###
###############
from typing import Dict, Any, List
from math import isnan
import inspect

from Server.Data.Phase.PhaseType         import PhaseType
from Server.Data.Session.ExerciseType    import ExerciseType
from Server.Utilities.Error.ErrorHandler import ErrorHandler
from Server.Utilities.Error.ErrorCode    import ErrorCode
from Server.Utilities.Logger             import Logger
from Server.Data.Session.SessionData     import SessionData
from Server.Data.Error.ErrorMappings     import ErrorMappings
from Server.Data.Error.DetectedErrorCode import DetectedErrorCode
from Server.Data.History.HistoryData     import HistoryData
from Server.Data.History.HistoryDictKey  import HistoryDictKey
from Server.Data.Joints.JointAngle       import JointAngle, Joint
from Server.Data.Phase.PhaseType         import PhaseType
from Server.Data.Phase.PhaseDictKey      import PhaseDictKey
from Server.Data.Pose.PositionSide       import PositionSide
    
############################
### ERROR DETECTOR CLASS ###
############################
class ErrorDetector:
    """
    ### Description:
    The `ErrorDetector` is responsible for **biomechanical validation**.
    It compares joint-angle values (computed by `JointAnalyzer`) against
    exercise-specific threshold ranges loaded from the configuration `JSON`.

    ### Workflow:
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
    • Returns `ErrorCode` for invalid states.
    """
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self):
        """
        ### Brief:
        The `__init__` method initializes the `ErrorDetector` instance.
        Loads all exercise thresholds from configuration.
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

        # If history state is not OK, return NOT_READY_FOR_ANALYSIS.
        if not history.is_state_ok():
            Logger.debug("History state not OK.")
            return DetectedErrorCode.NOT_READY_FOR_ANALYSIS
        
        # If last frame is not actually valid, return NOT_READY_FOR_ANALYSIS.
        if not history.is_last_frame_actually_valid():
            Logger.debug("Last frame not actually valid.")
            return DetectedErrorCode.NOT_READY_FOR_ANALYSIS

        # Get current phase.      
        phase:PhaseType = history.get_phase_state() 
        if phase is None:
            ErrorHandler.handle(
                error=ErrorCode.PHASE_IS_NONE_IN_FRAME,
                origin=inspect.currentframe()
            )
            return ErrorCode.PHASE_IS_NONE_IN_FRAME
        
        # Get angles from last valid frame.
        angles:Dict[str, float] = history.get_last_valid_frame().get(HistoryDictKey.Frame.JOINTS)
        if not angles:
            ErrorHandler.handle(
                error=ErrorCode.ANGLES_DICTIONARY_IS_EMPTY,
                origin=inspect.currentframe()
            )
            return ErrorCode.ANGLES_DICTIONARY_IS_EMPTY
        
        exercise_type:ExerciseType = session.get_exercise_type()
        exercise_name:str = exercise_type.value
        exercise_block:Dict[str, Any] = self.thresholds.get(exercise_name)

        # Iterate angles in the exact order defined in JSON.
        phase_thresholds: Dict[str,Dict[str, Any]] = exercise_block.get(phase.name)
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
                    extra_info={"Angle": angle_name, "Value": str(value)}
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

        # Validate the loaded configuration.
        if not self._validate_exercise_config():
            ErrorHandler.imidiate_abort(
                error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                origin=inspect.currentframe()
            )

        Logger.info("Configurations retrieved and validated successfully.")

    ################################
    ### VALIDATE EXERCISE CONFIG ###
    ################################
    def _validate_exercise_config(self) -> bool:
        """
        ### Brief:
        The `_validate_exercise_config` method validates the JSON dict of exercises configuration.

        ### Returns:
        - `True` if valid.
        - `False` otherwise.
        """
        # Thresholds must be a non-empty dict.
        if self.thresholds is None or not isinstance(self.thresholds, dict) or len(self.thresholds) == 0:
            ErrorHandler.handle(
                error=ErrorCode.ERROR_DETECTOR_CONFIG_ERROR,
                origin=inspect.currentframe(),
                extra_info={ "Config file": "is empty" }
            )
            return False
        
        # Iterating over the exercises configured in the thresholds config.
        for exercise_name, config in self.thresholds.items():
            try:
                # Exercise must exist in ExerciseType.
                exercise_type:ExerciseType = ExerciseType.get(exercise_name)
                # Get Phase enum for this exercise.
                phase_enum:PhaseType = PhaseType.get_phase_enum(exercise_type)
            except ValueError:
                ErrorHandler.handle(
                    error=ErrorCode.EXERCISE_TYPE_DOES_NOT_EXIST,
                    origin=inspect.currentframe(),
                    extra_info={ "Unknown exercise": exercise_name }
                ); return False
            
            for phase in phase_enum:
                if PhaseType.is_none(phase): continue
                if phase.name not in config:
                    ErrorHandler.handle(
                        error=ErrorCode.ERROR_DETECTOR_CONFIG_ERROR,
                        origin=inspect.currentframe(),
                        extra_info={ f"Missing phase block for exercise {exercise_name}": phase.name }
                    ); return False
            
            for phase_name, joints in config.items():
                if not isinstance(joints, dict):
                    ErrorHandler.handle(
                        error=ErrorCode.ERROR_DETECTOR_CONFIG_ERROR,
                        origin=inspect.currentframe(),
                        extra_info={ f"Invalid joints block for exercise {exercise_name}": joints }
                    ); return False
                
                # Get allowed joint names for this exercise type.
                joint_cls:JointAngle = JointAngle.exercise_type_to_joint_type(exercise_type)
                allowed_joint_names:List[str] = [
                    joint.name for joint in
                    JointAngle.get_all_joints(
                        cls_name=joint_cls,
                        position_side=PositionSide.FRONT,
                        extended_evaluation=True
                    )
                ]

                for joint, limits in joints.items():
                    # Joint must be valid.
                    if joint not in allowed_joint_names:
                        ErrorHandler.handle(
                            error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                            origin=inspect.currentframe(),
                            extra_info={ f"Unknown joint for {exercise_name}.{phase_name}": joint }
                        ); return False
                    
                    # Limits must be a dict with min and max numeric values.
                    if PhaseDictKey.MIN not in limits or PhaseDictKey.MAX not in limits:
                        ErrorHandler.handle(
                            error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                            origin=inspect.currentframe(),
                            extra_info={ f"Missing min/max for {exercise_name}.{phase_name}.{joint}": limits }
                        ); return False

                    # Min must be numeric.
                    if not isinstance(limits[PhaseDictKey.MIN], (int, float)):
                        ErrorHandler.handle(
                            error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                            origin=inspect.currentframe(),
                            extra_info={ f"Non-numeric min for {exercise_name}.{phase_name}.{joint}": limits[PhaseDictKey.MIN] }
                        ); return False

                    # Max must be numeric.
                    if not isinstance(limits[PhaseDictKey.MAX], (int, float)):
                        ErrorHandler.handle(
                            error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                            origin=inspect.currentframe(),
                            extra_info={ f"Non-numeric max for {exercise_name}.{phase_name}.{joint}": limits[PhaseDictKey.MAX] }
                        ); return False
                    
                    # Min must be less than or equal to Max.
                    if limits[PhaseDictKey.MIN] > limits[PhaseDictKey.MAX]:
                        ErrorHandler.handle(
                            error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                            origin=inspect.currentframe(),
                            extra_info={ f"Min greater than max for {exercise_name}.{phase_name}.{joint}": limits }
                        ); return False

        return True