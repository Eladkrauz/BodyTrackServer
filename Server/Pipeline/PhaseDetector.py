############################################################
############# BODY TRACK // SERVER // PIPELINE #############
############################################################
################### CLASS: PhaseDetector ###################
############################################################

###############
### IMPORTS ###
###############
from typing import Dict, Any, List
import inspect

from Server.Utilities.Error.ErrorCode    import ErrorCode
from Server.Utilities.Error.ErrorHandler import ErrorHandler
from Server.Utilities.Logger             import Logger

from Server.Data.Session.ExerciseType    import ExerciseType
from Server.Data.Session.SessionData     import SessionData
from Server.Data.Phase.PhaseType         import PhaseType
from Server.Data.Phase.PhaseDictKey      import PhaseDictKey
from Server.Data.Joints.JointAngle       import JointAngle
from Server.Data.History.HistoryDictKey  import HistoryDictKey
from Server.Data.History.HistoryData     import HistoryData

############################
### PHASE DETECTOR CLASS ###
############################
class PhaseDetector:
    """
    ### Description:
    The `PhaseDetector` class is responsible for determining the current phase of an exercise
    based on joint angle data and predefined rules.

    The class utilizes configurations loaded from a JSON file to define the rules for each exercise type.

    It provides methods to:
        1. Determine the current phase based on joint angles.
        2. Ensure the initial phase is correct according to the exercise type.
    """
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self):
        """
        ### Brief:
        The `__init__` method initializes the PhaseDetector class by retrieving configurations.
        """
        self.retrieve_configurations()

        Logger.info("Initialized successfully.")

    #######################
    ### DETERMINE PHASE ###
    #######################
    def determine_phase(self, session_data:SessionData) -> PhaseType | ErrorCode:
        """
        ### Brief:
        The `determine_phase` method determines the current phase of the exercise
        based on the latest joint angle data and predefined rules.

        ### Arguments:
        - `session_data` (SessionData): The session data containing relevant information.

        ### Returns:
        - `PhaseType` representing the determined phase.
        - `ErrorCode` in case of an error.
        """
        history:HistoryData = session_data.get_history()
        # Ensure session state is stable.
        if not history.is_state_ok():
            ErrorHandler.handle(
                error=ErrorCode.TRIED_TO_DETECT_FRAME_FOR_UNSTABLE_STATE,
                origin=inspect.currentframe()
            )
            return ErrorCode.TRIED_TO_DETECT_FRAME_FOR_UNSTABLE_STATE
        
        # Ensure there is valid frame data to analyze.
        if not history.is_last_frame_actually_valid():
            return history.get_phase_state()

        # Load configuration for this exercise.
        exercise_configuration:Dict[str, Any] = self._get_exercise_config(session_data)
        if isinstance(exercise_configuration, ErrorCode): return exercise_configuration

        # Get the rules of the exercise, from the configuration.
        rules = exercise_configuration.get(PhaseDictKey.RULES, None)
        if rules is None: return ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR

        # Retrieve the latest joints from history.
        last_valid_frame:Dict[str, Any] = session_data.get_history().get_last_valid_frame()
        last_valid_joints:Dict[str, Any] = last_valid_frame[HistoryDictKey.Frame.JOINTS]
        if last_valid_joints is None or len(last_valid_joints) == 0:
            return ErrorCode.NO_VALID_FRAME_DATA_IN_SESSION

        # Check which phases match all joint rules.
        phase_enum = PhaseType.get_phase_enum(session_data.get_exercise_type())
        candidates: list[str] = []

        for phase in phase_enum:
            # Ignoring the NONE type.
            if phase.name == "NONE": continue

            # Adding candidate if rules match.
            if self._phase_matches_rules(phase.name, rules, last_valid_joints):
                candidates.append(phase.name)

        # Resolve final selected phase.
        return self._select_phase_from_candidates(candidates, session_data)
    
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
        # Retrieve exercise configuration.
        exercise_config = self._get_exercise_config(session_data)
        if isinstance(exercise_config, ErrorCode): return exercise_config

        # Extract initial phase name.
        initial_phase_name:str = exercise_config.get(PhaseDictKey.INITIAL_PHASE)
        if not initial_phase_name:
            ErrorHandler.handle(
                error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                origin=inspect.currentframe(),
                extra_info={"Missing initial_phase for exercise": session_data.get_exercise_type().value}
            )
            return ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR

        # Extract phase rules.
        rules:Dict[str, Any] = exercise_config.get(PhaseDictKey.RULES)
        if rules is None or initial_phase_name not in rules:
            ErrorHandler.handle(
                error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                origin=inspect.currentframe(),
                extra_info={"Missing rules for initial phase": initial_phase_name}
            )
            return ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR

        # Validate joints against initial phase rules.
        is_match:bool = self._phase_matches_rules(
            phase_type=PhaseType.get_phase_enum(session_data.get_exercise_type())[initial_phase_name],
            rules=rules,
            joints=joints
        )

        return is_match
        
    #####################################################################
    ############################## HELPERS ##############################
    #####################################################################
    
    ###########################
    ### GET EXERCISE CONFIG ###
    ###########################
    def _get_exercise_config(self, session_data:SessionData) -> Dict[str, Any] | ErrorCode:
        """
        ### Brief:
        The `_get_exercise_config` method retrieves the exercise-specific configuration.
        
        ### Arguments:
        - `session_data` (SessionData): The session data containing relevant information.

        ### Returns:
        - `Dict[str, Any]` containing the exercise configuration.
        - `ErrorCode` in case of an error.
        """
        try:
            exercise_type:ExerciseType = session_data.get_exercise_type()
            exercise_thresholds:Dict[str, Any] = self.thresholds.get(exercise_type.value, None)
            # If the threshols configuration file does not contain the exercise type.
            if exercise_thresholds is None:
                ErrorHandler.handle(
                    error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={"Missing exercise config": exercise_type.value}
                )
                return ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR
            return exercise_thresholds
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.INTERNAL_SERVER_ERROR,
                origin=inspect.currentframe(),
                extra_info={"Exception": str(e)}
            )
            return ErrorCode.INTERNAL_SERVER_ERROR
        
    ###########################
    ### PHASE MATCHES RULES ###
    ###########################
    def _phase_matches_rules(self, phase_type:PhaseType, rules:Dict[str, Any], joints:Dict[str, float]) -> bool:
        """
        ### Brief:
        The `_phase_matches_rules` method checks if the given joint angles match
        the rules defined for a specific phase.

        ### Arguments:
        - `phase_type` (PhaseType): The phase type to check.
        - `rules` (Dict[str, Any]): The rules defining joint angle limits for phases.
        - `joints` (Dict[str, float]): The current joint angles.

        ### Returns:
        - `True` if the joint angles match the phase rules.
        - `False` otherwise.
        """
        phase_rules = rules.get(phase_type.name, None)
        if phase_rules is None:
            return False

        for joint_name, joint_range in phase_rules.items():
            if joint_name not in joints:
                # Missing joint: cannot match this phase.
                return False

            angle = joints[joint_name]
            min_allowed = joint_range.get(PhaseDictKey.MIN)
            max_allowed = joint_range.get(PhaseDictKey.MAX)

            if angle < min_allowed or angle > max_allowed:
                return False

        return True
    
    ####################################
    ### SELECT PHASE FROM CANDIDATES ###
    ####################################
    ####################################
    def _select_phase_from_candidates(self, candidates:List[str], session_data:SessionData) -> PhaseType | ErrorCode:
        """
        ### Brief:
        The `_select_phase_from_candidates` method selects the most appropriate phase
        from a list of candidate phases based on defined rules.

        ### Arguments:
        - `candidates` (List[str]): The list of candidate phase names.
        - `session_data` (SessionData): The session data containing relevant information.

        ### Returns:
        - `PhaseType` representing the selected phase.
        - `ErrorCode` in case of an error.
        """

        # No candidates at all, cannot determine phase.
        if len(candidates) == 0: return ErrorCode.PHASE_UNDETERMINED_IN_FRAME

        # Get phase enum for this exercise.
        phase_enum:PhaseType = PhaseType.get_phase_enum(session_data.get_exercise_type())

        ### Option 1: CANDIDATES LENGTH IS ONE (TRIVIAL CASE)
        # If exactly one candidate, this is the trivial case and we return it.
        if len(candidates) == 1: return phase_enum[candidates[0]]

        ### Option 2: MULTIPLE CANDIDATES (NEED RESOLUTION)
        # Retrieve last known phase from history.
        last_phase:PhaseType | None = session_data.get_history().get_phase_state()

        # If the previous phase is still valid: stay in the same phase.
        if last_phase is not None and last_phase.name in candidates:
            return last_phase

        # Prefer the next phase in the configured transition order.
        exercise_configuration:Dict[str, Any] | ErrorCode = self._get_exercise_config(session_data)
        if isinstance(exercise_configuration, ErrorCode): return exercise_configuration

        # Get transition order.
        transition_order:List[str] = exercise_configuration.get(PhaseDictKey.TRANSITION_ORDER, [])
        if not transition_order: return ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR

        # Look for the next expected phase after the last known phase.
        if last_phase is not None:
            try:
                # Find index of last phase in transition order.
                idx = transition_order.index(last_phase.name)
                # Get next expected phase.
                next_expected = transition_order[(idx + 1) % len(transition_order)]
                # If next expected phase is a candidate, return it.
                if next_expected in candidates:
                    return phase_enum[next_expected]
            except ValueError:
                # If last_phase not found in transition order, ignore.
                pass
        
        # Option 3: RECOVER FROM LOST TRACKING
        for phase_name in transition_order:
            if phase_name in candidates:
                return phase_enum[phase_name]

        # Should never happen if config is valid, but safe guard
        return ErrorCode.PHASE_UNDETERMINED_IN_FRAME

    ###########################################################################
    ############################## CONFIGURATION ##############################
    ###########################################################################

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