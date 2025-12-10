############################################################
############# BODY TRACK // SERVER // PIPELINE #############
############################################################
################### CLASS: PhaseDetector ###################
############################################################

###############
### IMPORTS ###
###############
from typing import Dict, Any
import inspect


from Server.Utilities.Error.ErrorCode import ErrorCode
from Server.Utilities.Error.ErrorHandler import ErrorHandler
from Server.Utilities.Logger          import Logger

from Server.Data.Session.ExerciseType import ExerciseType
from Server.Data.Session.SessionData  import SessionData
from Server.Data.Phase.PhaseType      import PhaseType
from Server.Data.Phase.PhaseDictKey   import PhaseDictKey
from Server.Data.Joints.JointAngle    import JointAngle

############################
### PHASE DETECTOR CLASS ###
############################
class PhaseDetector:
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self):
        self.retrieve_configurations()

        Logger.info("Initialized successfully.")

    #######################
    ### DETERMINE PHASE ###
    #######################
    def determine_phase(self, session_data:SessionData) -> PhaseType | ErrorCode:
        pass

    ####################################
    ### ENSURE INITIAL PHASE CORRECT ###
    ####################################
    def ensure_initial_phase_correct(self, session_data:SessionData, joints:Dict[str, Any]) -> bool | ErrorCode:
        """
        ### Brief:
        The `ensure_initial_phase_correct` method ensures that the initial phase
        detected is correct based on predefined correct initial phase of the exercise.

        ### Args:
        - `session_data` (SessionData): The session data containing relevant information.
        - `joints` (Dict[str, Any]): The joint data used for phase detection.

        ### Returns:
        - `True` if the initial phase is correct according to the `ExerciseType`.
        - `False` if incorrect.
        - `ErrorCode` in case of an error.
        """
        try:
            exercise_type:ExerciseType = session_data.get_exercise_type()
            exercise_thresholds:Dict[str, Any] = self.thresholds.get(exercise_type.value, {})
            if exercise_thresholds is None:
                ErrorHandler.handle(
                    error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Missing exercise type:": exercise_type.value
                    }
                ); return ErrorCode.INTERNAL_SERVER_ERROR
            
            correct_initial_phase:PhaseType = exercise_thresholds.get(PhaseDictKey.INITIAL_PHASE, None)
            if correct_initial_phase is None:
                ErrorHandler.handle(
                    error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Missing initial phase for exercise type:": exercise_type.value
                    }
                ); return ErrorCode.INTERNAL_SERVER_ERROR


            # Example criteria check (to be replaced with actual logic):
            initial_phase = session_data.get_current_phase()
            if initial_phase == PhaseType.START and joints.get("SpineBase", {}).get("y", 0) < self.thresholds.get("InitialPhaseHeightThreshold", 0):
                Logger.info("Initial phase verified as correct.")
                return True
            else:
                Logger.info("Initial phase verification failed.")
                return False

        except Exception as e:
            Logger.error(f"Error in {inspect.currentframe().f_code.co_name}: {str(e)}")
            return ErrorCode.PHASE_DETECTION_ERROR


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

        # Load configuration file path.
        self.config_file_path:str = ConfigLoader.get(
            key=[
                ConfigParameters.Major.PHASE,
                ConfigParameters.Minor.PHASE_DETECTOR_CONFIG_FILE
            ]
        )

        # Load thresholds from the specific configuration file.
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

    from enum import Enum

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
                error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
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

            # Essential keys must exist.
            for key in (PhaseDictKey.RULES, PhaseDictKey.INITIAL_PHASE, PhaseDictKey.TRANSITION_ORDER):
                if key not in config:
                    ErrorHandler.handle(
                        error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                        origin=inspect.currentframe(),
                        extra_info={ f"Missing '{key}' for exercise": exercise_name }
                    ); return False

            rules      = config[PhaseDictKey.RULES]
            initial    = config[PhaseDictKey.INITIAL_PHASE]
            transition = config[PhaseDictKey.TRANSITION_ORDER]

            # Check rules contain all phase names.
            phase_names:set = { phase.name for phase in phase_enum if phase.name != "NONE" }

            # Check for missing phases in rules.
            missing_phases = phase_names - rules.keys()
            if missing_phases: # There are missing phases.
                ErrorHandler.handle(
                    error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={ f"Missing phases for exercise {exercise_name}": list(missing_phases) }
                ); return False

            # Validate every phase rule block.
            for phase_name, joints in rules.items():
                # Phase name must be valid.
                if phase_name not in phase_names:
                    ErrorHandler.handle(
                        error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                        origin=inspect.currentframe(),
                        extra_info={ f"Unknown phase for exercise {exercise_name}": phase_name }
                    ); return False
                
                # Joints must be a non-empty dict.
                if not isinstance(joints, dict) or len(joints) == 0:
                    ErrorHandler.handle(
                        error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                        origin=inspect.currentframe(),
                        extra_info={ f"Invalid joint rules for {exercise_name}.{phase_name}": joints }
                    ); return False
                
                # check joint -> (min,max)
                joint_cls:JointAngle = JointAngle.exercise_type_to_joint_type(exercise_type)
                allowed_joint_names:set = { j.name for j in (joint_cls.CORE + joint_cls.EXTENDED) }
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

            # Initial_phase must be valid.
            if initial not in phase_names:
                ErrorHandler.handle(
                    error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={ f"Invalid initial_phase for exercise {exercise_name}": initial }
                ); return False

            # Transition_order must be list of valid phases.
            if not isinstance(transition, list):
                ErrorHandler.handle(
                    error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={ f"transition_order not a list for exercise {exercise_name}": transition }
                ); return False
            
            # Each phase in transition_order must be valid.
            for phase in transition:
                if phase not in phase_names:
                    ErrorHandler.handle(
                        error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                        origin=inspect.currentframe(),
                        extra_info={ f"Invalid phase in transition_order for exercise {exercise_name}": phase }
                    ); return False
            
            # Transition order must start and end with the same phase.
            if transition[0] != transition[-1] or len(transition) < 2:
                ErrorHandler.handle(
                    error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={ f"transition_order must start and end with the same phase for exercise {exercise_name}": transition }
                ); return False
            
            # Transition order must start with initial_phase.
            if transition[0] != initial:
                ErrorHandler.handle(
                    error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={ f"transition_order must start with initial_phase for exercise {exercise_name}": transition }
                ); return False

        return True