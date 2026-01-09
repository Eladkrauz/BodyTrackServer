####################################################################
################# BODY TRACK // SERVER // PIPELINE #################
####################################################################
###################### CLASS: PhaseDetector ########################
####################################################################

###############
### IMPORTS ###
###############
from typing import Dict, Any, List, Set
import inspect

from Utilities.Error.ErrorCode    import ErrorCode
from Utilities.Error.ErrorHandler import ErrorHandler
from Utilities.Logger             import Logger

from Data.Session.ExerciseType    import ExerciseType
from Data.Session.SessionData     import SessionData
from Data.Phase.PhaseType         import PhaseType
from Data.Phase.PhaseDictKey      import PhaseDictKey
from Data.Joints.JointAngle       import JointAngle, Joint
from Data.History.HistoryDictKey  import HistoryDictKey
from Data.History.HistoryData     import HistoryData
from Data.Pose.PositionSide       import PositionSide

###################
### RULES ALIAS ###
###################
Rules = Dict[str, Dict[str, Any]]

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
            current_phase_state:PhaseType.Squat | PhaseType.BicepsCurl = history.get_phase_state()
            session_data.get_last_frame_trace().add_event(
                stage="PhaseDetector",
                success=True,
                result_type="No valid frame data. Keeping last known phase.",
                result={ "Phase": current_phase_state.name } if current_phase_state is not None else { "Phase": None }
            )
            return current_phase_state

        # Load configuration for this exercise.
        exercise_configuration:Dict[str, Any] = self._get_exercise_config(session_data)
        if isinstance(exercise_configuration, ErrorCode): return exercise_configuration

        # Get the rules of the exercise, from the configuration.
        rules:Rules = exercise_configuration.get(PhaseDictKey.RULES, None)
        if rules is None:
            ErrorHandler.handle(
                error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                origin=inspect.currentframe(),
                extra_info={ "Missing": "Rules" }
            )
            return ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR
        
        # Filter rules based on position side.
        rules:Rules = self._filter_rules(
            rules=rules,
            session_data=session_data,
            position_side=session_data.get_history().get_position_side()
        )

        # Retrieve the latest joints from history.
        last_valid_frame:Dict[str, Any] = session_data.get_history().get_last_valid_frame()
        last_valid_joints:Dict[str, Any] = last_valid_frame[HistoryDictKey.Frame.JOINTS]
        if last_valid_joints is None or len(last_valid_joints) == 0:
            return ErrorCode.NO_VALID_FRAME_DATA_IN_SESSION

        # Check which phases match all joint rules.
        phase_enum:PhaseType.Squat | PhaseType.BicepsCurl \
              = PhaseType.get_phase_enum(session_data.get_exercise_type())
        candidates: list[str] = []

        for phase in phase_enum:
            # Ignoring the NONE type.
            if PhaseType.is_none(phase): continue

            # Adding candidate if rules match.
            if self._phase_matches_rules(phase, rules, last_valid_joints):
                candidates.append(phase.name)

        print(f"PhaseDetector: Candidates: {candidates}")
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
        
        # Filter rules based on position side.
        rules:Rules = self._filter_rules(
            rules=rules,
            session_data=session_data,
            position_side=session_data.get_history().get_position_side()
        )

        # Validate joints against initial phase rules.
        is_match:bool = self._phase_matches_rules(
            phase_type=PhaseType.get_phase_enum(session_data.get_exercise_type())[initial_phase_name],
            rules=rules,
            joints=joints
        )

        Logger.debug(f"Initial phase '{initial_phase_name}' match status: {is_match}")
        return is_match
        
    #####################################################################
    ############################## HELPERS ##############################
    #####################################################################

    #######################
    ### IS MOTION SMALL ###
    #######################
    def _is_motion_small(self, history:HistoryData, joints:Dict[str, float]) -> bool:
        """
        ### Brief:
        The `_is_motion_small` method checks if the motion between the last valid frame
        and the current joints is within a small threshold.

        ### Arguments:
        - `history` (HistoryData): The history data containing past frames.
        - `joints` (Dict[str, float]): The current joint angles.

        ### Returns:
        - `True` if the motion is small.
        - `False` otherwise.
        """
        last_frame = history.get_last_valid_frame()
        if not last_frame: return False

        prev_joints = last_frame.get(HistoryDictKey.Frame.JOINTS, {})
        if not prev_joints: return False

        for joint, value in joints.items():
            prev_value = prev_joints.get(joint)
            if prev_value is None:
                continue
            if abs(value - prev_value) > self.phase_low_motion_threshold:
                return False

        return True

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
            Logger.error(f"Phase rules not found for phase '{phase_type.name}'.")
            return False

        for joint_name, joint_range in phase_rules.items():
            if joint_name not in joints:
                # Missing joint: cannot match this phase.
                Logger.error(f"Phase '{phase_type.name}': Missing joint '{joint_name}' in provided joints.")
                return False

            angle = joints[joint_name]
            min_allowed = joint_range.get(PhaseDictKey.MIN)
            max_allowed = joint_range.get(PhaseDictKey.MAX)

            if angle < min_allowed or angle > max_allowed:
                return False

        return True
    
    ####################
    ### FILTER RULES ###
    ####################
    def _filter_rules(self, rules:Rules, session_data:SessionData, position_side:PositionSide) -> Rules:
        """
        ### Brief:
        The `_filter_rules` method filters the joint angle rules based on the
        position side (front, left, right) of the user.

        ### Arguments:
        - `rules` (Rules): The original joint angle rules.
        - `session_data` (SessionData): The session data containing relevant information.
        - `position_side` (PositionSide): The position side of the user.

        ### Returns:
        - `Rules`: The filtered joint angle rules.
        """
        joint_cls:JointAngle.Squat | JointAngle.BicepsCurl \
              = JointAngle.exercise_type_to_joint_type(session_data.get_exercise_type())

        # Unknown side, do nit restrict rules.
        if position_side.is_unkwown(): return rules

        # Get allowed joints for the given position side.
        allowed:Set[str] = { joint.name for joint in JointAngle.get_all_joints(
            cls_name=joint_cls,
            position_side=position_side,
        )}

        filtered_rules:Rules = {}

        # Filter rules to only include allowed joints.
        for phase_name, phase_rules in rules.items():
            filtered_rules[phase_name] = {
                joint: limits
                for joint, limits in phase_rules.items()
                if joint in allowed
            }

        return filtered_rules

    ####################################
    ### SELECT PHASE FROM CANDIDATES ###
    ####################################
    ####################################
    def _select_phase_from_candidates(self, candidates:List[str], session_data:SessionData) -> PhaseType | ErrorCode:
        """
        ### Brief:
        The `_select_phase_from_candidates` selects the best phase out of a list of
        candidate phases that matched thresholds for this frame.

        ### Arguments:
        - `candidates` (List[str]): A `list` of phase names (strings) whose rule blocks
                                    matched the current joints.
        - `session_data` (SessionData): provides exercise type + history, including last selected phase.

        ### Returns:
        - The selected `PhaseType` enum element for this frame, or `ErrorCode` on configuration failures.

        ### Idea:
        This method implements a *robust real-time phase selection* strategy:
        1) Never “drop” to an undefined phase if we can keep continuity.
        2) Prefer stable behavior (hysteresis) over flickering between phases.
        3) Prefer the next expected phase according to the configured transition order.
        4) Support special “low motion” phases (like HOLD) by gating them until motion is actually small.
        """
        ##############
        ### CASE 1 ### - No candidates matched the rules for this frame.
        ##############
        # In real-time systems, “no match” is usually caused by noise:
        # - skeleton jitter
        # - borderline angles around thresholds
        # - one joint temporarily failing
        #
        # Returning "PHASE_UNDETERMINED" in this case is harmful because it blocks feedback.
        # Therefore: prefer continuity (last phase) or a safe initial default.
        last_phase:PhaseType = session_data.get_history().get_phase_state()
        if len(candidates) == 0:
            # If we have a last known phase, keep it (hysteresis / continuity).
            if last_phase is not None:
                session_data.get_last_frame_trace().add_event(
                    stage="PhaseDetector",
                    success=True,
                    result_type="Case 1: No candidates. Keeping last phase.",
                    result={ "Phase": last_phase.name }
                )
                return last_phase

            # If we have no last phase (for example - start of session), fallback to initial phase from config.
            exercise_configuration:Dict[str, Any] = self._get_exercise_config(session_data)
            if isinstance(exercise_configuration, ErrorCode):
                # If config failed, we cannot decide.
                return ErrorCode.PHASE_UNDETERMINED_IN_FRAME

            initial:str = exercise_configuration.get(PhaseDictKey.INITIAL_PHASE)
            phase_enum:PhaseType = PhaseType.get_phase_enum(session_data.get_exercise_type())

            # Config validation should ensure 'initial' exists, but we keep this safe-guard anyway.
            if initial in phase_enum:
                session_data.get_last_frame_trace().add_event(
                    stage="PhaseDetector",
                    success=True,
                    result_type="Case 1: No candidates. Using initial phase from config.",
                    result={ "Phase": initial }
                )
                return phase_enum[initial]

            # If we cannot determine a safe phase, return undetermined.
            return ErrorCode.PHASE_UNDETERMINED_IN_FRAME
        
        # Load config for transition order and low-motion behavior.
        exercise_configuration:Dict[str, Any] | ErrorCode = self._get_exercise_config(session_data)
        # If config retrieval failed, we cannot decide.
        if isinstance(exercise_configuration, ErrorCode): return exercise_configuration

        # Transition order defines the natural cycle of phases for this exercise.
        transition_order:List[str] = exercise_configuration.get(PhaseDictKey.TRANSITION_ORDER, [])
        # If transition order is missing, we cannot decide.
        if not transition_order: return ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR

        ##############
        ### CASE 2 ### - Exactly one candidate, a trivial selection.
        ##############
        # At least one candidate exists.
        # Load phase enum for this exercise once so we can return PhaseType elements.
        phase_enum:PhaseType = PhaseType.get_phase_enum(session_data.get_exercise_type())
        idx:int = transition_order.index(last_phase.name)
        next_expected:PhaseType = phase_enum[transition_order[(idx + 1) % len(transition_order)]]

        # If only one phase matches rules, that is the phase.
        if len(candidates) == 1:
            # Hysteresis: if last phase is different, but still valid, keep it for stability.
            candidate:PhaseType = phase_enum[candidates[0]]

            if candidate != last_phase and last_phase is not None and candidate != next_expected:
                session_data.get_last_frame_trace().add_event(
                    stage="PhaseDetector",
                    success=True,
                    result_type=f"Case 2: One candidate ({candidates[0]}) but keeping last phase for hysteresis.",
                    result={ "Phase": last_phase.name }
                )
                return last_phase
            else:
                session_data.get_last_frame_trace().add_event(
                    stage="PhaseDetector",
                    success=True,
                    result_type="Case 2: One candidate selected.",
                    result={ "Phase": candidate.name }
                )
                return candidate

        ##############
        ### CASE 3 ### - Multiple candidates, we need resolution logic.
        ##############
        # Common cause: overlapping thresholds.
        last_phase:PhaseType | None = session_data.get_history().get_phase_state()

        # If the last phase is still a valid candidate this frame, keep it.
        # This is standard hysteresis to prevent flickering when multiple phases match.
        if last_phase is not None and last_phase.name in candidates:
            session_data.get_last_frame_trace().add_event(
                stage="PhaseDetector",
                success=True,
                result_type="Case 3: Multiple candidates but keeping last phase for hysteresis.",
                result={ "Phase": last_phase.name, "Candidates": candidates }
            )
            return last_phase

        # Low-motion phases are phases we only want to allow when motion is actually small.
        # Example: HOLD at the top of a curl or bottom of a squat.
        # IMPORTANT: This list may legitimately be empty for some exercises.
        low_motion_phases:List[str] = exercise_configuration.get(PhaseDictKey.LOW_MOTION_PHASES, [])
        low_motion_streak:int = session_data.get_history().get_low_motion_streak()

        # Gate low-motion phases by requiring a streak of “low motion” frames.
        is_low_motion_ready:bool = low_motion_streak >= self.phase_low_motion_threshold

        #######################
        ### PRIORITY RULE 1 ### - Prefer the "next expected" phase in transition order.
        #######################
        # If we know the last phase, the most natural choice is the next phase in the configured cycle.
        # This enforces correct phase progression rather than allowing random jumps.
        if last_phase is not None:
            try:
                idx:int = transition_order.index(last_phase.name)
                next_expected:str = transition_order[(idx + 1) % len(transition_order)]

                # If the next expected phase is “low motion” but we are not in low motion, we do NOT go there.
                # Instead, keep last phase to avoid falsely entering HOLD (or similar).
                # Note: last_phase may not be in candidates here, but we accept hysteresis for stability.
                if (next_expected in low_motion_phases) and (not is_low_motion_ready):
                    session_data.get_last_frame_trace().add_event(
                        stage="PhaseDetector",
                        success=True,
                        result_type="Priority Rule 1: Next expected phase is low-motion but not ready. Keeping last phase.",
                        result={ "Phase": last_phase.name, "Candidates": candidates }
                    )
                    return last_phase

                # If the next expected phase is one of the candidates, choose it.
                if next_expected in candidates:
                    session_data.get_last_frame_trace().add_event(
                        stage="PhaseDetector",
                        success=True,
                        result_type="Priority Rule 1: Selecting next expected phase.",
                        result={ "Phase": next_expected, "Candidates": candidates }
                    )
                    return phase_enum[next_expected]

            except ValueError:
                # If last_phase is not found in transition_order (should not happen if config is consistent),
                # we simply skip this “next expected” logic and move to recovery logic.
                pass
        
        #######################
        ### PRIORITY RULE 2 ### - Recovery from lost tracking.
        #######################
        # If the "next expected" phase isn't a candidate (or we can't use it),
        # choose the first candidate that appears in a sensible order.
        # We bias the search forward from last_phase to preserve directionality.
        if last_phase is not None:
            try:
                start_idx:int = transition_order.index(last_phase.name)
                ordered:list[str] = transition_order[start_idx + 1:] + transition_order[:start_idx + 1]
            except ValueError:
                # If last_phase isn't in transition order, fall back to the transition order as-is.
                ordered = transition_order
        else:
            ordered:list[str] = transition_order

        for phase_name in ordered:
            if phase_name in candidates:
                # If this candidate is a low-motion phase but we are not yet “low-motion ready”, skip it.
                if (phase_name in low_motion_phases) and (not is_low_motion_ready):
                    continue
                
                session_data.get_last_frame_trace().add_event(
                    stage="PhaseDetector",
                    success=True,
                    result_type="Priority Rule 2: Selecting first sensible candidate phase.",
                    result={ "Phase": phase_name, "Candidates": candidates }
                )
                return phase_enum[phase_name]

        # If we got here, candidates exist but none were selectable under gating rules.
        # This can happen if candidates only include low-motion phases but motion isn't low yet.
        # In that case, prefer continuity.
        if last_phase is not None:
            session_data.get_last_frame_trace().add_event(
                stage="PhaseDetector",
                success=True,
                result_type="No selectable candidates under gating rules. Keeping last phase.",
                result={ "Phase": last_phase.name, "Candidates": candidates }
            )
            return last_phase

        # Otherwise, safe-guard.
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
        from Utilities.Config.ConfigLoader import ConfigLoader
        from Utilities.Config.ConfigParameters import ConfigParameters

        # Load phase low motion threshold.
        self.phase_low_motion_threshold:int = ConfigLoader.get(
            key=[
                ConfigParameters.Major.PHASE,
                ConfigParameters.Minor.PHASE_LOW_MOTION_THRESHOLD
            ]
        )

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

        Logger.info("Retrieved configurations successfully")
        
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
            low_motion = config[PhaseDictKey.LOW_MOTION_PHASES]
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
                
                # Get allowed joint names for this exercise type.
                joint_cls:JointAngle = JointAngle.exercise_type_to_joint_type(exercise_type)
                allowed_joint_names:List[str] = [
                    joint.name for joint in
                    JointAngle.get_all_joints(
                        cls_name=joint_cls,
                        position_side=PositionSide.FRONT
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

            # Initial_phase must be valid.
            if initial not in phase_names:
                ErrorHandler.handle(
                    error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={ f"Invalid initial_phase for exercise {exercise_name}": initial }
                ); return False
            
            # Low_motion phases must be list of valid phases.
            if not isinstance(low_motion, list):
                ErrorHandler.handle(
                    error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={ f"Low motion phases is not a list for exercise {exercise_name}": low_motion }
                ); return False
            for phase in low_motion:
                if phase not in phase_names:
                    ErrorHandler.handle(
                        error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                        origin=inspect.currentframe(),
                        extra_info={ f"Invalid phase in low_motion_phases for exercise {exercise_name}": phase }
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