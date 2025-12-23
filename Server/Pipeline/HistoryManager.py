############################################################
############ BODY TRACK // SERVER // PIPELINE ##############
############################################################
################# CLASS: HistoryManager ####################
############################################################

###############
### IMPORTS ###
###############
from __future__ import annotations
import inspect
from datetime import datetime
from typing import Dict, TYPE_CHECKING, Any, Set, List
from copy import deepcopy

from Server.Data.Pose.PoseQuality          import PoseQuality
from Server.Data.History.HistoryDictKey    import HistoryDictKey
from Server.Data.History.HistoryData       import HistoryData
from Server.Data.Error.DetectedErrorCode   import DetectedErrorCode
from Server.Data.Session.ExerciseType      import ExerciseType
from Server.Data.Phase.PhaseType           import PhaseType
from Server.Data.Pose.PoseLandmarks        import PoseLandmarksArray
from Server.Data.Pose.PositionSide         import PositionSide
from Server.Utilities.Logger               import Logger
from Server.Data.Response.FeedbackResponse import FeedbackCode

if TYPE_CHECKING:
    from Server.Data.Pose.PoseQuality  import PoseQuality
    from Server.Data.Joints.JointAngle import JointAngle

#############################
### HISTORY MANAGER CLASS ###
#############################
class HistoryManager:
    """
    ### Description:
    The `HistoryManager` is the active service responsible for mutating, updating and maintaining
    the temporal state of an exercise session. It performs all operations related to history evolution,
    while delegating pure data storage and read-access to `HistoryData`.
    """
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self):
        """
        ### Brief:
        The `__init__` method initializes the `HistoryManager` instance.
        """
        self.retrieve_configurations()
        Logger.info("Initialized successfully.")

    ###############################################################################################
    ############################## RECORD NEW VALID OR INVALID FRAME ##############################
    ###############################################################################################

    ##########################
    ### RECORD VALID FRAME ###
    ##########################
    def record_valid_frame(
            self,
            history_data:HistoryData,
            frame_id:int,
            landmarks:PoseLandmarksArray,
            joints:Dict[str, float]
        ) -> None:
        """
        ### Brief:
        The `record_valid_frame` method adds a new valid (OK) frame record to history.

        This method is called only after:
            1. `PoseAnalyzer` produced landmarks
            2. `PoseQualityManager` returned `PoseQuality.OK`
            3. `JointAnalyzer` successfully computed joints

        ### Argumetns:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        - `frame_id` (int): The frame number.
        - `landmarks` (PoseLandmarksArray): The landmarks from `PoseAnalyzer`.
        - `joints` (Dict[str, Any]): The angles dictionary from `JointAnalyzer`.

        ### Use:
        - Used by the `SessionManager` to record an `OK` frame after calculating its joints.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)
        try:
            # New frame to store.
            new_frame = {
                HistoryDictKey.Frame.FRAME_ID:  frame_id,
                HistoryDictKey.Frame.TIMESTAMP: datetime.now(),
                HistoryDictKey.Frame.LANDMARKS: deepcopy(landmarks),
                HistoryDictKey.Frame.JOINTS:    deepcopy(joints),
                HistoryDictKey.Frame.ERRORS:    []
            }

            # Inserting and handling rolling window of the frames list.
            frames_list:List = history_raw_dict[HistoryDictKey.FRAMES]
            frames_list.append(new_frame)
            self._pop_frame_if_needed(history_data)

            # If the current frame is valid but not yet stable (lower than threshold),
            # keep info about the previous bad frames.
            if not self._is_valid_frame_in_threshold(history_data): return

            # At this point - the frame is valid and stable.
            # Calculating deltas.
            self._update_low_motion_streak(
                history_data=history_data,
                joints=new_frame[HistoryDictKey.Frame.JOINTS]
            )

            # Updating last valid frame.
            history_raw_dict[HistoryDictKey.LAST_VALID_FRAME] = new_frame

            # Resetting counters.
            self._reset_bad_frame_counters(history_data)

        except Exception as e:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_INTERNAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={ "Exception": type(e), "Reason": str(e) }
            )

    #######################
    ### ADD FRAME ERROR ###
    #######################
    def add_frame_error(self, history_data:HistoryData, error_to_add:DetectedErrorCode, frame_id:int) -> None:
        """
        ### Brief:
        The `add_frame_error` method adds an error to a valid frame.

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        - `error_to_add` (DetectedErrorCode): The error to be added.
        - `frame_id` (int): The frame id.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)
        current_amount_of_frames:int = len(history_raw_dict[HistoryDictKey.FRAMES])
        error_to_add:str = error_to_add.name

        # Searching for the frame in the stored frames list.
        for i in range(current_amount_of_frames - 1, -1, -1):
            iterated_frame_id:int = history_raw_dict[HistoryDictKey.FRAMES][i][HistoryDictKey.Frame.FRAME_ID]
            
            # If found - adding the error.
            if iterated_frame_id == frame_id:
                frame_errors:List[str] = history_raw_dict[HistoryDictKey.FRAMES][i][HistoryDictKey.Frame.ERRORS]
                frame_errors.append(error_to_add)

                # Updating counters.
                error_counters:Dict[str, int] = history_raw_dict[HistoryDictKey.ERROR_COUNTERS]
                if error_counters.get(error_to_add, None) is None: error_counters[error_to_add] = 1
                else:                                              error_counters[error_to_add] += 1

                # Updating streaks.
                error_streaks:Dict[str, int] = history_raw_dict[HistoryDictKey.ERROR_STREAKS]
                if error_streaks.get(error_to_add, None) is None: streak:int = 1
                else:                                             streak:int = error_streaks.pop(error_to_add) + 1

                # Reset other streaks.
                for error in error_streaks: error_streaks[error] = 0
                error_streaks[error_to_add] = streak
                return
        
        # If arrived here - did not find the frame in the list (probably it is too old).
        from Server.Utilities.Error.ErrorHandler import ErrorHandler
        from Server.Utilities.Error.ErrorCode import ErrorCode
        ErrorHandler.handle(
            error=ErrorCode.CANT_FIND_FRAME_IN_FRAMES_WINDOW,
            origin=inspect.currentframe()
            )

    ############################
    ### RECORD INVALID FRAME ###
    ############################
    def record_invalid_frame(self, history_data:HistoryData, frame_id:int, invalid_reason:PoseQuality) -> None:
        """
        ### Brief:
        The `record_invalid_frame` method adds a new invalid (not `OK`) frame record to history.

        This method is called only after:
            1. `PoseAnalyzer` produced landmarks
            2. `PoseQualityManager` returned something else but `PoseQuality.OK`

        ### Argumetns:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        - `frame_id` (int): The frame number
        - `invalid_reason` (PoseQuality): The reason why the frame is invalid

        ### Use:
        - Used by the `SessionManager` to record a not `OK` frame after `PoseQualityManager` determined it.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)
        try:
            entry = {
                HistoryDictKey.BadFrame.FRAME_ID:  frame_id,
                HistoryDictKey.BadFrame.TIMESTAMP: datetime.now(),
                HistoryDictKey.BadFrame.REASON:    invalid_reason.value
            }
            bad_frames_log:List[Dict] = history_raw_dict[HistoryDictKey.BAD_FRAMES_LOG]
            bad_frames_log.append(entry)
            self._pop_bad_frame_if_needed(history_data)

            # Increment total counters for this reason.
            history_raw_dict[HistoryDictKey.BAD_FRAME_COUNTERS][invalid_reason.name] += 1
            # Increase total invalid frames count.
            history_raw_dict[HistoryDictKey.FRAMES_SINCE_LAST_VALID] += 1
            # Increment bad frame streak.
            for pose_quality in history_raw_dict[HistoryDictKey.BAD_FRAME_STREAKS]:
                if pose_quality == invalid_reason.name:
                    history_raw_dict[HistoryDictKey.BAD_FRAME_STREAKS][pose_quality] += 1
                else:
                    history_raw_dict[HistoryDictKey.BAD_FRAME_STREAKS][pose_quality] = 0

            # Break the OK streak.
            self.reset_consecutive_ok_streak(history_data)

            # If too many bad frames - system is unstable.
            if history_raw_dict[HistoryDictKey.BAD_FRAME_STREAKS][invalid_reason.name] >= self.bad_stability_limit:
                    Logger.warning(f"Camera became unstable due to too many '{invalid_reason.name}' frames.")
                    history_raw_dict[HistoryDictKey.IS_CAMERA_STABLE] = False

        except Exception as e:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_INTERNAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={ "Exception": type(e), "Reason": str(e) }
            )

    #########################################################################
    ############################## PHASE STATE ##############################
    #########################################################################

    #########################
    ### SET INITIAL PHASE ###
    #########################
    def set_initial_phase(self, history_data:HistoryData, exercise_type:ExerciseType) -> None:
        """
        ### Brief:
        The `set_initial_phase` method sets the initial phase for the exercise session.

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        - `exercise_type` (ExerciseType): The type of exercise being performed.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        initial_phase:PhaseType = self.initial_phase_per_exercise.get(exercise_type, None)
        if initial_phase is None:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_INTERNAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={ "Exercise Type": exercise_type }
            )
            return
        
        history_raw_dict[HistoryDictKey.PHASE_STATE] = initial_phase
        
    ###############################
    ### RECOED PHASE TRANSITION ###
    ###############################
    def record_phase_transition(
            self,
            history_data:HistoryData,
            exercise_type:ExerciseType,
            new_phase:PhaseType,
            frame_id:int,
            joints:Dict[str, float]
        ) -> None:
        """
        ### Brief:
        The `record_phase_transition` method records a biomechanical phase transition event.
        This is triggered only when `PhaseDetector` identifies an actual movement state transition.

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        - `new_phase` (PhaseType): The new phase.
        - `frame_id` (int): The frame where the transition happened.
        - `joints` (dict[str, float]): Snapshot of key joint angles at transition moment.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        # First: checking if an actual transition happened.
        old_phase = history_data.get_phase_state()

        # If this is the first phase being recorded - just store it.
        # No transition to handle.
        if old_phase is None:
            history_raw_dict[HistoryDictKey.PHASE_STATE] = new_phase
            return
        
        # If the new phase is the same as the old one - no transition.
        if new_phase is None or new_phase == old_phase: return
        
        # If arrived here - an actual transition happened, so we handle it.

        #######################################
        ### HANDLING REPETITION PROGRESSION ###
        #######################################
        transition_order:List[str] = self.transition_order_per_exercise.get(exercise_type, [])
        initial_phase:PhaseType    = self.initial_phase_per_exercise.get(exercise_type, None)
        current_index:int          = history_data.get_current_transition_index()

        if not transition_order or initial_phase is None or current_index is None:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_INTERNAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exercise Type":       exercise_type,
                    "Transition Order":    transition_order,
                    "Initial Phase":       initial_phase,
                    "Current Transition Index": current_index
                }
            )
            return

        # Determining next expected phase in the transition order.
        if current_index + 1 < len(transition_order): next_phase:PhaseType = transition_order[current_index + 1]
        else:                                         next_phase:PhaseType = None
        
        print("old_phase >>>", old_phase)
        print("new_phase >>>", new_phase)
        print("next_phase >>>", next_phase)
        print("initial_phase >>>", initial_phase)
        print("transition_order >>>", transition_order)
        print("current_index >>>", current_index)
        ##############
        ### Case 1 ### - Correct progression in transition order.
        ##############
        if new_phase == next_phase and new_phase != initial_phase:
            # Starting a new rep: leaving initial phase.
            if current_index == 0:
                Logger.info("#\n#\n#\n#\n#\nStarting a new repetition.\n#\n#\n#\n#\n#")
                self.start_a_new_rep(history_data)
            
            # Progressing in the transition order.
            history_raw_dict[HistoryDictKey.CURRENT_TRANSITION_INDEX] += 1

        ##############
        ### Case 2 ### - Cycle completed - end rep.
        ##############
        elif new_phase == initial_phase and current_index != 0:
            Logger.info("#\n#\n#\n#\n#\nEnding the repetition.\n#\n#\n#\n#\n#")
            self.end_current_rep(history_data)
            history_raw_dict[HistoryDictKey.CURRENT_TRANSITION_INDEX] = 0

        ##############
        ### Case 3 ### - Invalid transition - reset rep tracking.
        ##############
        else:
            history_raw_dict[HistoryDictKey.CURRENT_TRANSITION_INDEX] = 0

        ########################################################
        ### HANDLING PHASE DURATION AND TRANSITION RECORDING ###
        ########################################################
        now = datetime.now()

        # If we have a previous transition (it is not the first now) - compute duration.
        transitions:List = history_raw_dict[HistoryDictKey.PHASE_TRANSITIONS]
        if transitions:
            last = transitions[-1]
            start_time:datetime = last[HistoryDictKey.PhaseTransition.TIMESTAMP]
            duration = (now - start_time).total_seconds()

            # Store finished phase duration entry.
            phase_durations:List = history_raw_dict[HistoryDictKey.PHASE_DURATIONS]
            phase_durations.append({
                HistoryDictKey.PhaseDuration.PHASE:       old_phase,
                HistoryDictKey.PhaseDuration.START_TIME:  start_time,
                HistoryDictKey.PhaseDuration.END_TIME:    now,
                HistoryDictKey.PhaseDuration.DURATION:    duration,
                HistoryDictKey.PhaseDuration.FRAME_START: last[HistoryDictKey.PhaseTransition.FRAME_ID],
                HistoryDictKey.PhaseDuration.FRAME_END:   frame_id
            })

        # Store the actual transition.
        new_transition = {
            HistoryDictKey.PhaseTransition.PHASE_FROM: old_phase,
            HistoryDictKey.PhaseTransition.PHASE_TO:   new_phase,
            HistoryDictKey.PhaseTransition.TIMESTAMP:  now,
            HistoryDictKey.PhaseTransition.FRAME_ID:   frame_id,
            HistoryDictKey.PhaseTransition.JOINTS:     joints
        }

        transitions.append(new_transition)

        # Update current phase type and start time.
        history_raw_dict[HistoryDictKey.PHASE_STATE] = new_phase

    def set_position_side(self, history_data:HistoryData, position_side:PositionSide) -> None:
        """
        ### Brief:
        The `set_position_side` method sets the user's position side in history.

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        - `position_side` (PositionSide): The user's position side.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)
        history_raw_dict[HistoryDictKey.POSITION_SIDE] = position_side

    #########################################################################
    ############################## REPETITIONS ##############################
    #########################################################################

    #######################
    ### START A NEW REP ###
    #######################
    def start_a_new_rep(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `start_a_new_rep` method starts a new repetition and stores it.

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        if history_raw_dict[HistoryDictKey.CURRENT_REP] is not None:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(error=ErrorCode.TRIED_TO_START_REP_WHILE_HAVE_ONE, origin=inspect.currentframe())
        else:
            new_rep = {
                HistoryDictKey.CurrentRep.START_TIME: datetime.now(),
                HistoryDictKey.CurrentRep.HAS_ERROR:  False,
                HistoryDictKey.CurrentRep.ERRORS:     [],
                HistoryDictKey.CurrentRep.NOTIFIED:   set()
            }

            history_raw_dict[HistoryDictKey.CURRENT_REP] = new_rep

    ################################
    ### ADD ERROR TO CURRENT REP ###
    ################################
    def add_error_to_current_rep(self, history_data:HistoryData, error_to_add:DetectedErrorCode) -> None:
        """
        ### Brief:
        The `add_error_to_current_rep` method adds a new detected error to the current repetition.

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        - `error_to_add` (DetectedErrorCode): The detected error to be added.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        if history_raw_dict[HistoryDictKey.CURRENT_REP] is None:
            Logger.warning("Tried to add error to a None current rep.")
            return
        else:
            history_raw_dict[HistoryDictKey.CURRENT_REP][HistoryDictKey.CurrentRep.HAS_ERROR] = True
            errors_set:List[str] = history_raw_dict[HistoryDictKey.CURRENT_REP][HistoryDictKey.CurrentRep.ERRORS]
            errors_set.append(error_to_add.name)

    ################################
    ### RECORD FEEDBACK NOTIFIED ###
    ################################
    def record_feedback_notified(self, history_data:HistoryData, error_notified:FeedbackCode) -> None:
        """
        ### Brief:
        The `record_feedback_notified` method records that a feedback has been notified
        for the current repetition.

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        - `error_notified` (FeedbackCode): The feedback code that was notified.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        if history_raw_dict[HistoryDictKey.CURRENT_REP] is None:
            Logger.warning("Tried to add notified feedback to a None current rep.")
            return
        else:
            notified_set:Set[str] = history_raw_dict[HistoryDictKey.CURRENT_REP][HistoryDictKey.CurrentRep.NOTIFIED]
            notified_set.add(error_notified)

    #######################
    ### END CURRENT REP ###
    #######################
    def end_current_rep(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `end_current_rep` method finishes the current repetition.

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        if history_raw_dict[HistoryDictKey.CURRENT_REP] is None:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(error=ErrorCode.TRIED_TO_END_A_NONE_REP, origin=inspect.currentframe())
        else:
            # Finishing current rep and inserting it to the completed reps list.
            current_rep:Dict[str, Any] = history_raw_dict[HistoryDictKey.CURRENT_REP]
            start_time:datetime = current_rep[HistoryDictKey.CurrentRep.START_TIME]
            end_time:datetime = datetime.now()
            completed_rep = {
                HistoryDictKey.Repetition.START_TIME: start_time,
                HistoryDictKey.Repetition.END_TIME:   end_time,
                HistoryDictKey.Repetition.DURATION:   (end_time - start_time).total_seconds(),
                HistoryDictKey.Repetition.IS_CORRECT: not current_rep[HistoryDictKey.CurrentRep.HAS_ERROR],
                HistoryDictKey.Repetition.ERRORS:     deepcopy(current_rep[HistoryDictKey.CurrentRep.ERRORS])
            }
            repetitions:List[Dict[str, Any]] = history_raw_dict[HistoryDictKey.REPETITIONS]
            repetitions.append(completed_rep)
            history_raw_dict[HistoryDictKey.REP_COUNT] += 1
            history_raw_dict[HistoryDictKey.CURRENT_REP] = None

    ########################################################################
    ############################## TIMESTAMPS ##############################
    ########################################################################

    ###########################
    ### MARK EXERCISE START ###
    ###########################
    def mark_exercise_start(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `mark_exercise_start` method sets the exercise start timestamp (only once).

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        if history_raw_dict[HistoryDictKey.EXERCISE_START_TIME] is None:
            history_raw_dict[HistoryDictKey.EXERCISE_START_TIME] = datetime.now()
        else:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(
                error=ErrorCode.EXERCISE_START_TIME_ALREADY_SET,
                origin=inspect.currentframe(),
                extra_info={ "Already Set": history_raw_dict[HistoryDictKey.EXERCISE_START_TIME] }
            )

    #########################
    ### MARK EXERCISE END ###
    #########################
    def mark_exercise_end(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `mark_exercise_start` method sets the exercise end timestamp (only once).

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        try:
            # Prevent multiple calls.
            if history_raw_dict[HistoryDictKey.EXERCISE_END_TIME] is not None:
                from Server.Utilities.Error.ErrorHandler import ErrorHandler
                from Server.Utilities.Error.ErrorCode import ErrorCode
                ErrorHandler.handle(
                    error=ErrorCode.EXERCISE_END_TIME_ALREADY_SET,
                    origin=inspect.currentframe(),
                    extra_info={ "Already Set": history_raw_dict[HistoryDictKey.EXERCISE_END_TIME] }
                )
                return

            # Mark end time and calculate total duration.
            end_timestamp = datetime.now()
            history_raw_dict[HistoryDictKey.EXERCISE_END_TIME] = end_timestamp
            exercise_start_timestamp:datetime = history_raw_dict[HistoryDictKey.EXERCISE_START_TIME]
            total_duration:float = (end_timestamp - exercise_start_timestamp).total_seconds()

            # If the session ended after being paused, add this pause duration.
            current_pause_timestamp:datetime = history_raw_dict[HistoryDictKey.PAUSE_SESSION_TIMESTAMP]
            if current_pause_timestamp is not None:
                pause_duration:float = (end_timestamp - current_pause_timestamp).total_seconds()
                history_raw_dict[HistoryDictKey.PAUSES_DURATIONS] += pause_duration
                history_raw_dict[HistoryDictKey.PAUSE_SESSION_TIMESTAMP] = None
            
            # Subtract total pause durations from final duration.
            total_duration -= history_raw_dict[HistoryDictKey.PAUSES_DURATIONS]
            history_raw_dict[HistoryDictKey.EXERCISE_FINAL_DURATION] = total_duration

            # Finalize last open phase.
            transitions:List = history_raw_dict[HistoryDictKey.PHASE_TRANSITIONS]
            durations:List   = history_raw_dict[HistoryDictKey.PHASE_DURATIONS]
            repetitions:List = history_raw_dict[HistoryDictKey.REPETITIONS]
            
            if transitions:
                last_transition = transitions[-1]
                start_time:datetime = last_transition[HistoryDictKey.PhaseTransition.TIMESTAMP]
                duration = (end_timestamp - start_time).total_seconds()

                durations.append({
                    HistoryDictKey.PhaseDuration.PHASE:       last_transition[HistoryDictKey.PhaseTransition.PHASE_TO],
                    HistoryDictKey.PhaseDuration.START_TIME:  start_time,
                    HistoryDictKey.PhaseDuration.END_TIME:    end_timestamp,
                    HistoryDictKey.PhaseDuration.DURATION:    duration,
                    HistoryDictKey.PhaseDuration.FRAME_START: last_transition[HistoryDictKey.PhaseTransition.FRAME_ID],
                    HistoryDictKey.PhaseDuration.FRAME_END:   None,  # No phase-changing frame.
                })

            # Finalize open repetition.
            current_rep:dict = history_raw_dict[HistoryDictKey.CURRENT_REP]
            if current_rep is not None:
                start_time = current_rep[HistoryDictKey.CurrentRep.START_TIME]

                completed_rep = {
                    HistoryDictKey.Repetition.START_TIME: start_time,
                    HistoryDictKey.Repetition.END_TIME:   end_timestamp,
                    HistoryDictKey.Repetition.DURATION:   (end_timestamp - start_time).total_seconds(),
                    HistoryDictKey.Repetition.IS_CORRECT: False, # Incomplete rep = not correct.
                    HistoryDictKey.Repetition.ERRORS:     deepcopy(current_rep[HistoryDictKey.CurrentRep.ERRORS])
                }
                repetitions.append(completed_rep)
                history_raw_dict[HistoryDictKey.REP_COUNT] += 1

                # Clear current rep.
                history_raw_dict[HistoryDictKey.CURRENT_REP] = None

        except Exception as e:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode

            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_INTERNAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={"Exception": type(e), "Reason": str(e)}
            )

    #####################
    ### PAUSE SESSION ###
    #####################
    def pause_session(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `pause_session` method marks the session as paused in history.

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        if history_raw_dict[HistoryDictKey.PAUSE_SESSION_TIMESTAMP] is not None:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_INTERNAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={ "Pause timestamp is already set": history_raw_dict[HistoryDictKey.PAUSE_SESSION_TIMESTAMP] }
            )
            return
        
        history_raw_dict[HistoryDictKey.PAUSE_SESSION_TIMESTAMP] = datetime.now()

    ######################
    ### RESUME SESSION ###
    ######################
    def resume_session(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `resume_session` method marks the session as resumed in history.

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        pause_timestamp:datetime = history_raw_dict[HistoryDictKey.PAUSE_SESSION_TIMESTAMP]
        if pause_timestamp is None:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_INTERNAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={ "Pause timestamp is not set": history_raw_dict[HistoryDictKey.PAUSE_SESSION_TIMESTAMP] }
            )
            return
        
        pause_duration:float = (datetime.now() - pause_timestamp).total_seconds()
        history_raw_dict[HistoryDictKey.PAUSES_DURATIONS] += pause_duration
        history_raw_dict[HistoryDictKey.PAUSE_SESSION_TIMESTAMP] = None

    ##################################################################################
    ############################## STREAKS AND COUNTERS ##############################
    ##################################################################################

    ############################
    ### SHOULD ABORT SESSION ###
    ############################
    def should_abort_session(self, history_data:HistoryData) -> bool:
        """
        ### Brief:
        The `should_abort_session` method returns whether the session should be aborted.

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.

        ### Returns:
        - `True` if should abort (current amount of frames since last valid one is too big).
        - `False` otherwise.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        return history_raw_dict[HistoryDictKey.FRAMES_SINCE_LAST_VALID] >= self.max_consecutive_invalid_before_abort
    
    #######################################
    ### INCREMENT CONSECUTIVE OK STREAK ###
    #######################################
    def increment_consecutive_ok_streak(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `increment_ok_streak` method increments the number of consecutive `OK` frames.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        history_raw_dict[HistoryDictKey.CONSECUTIVE_OK_FRAMES] += 1
    
    ###################################
    ### RESET CONSECUTIVE OK STREAK ###
    ###################################
    def reset_consecutive_ok_streak(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `reset_consecutive_ok_streak` method resets the number of consecutive `OK` frames.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        history_raw_dict[HistoryDictKey.CONSECUTIVE_OK_FRAMES] = 0
    
    ################################################
    ### INCREMENT CONSECUTIVE INIT PHASE COUNTER ###
    ################################################
    def increment_consecutive_init_phase_counter(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `increment_consecutive_init_phase_counter` method increments the number of consecutive
        correct initial phase detections.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        history_raw_dict[HistoryDictKey.INITIAL_PHASE_COUNTER] += 1
    
    ############################################
    ### RESET CONSECUTIVE INIT PHASE COUNTER ###
    ############################################
    def reset_consecutive_init_phase_counter(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `reset_consecutive_init_phase_counter` method resets the number of consecutive
        correct initial phase detections.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        history_raw_dict[HistoryDictKey.INITIAL_PHASE_COUNTER] = 0

    ############################################
    ### INCREMENT FRAMES SINCE LAST FEEDBACK ###
    ############################################
    def increment_frames_since_last_feedback(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `increment_frames_since_last_feedback` method increments the number of frames since last feedback.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        history_raw_dict[HistoryDictKey.FRAMES_SINCE_LAST_FEEDBACK] += 1

    ########################################
    ### RESET FRAMES SINCE LAST FEEDBACK ###
    ########################################
    def reset_frames_since_last_feedback(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `reset_frames_since_last_feedback` method resets the number of frames since last feedback.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        history_raw_dict[HistoryDictKey.FRAMES_SINCE_LAST_FEEDBACK] = 0

    ############################
    ### SET CAMERA IS STABLE ###
    ############################
    def set_camera_is_stable(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `set_camera_is_stable` method sets the camera stability flag to True.

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)
        history_raw_dict[HistoryDictKey.IS_CAMERA_STABLE] = True

    #####################################################################
    ############################## HELPERS ##############################
    #####################################################################

    ###################################
    ### IS VALID FRAME IN THRESHOLD ###
    ###################################
    def _is_valid_frame_in_threshold(self, history_data:HistoryData) -> bool:
        """
        ### Brief:
        The `_is_valid_frame_in_threshold` method increments the consecutive ok frames
        counter and returns whether the current consecutive amount has reached the
        minimum threshold, as stored (from the configuration file) in `self.recovery_ok_threshold`.

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.

        ### Returns:
        - `True` if the current consecutive amount has reached the minimum threshold.
        - `False` if not.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        history_raw_dict[HistoryDictKey.CONSECUTIVE_OK_FRAMES] += 1
        if history_raw_dict[HistoryDictKey.CONSECUTIVE_OK_FRAMES] >= self.recovery_ok_threshold:
            Logger.info("Camera became stable again after receiving enough consecutive valid frames.")
            history_raw_dict[HistoryDictKey.IS_CAMERA_STABLE] = True
            return True
        else:
            return False
    
    ################################
    ### RESET BAD FRAME COUNTERS ###
    ################################
    def _reset_bad_frame_counters(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `_reset_bad_frame_counters` method resets all bad frame counters (to 0).

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        for quality_enum in PoseQuality:
            history_raw_dict[HistoryDictKey.BAD_FRAME_COUNTERS][quality_enum.name] = 0
            history_raw_dict[HistoryDictKey.BAD_FRAME_STREAKS][quality_enum.name] = 0

        history_raw_dict[HistoryDictKey.FRAMES_SINCE_LAST_VALID] = 0

    ###########################
    ### POP FRAME IF NEEDED ###
    ###########################
    def _pop_frame_if_needed(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `_pop_frame_if_needed` checks if the current amount of stored frames is bigger
        than the allowed amount as configured in the configuration file.
        Pops frame/s (from the begining, which are the oldest).

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        if self.frames_rolling_window_size is None: return # Failed to read from configuration file.
        try:
            while len(history_raw_dict[HistoryDictKey.FRAMES]) > self.frames_rolling_window_size:
                history_raw_dict[HistoryDictKey.FRAMES].pop(0)
        except IndexError as e:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(
                error=ErrorCode.ERROR_WITH_HANDLING_FRAMES_LIST,
                origin=inspect.currentframe(),
                extra_info={ "Exception": type(e), "Reason": str(e) }
            )

    ###############################
    ### POP BAD FRAME IF NEEDED ###
    ###############################
    def _pop_bad_frame_if_needed(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `_pop_bad_frame_if_needed` checks if the current amount of stored bad frames is bigger
        than the allowed amount as configured in the configuration file.
        Pops frame/s (from the begining, which are the oldest).

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        if self.bad_frame_log_size is None: return # Failed to read from configuration file.
        try:
            while len(history_raw_dict[HistoryDictKey.BAD_FRAMES_LOG]) > self.bad_frame_log_size:
                history_raw_dict[HistoryDictKey.BAD_FRAMES_LOG].pop(0)
        except IndexError as e:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(
                error=ErrorCode.ERROR_WITH_HANDLING_BAD_FRAMES_LIST,
                origin=inspect.currentframe(),
                extra_info={ "Exception": type(e), "Reason": str(e) }
            )

    ############################
    ### GET RAW HISTORY DATA ###
    ############################
    def _get_raw_history_data(self, history_data:HistoryData) -> Dict[str, Any]:
        """
        ### Brief:
        The `_get_raw_history_data` method returns the raw history data dictionary.

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.

        ### Returns:
        - `Dict[str, Any] - The raw history data dictionary.
        """
        return history_data.history
    
    ################################
    ### UPDATE LOW MOTION STREAK ###
    ################################
    def _update_low_motion_streak(self, history_data:HistoryData, joints:Dict[str, float]) -> None:
        """
        ### Brief:
        The `_update_low_motion_streak` method updates the low motion streak counter
        based on the provided joint angles.

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        - `joints` (Dict[str, float]): The current joint angles.
        """
        history_raw_dict:Dict[str, Any] = self._get_raw_history_data(history_data)

        # Get the last valid frame.
        last_valid_frame:Dict[str, Any] = history_data.get_last_valid_frame()
        if last_valid_frame is None or joints is None:
            history_raw_dict[HistoryDictKey.LOW_MOTION_STREAK] = 0
            return

        # Get the previous joints.
        prev_joints = last_valid_frame[HistoryDictKey.Frame.JOINTS]
        if prev_joints is None:
            history_raw_dict[HistoryDictKey.LOW_MOTION_STREAK] = 0
            return

        # Calculating angle deltas.
        deltas = []
        for name in joints:
            if name in joints and name in prev_joints:
                if joints[name] is None or prev_joints[name] is None:
                    continue
                deltas.append(abs(float(joints[name]) - float(prev_joints[name])))
        # If no deltas - reset streak.
        if not deltas:
            history_raw_dict[HistoryDictKey.LOW_MOTION_STREAK] = 0
            return

        # Calculate average motion score.
        motion_score = sum(deltas) / len(deltas)
        # Update streak if below threshold.
        if motion_score <= self.low_motion_angle_degrees_threshold:
            history_raw_dict[HistoryDictKey.LOW_MOTION_STREAK] += 1
        else:
            history_raw_dict[HistoryDictKey.LOW_MOTION_STREAK] = 0

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
        from Server.Utilities.Error.ErrorHandler import ErrorHandler
        from Server.Utilities.Error.ErrorCode import ErrorCode

        # Reading frames rolling window size.
        self.frames_rolling_window_size:int = ConfigLoader.get([
            ConfigParameters.Major.HISTORY,
            ConfigParameters.Minor.FRAMES_ROLLING_WINDOW_SIZE
        ])
        if self.frames_rolling_window_size is None:
            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_INIT_ERROR,
                origin=inspect.currentframe(),
                extra_info={ "Frames rolling window size": "Not found in the configuration file" }
            )
            self.frames_rolling_window_size = None # Using unlimited.
        
        # Reading bad frame list size.
        self.bad_frame_log_size:int = ConfigLoader.get([
            ConfigParameters.Major.HISTORY,
            ConfigParameters.Minor.BAD_FRAME_LOG_SIZE
        ])
        if self.bad_frame_log_size is None:
            
            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_INIT_ERROR,
                origin=inspect.currentframe(),
                extra_info={ "Bad frames log maximum size": "Not found in the configuration file" }
            )
            self.bad_frame_log_size = None # Using unlimited.

        # Reading recocery 'ok' (frames) threshold.
        self.recovery_ok_threshold:int = ConfigLoader.get([
            ConfigParameters.Major.HISTORY,
            ConfigParameters.Minor.RECOVERY_OK_THRESHOLD
        ])
        if self.recovery_ok_threshold is None:
            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_INIT_ERROR,
                origin=inspect.currentframe(),
                extra_info={ "Recovery 'OK' threshold": "Not found in the configuration file" }
            )
            self.recovery_ok_threshold = 4

        # Reading bad stability limit.
        self.bad_stability_limit:int = ConfigLoader.get([
            ConfigParameters.Major.HISTORY,
            ConfigParameters.Minor.BAD_STABILITY_LIMIT
        ])
        if self.bad_stability_limit is None:
            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_INIT_ERROR,
                origin=inspect.currentframe(),
                extra_info={ "Bad stability limit": "Not found in the configuration file" }
            )
            self.bad_stability_limit = 30
        
        # Reading maximum consecutive invalid frames before abort.
        self.max_consecutive_invalid_before_abort:int = ConfigLoader.get([
            ConfigParameters.Major.HISTORY,
            ConfigParameters.Minor.MAX_CONSECUTIVE_INVALID_BEFORE_ABORT
        ])
        if self.max_consecutive_invalid_before_abort is None:
            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_INIT_ERROR,
                origin=inspect.currentframe(),
                extra_info={ "Max consecutive invalid frames before abort": "Not found in the configuration file" }
            )
            self.max_consecutive_invalid_before_abort = 60

        # Reading low motion angle degrees threshold.
        self.low_motion_angle_degrees_threshold:float = ConfigLoader.get([
            ConfigParameters.Major.HISTORY,
            ConfigParameters.Minor.LOW_MOTION_ANGLE_DEGREES_THRESHOLD
        ])
        if self.low_motion_angle_degrees_threshold is None:
            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_INIT_ERROR,
                origin=inspect.currentframe(),
                extra_info={ "Low motion angle degrees threshold": "Not found in the configuration file" }
            )
            self.low_motion_angle_degrees_threshold = 3.0

        # Reading transition orders of each exercise.
        config_file_path:str = ConfigLoader.get(
            key=[
                ConfigParameters.Major.PHASE,
                ConfigParameters.Minor.PHASE_DETECTOR_CONFIG_FILE
            ]
        )
        # Load thresholds from the specific configuration file.
        thresholds:Dict[str, Any] = ConfigLoader.get(
            key=None,
            different_file=config_file_path,
            read_all=True
        )

        # Store transition orders and initial phases.
        self.transition_order_per_exercise:Dict[ExerciseType, Any] = {}
        self.initial_phase_per_exercise:Dict[ExerciseType, PhaseType]    = {}

        from Server.Data.Phase.PhaseDictKey import PhaseDictKey
        for exercise_type in ExerciseType:
            # Get exercise configuration.
            exercise_config:Dict[str, Any] = thresholds.get(exercise_type.value, None)
            if exercise_config is None:
                ErrorHandler.handle(
                    error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Exercise Type": exercise_type.name,
                        "Reason": "Not found in the configuration file"
                    }
                )
            # Get transition order.
            exercise_order:List[str] = exercise_config.get(PhaseDictKey.TRANSITION_ORDER, None)
            exercise_phases:List[PhaseType] = []
            if exercise_order is None:
                ErrorHandler.handle(
                    error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Exercise Type": exercise_type.name,
                        "Reason": "Not found in the configuration file"
                    }
                )
            # Convert phase names to enums.
            for phase in exercise_order:
                try:
                    phase_enum = PhaseType.get_phase_enum(exercise_type)
                    exercise_phases.append(PhaseType.get_phase_enum(exercise_type)[phase])
                except Exception as e:
                    ErrorHandler.handle(
                        error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                        origin=inspect.currentframe(),
                        extra_info={
                            "Exception": type(e),
                            "Cause": str(e),
                            "Exercise Type": exercise_type.name,
                            "Reason": f"Phase '{phase}' in transition order is not a valid phase"
                        }
                    )
            # Store transition order.
            self.transition_order_per_exercise[exercise_type] = exercise_phases

            # Get initial phase.
            exercise_initial_phase:str = exercise_config.get(PhaseDictKey.INITIAL_PHASE, None)
            if exercise_initial_phase is None:
                ErrorHandler.handle(
                    error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Exercise Type": exercise_type.name,
                        "Reason": "Initial phase not found in the configuration file"
                    }
                )
            # Store initial phase.
            try:
                self.initial_phase_per_exercise[exercise_type] = PhaseType.get_phase_enum(exercise_type)[exercise_initial_phase]
            except:
                ErrorHandler.handle(
                    error=ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Exercise Type": exercise_type.name,
                        "Reason": f"Initial phase '{exercise_initial_phase}' is not a valid phase"
                    }
                )