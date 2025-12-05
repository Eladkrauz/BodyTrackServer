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
from typing import Dict, TYPE_CHECKING
from copy import deepcopy

from Server.Data.Pose.PoseQuality import PoseQuality
from Server.Data.History.HistoryDictKey import HistoryDictKey
from Server.Data.History.HistoryData import HistoryData
from Server.Data.Error.DetectedErrorCode import DetectedErrorCode

if TYPE_CHECKING:
    from Server.Data.Phase.PhaseType import PhaseType
    from Server.Data.Pose.PoseQuality import PoseQuality
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

    ###############################################################################################
    ############################## RECORD NEW VALID OR INVALID FRAME ##############################
    ###############################################################################################

    ##########################
    ### RECORD VALID FRAME ###
    ##########################
    def record_valid_frame(self, history_data:HistoryData, frame_id:int, joints:Dict[JointAngle, float]) -> None:
        """
        ### Brief:
        The `record_valid_frame` method adds a new valid (OK) frame record to history.

        This method is called only after:
            1. `PoseAnalyzer` produced landmarks
            2. `PoseQualityManager` returned `PoseQuality.OK`
            3. `JointAnalyzer` successfully computed joints

        ### Argumetns:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        - `frame_id` (int): The frame number
        - `joints` (Dict[JointAngle, Any]): The angles dictionary from `JointAnalyzer`

        ### Use:
        - Used by the `SessionManager` to record an `OK` frame after calculating its joints.
        """
        try:
            # New frame to store.
            new_frame = {
                HistoryDictKey.Frame.FRAME_ID:  frame_id,
                HistoryDictKey.Frame.TIMESTAMP: datetime.now(),
                HistoryDictKey.Frame.JOINTS:    deepcopy(joints),
                HistoryDictKey.Frame.ERRORS:    []
            }

            # Inserting and handling rolling window of the frames list.
            history_data.history[HistoryDictKey.FRAMES].append(new_frame)
            self._pop_frame_if_needed(history_data)

            # If the current frame is valid but not yet stable (lower than threshold),
            # keep info about the previous bad frames.
            if not self._is_valid_frame_in_threshold(history_data): return

            # Updating last valid frame.
            history_data.history[HistoryDictKey.LAST_VALID_FRAME] = new_frame

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
        current_amount_of_frames = len(history_data.history[HistoryDictKey.FRAMES])
        error_to_add:str = error_to_add.name
        for i in range(current_amount_of_frames - 1, -1, -1):
            iterated_frame_id = history_data.history[HistoryDictKey.FRAMES][i][HistoryDictKey.Frame.FRAME_ID]
            if iterated_frame_id == frame_id:
                history_data.history[HistoryDictKey.FRAMES][i][HistoryDictKey.Frame.ERRORS].append(error_to_add)
                # Updating counters.
                error_counters:dict = history_data.history[HistoryDictKey.ERROR_COUNTERS]
                if error_counters.get(error_to_add, None) is None: error_counters[error_to_add] = 1
                else:                                              error_counters[error_to_add] += 1

                # Updating streaks.
                error_streaks:dict = history_data.history[HistoryDictKey.ERROR_STREAKS]
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
    
    ##################################
    ### UPDATE FRAME ABSOLUTELY OK ###
    ##################################
    def update_frame_absolutely_ok(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `update_frame_absolutely_ok` method is called when a frame is valid
        and does not have any detected error. The method resets the `ERROR_COUNTERS`.

        ### Argumetns:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        """
        error_counters:dict = history_data.history[HistoryDictKey.ERROR_COUNTERS]
        error_counters.clear()

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
        try:
            entry = {
                HistoryDictKey.BadFrame.FRAME_ID:  frame_id,
                HistoryDictKey.BadFrame.TIMESTAMP: datetime.now(),
                HistoryDictKey.BadFrame.REASON:    invalid_reason.value
            }
            history_data.history[HistoryDictKey.BAD_FRAMES_LOG].append(entry)
            self._pop_bad_frame_if_needed(history_data)

            # Increment total counters for this reason.
            history_data.history[HistoryDictKey.BAD_FRAME_COUNTERS][invalid_reason.name] += 1
            # Increase total invalid frames count.
            history_data.history[HistoryDictKey.FRAMES_SINCE_LAST_VALID] += 1
            # Increment bad frame streak.
            for pose_quality in history_data.history[HistoryDictKey.BAD_FRAME_STREAKS]:
                if pose_quality == invalid_reason.name:
                    history_data.history[HistoryDictKey.BAD_FRAME_STREAKS][pose_quality] += 1
                else:
                    history_data.history[HistoryDictKey.BAD_FRAME_STREAKS][pose_quality] = 0

            # Break the OK streak.
            self.reset_consecutive_ok_streak(history_data)

            # If too many bad frames - system is unstable.
            if history_data.history[HistoryDictKey.BAD_FRAME_STREAKS][invalid_reason] >= self.bad_stability_limit:
                    history_data.history[HistoryDictKey.IS_CAMERA_STABLE] = False

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

    ###############################
    ### RECOED PHASE TRANSITION ###
    ###############################
    def record_phase_transition(self, history_data:HistoryData, new_phase:PhaseType, frame_id:int, joints:Dict[str, float]) -> None:
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
        old_phase = history_data.get_previous_phase()
        if new_phase is None or old_phase is None or new_phase == old_phase: return
        now = datetime.now()

        # If we have a previous transition (it is not the first now) - compute duration.
        transitions:list = history_data.history[HistoryDictKey.PHASE_TRANSITIONS]
        if transitions:
            last = transitions[-1]
            start_time:datetime = last[HistoryDictKey.PhaseTransition.TIMESTAMP]
            duration = (now - start_time).total_seconds()

            # Store finished phase duration entry.
            history_data.history[HistoryDictKey.PHASE_DURATIONS].append({
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
        history_data.history[HistoryDictKey.PHASE_STATE] = new_phase
        history_data.history[HistoryDictKey.PHASE_START_TIME] = now

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
        if history_data.history[HistoryDictKey.CURRENT_REP] is not None:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(error=ErrorCode.TRIED_TO_START_REP_WHILE_HAVE_ONE, origin=inspect.currentframe())
        else:
            new_rep = {
                HistoryDictKey.CurrentRep.START_TIME: datetime.now(),
                HistoryDictKey.CurrentRep.HAS_ERROR:  False,
                HistoryDictKey.CurrentRep.ERRORS:     []
            }

            history_data.history[HistoryDictKey.CURRENT_REP] = new_rep

    ################################
    ### ADD ERROR TO CURRENT REP ###
    ################################
    def add_error_to_current_rep(self, history_data:HistoryData, error_to_add:str) -> None:
        """
        ### Brief:
        The `add_error_to_current_rep` method adds a new detected error to the current repetition.

        ### Arguments:
        - `history_data` (HistoryData): The `HistoryData` instance to work with.
        - `error_to_add` (str): The detected error to be added.
        """
        if history_data.history[HistoryDictKey.CURRENT_REP] is None:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(error=ErrorCode.TRIED_TO_ADD_ERROR_TO_NONE_REP, origin=inspect.currentframe())
        else:
            history_data.history[HistoryDictKey.CURRENT_REP][HistoryDictKey.CurrentRep.HAS_ERROR] = True
            history_data.history[HistoryDictKey.CURRENT_REP][HistoryDictKey.CurrentRep.ERRORS].append(error_to_add)

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
        if history_data.history[HistoryDictKey.CURRENT_REP] is None:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(error=ErrorCode.TRIED_TO_END_A_NONE_REP, origin=inspect.currentframe())
        else:
            # Finishing current rep and inserting it to the completed reps list.
            current_rep:dict = history_data.history[HistoryDictKey.CURRENT_REP]
            start_time:datetime = current_rep[HistoryDictKey.CurrentRep.START_TIME]
            end_time:datetime = datetime.now()
            completed_rep = {
                HistoryDictKey.Repetition.START_TIME: start_time,
                HistoryDictKey.Repetition.END_TIME:   end_time,
                HistoryDictKey.Repetition.DURATION:   (end_time - start_time).total_seconds(),
                HistoryDictKey.Repetition.IS_CORRECT: not current_rep[HistoryDictKey.CurrentRep.HAS_ERROR],
                HistoryDictKey.Repetition.ERRORS:     deepcopy(current_rep[HistoryDictKey.CurrentRep.ERRORS])
            }
            history_data.history[HistoryDictKey.REPETITIONS].append(completed_rep)
            history_data.history[HistoryDictKey.REP_COUNT] += 1
            history_data.history[HistoryDictKey.CURRENT_REP] = None

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
        if history_data.history[HistoryDictKey.EXERCISE_START_TIME] is None:
            history_data.history[HistoryDictKey.EXERCISE_START_TIME] = datetime.now()
        else:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(
                error=ErrorCode.EXERCISE_START_TIME_ALREADY_SET,
                origin=inspect.currentframe(),
                extra_info={ "Already Set": history_data.history[HistoryDictKey.EXERCISE_START_TIME] }
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
        try:
            # Prevent multiple calls.
            if history_data.history[HistoryDictKey.EXERCISE_END_TIME] is not None:
                from Server.Utilities.Error.ErrorHandler import ErrorHandler
                from Server.Utilities.Error.ErrorCode import ErrorCode
                ErrorHandler.handle(
                    error=ErrorCode.EXERCISE_END_TIME_ALREADY_SET,
                    origin=inspect.currentframe(),
                    extra_info={ "Already Set": history_data.history[HistoryDictKey.EXERCISE_END_TIME] }
                )
                return

            # Mark end time.
            end_timestamp = datetime.now()
            history_data.history[HistoryDictKey.EXERCISE_END_TIME] = end_timestamp

            # Finalize last open phase.
            transitions:list = history_data.history[HistoryDictKey.PHASE_TRANSITIONS]
            durations:list   = history_data.history[HistoryDictKey.PHASE_DURATIONS]
            repetitions:list = history_data.history[HistoryDictKey.REPETITIONS]
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
            current_rep:dict = history_data.history[HistoryDictKey.CURRENT_REP]
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
                history_data.history[HistoryDictKey.REP_COUNT] += 1

                # Clear current rep.
                history_data.history[HistoryDictKey.CURRENT_REP] = None

        except Exception as e:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode

            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_INTERNAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={"Exception": type(e), "Reason": str(e)}
            )

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
        return history_data.history[HistoryDictKey.FRAMES_SINCE_LAST_VALID] >= self.max_consecutive_invalid_before_abort
    
    #######################################
    ### INCREMENT CONSECUTIVE OK STREAK ###
    #######################################
    def increment_consecutive_ok_streak(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `increment_ok_streak` method increments the number of consecutive `OK` frames.
        """
        history_data.history[HistoryDictKey.CONSECUTIVE_OK_FRAMES] += 1
    
    ###################################
    ### RESET CONSECUTIVE OK STREAK ###
    ###################################
    def reset_consecutive_ok_streak(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `reset_consecutive_ok_streak` method resets the number of consecutive `OK` frames.
        """
        history_data.history[HistoryDictKey.CONSECUTIVE_OK_FRAMES] = 0
    
    ################################################
    ### INCREMENT CONSECUTIVE INIT PHASE COUNTER ###
    ################################################
    def increment_consecutive_init_phase_counter(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `increment_consecutive_init_phase_counter` method increments the number of consecutive
        correct initial phase detections.
        """
        history_data.history[HistoryDictKey.INITIAL_PHASE_COUNTER] += 1
    
    ############################################
    ### RESET CONSECUTIVE INIT PHASE COUNTER ###
    ############################################
    def reset_consecutive_init_phase_counter(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `reset_consecutive_init_phase_counter` method resets the number of consecutive
        correct initial phase detections.
        """
        history_data.history[HistoryDictKey.INITIAL_PHASE_COUNTER] = 0

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
        history_data.history[HistoryDictKey.CONSECUTIVE_OK_FRAMES] += 1
        if history_data.history[HistoryDictKey.CONSECUTIVE_OK_FRAMES] >= self.recovery_ok_threshold:
            history_data.history[HistoryDictKey.IS_CAMERA_STABLE] = True
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
        for quality_enum in PoseQuality:
            history_data.history[HistoryDictKey.BAD_FRAME_COUNTERS][quality_enum.name] = 0
            history_data.history[HistoryDictKey.BAD_FRAME_STREAKS][quality_enum.name] = 0

        history_data.history[HistoryDictKey.FRAMES_SINCE_LAST_VALID] = 0

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
        if self.frames_rolling_window_size is None: return # Failed to read from configuration file.
        try:
            while len(history_data.history[HistoryDictKey.FRAMES]) > self.frames_rolling_window_size:
                history_data.history[HistoryDictKey.FRAMES].pop(0)
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
        if self.bad_frame_log_size is None: return # Failed to read from configuration file.
        try:
            while len(history_data.history[HistoryDictKey.BAD_FRAMES_LOG]) > self.bad_frame_log_size:
                history_data.history[HistoryDictKey.BAD_FRAMES_LOG].pop(0)
        except IndexError as e:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(
                error=ErrorCode.ERROR_WITH_HANDLING_BAD_FRAMES_LIST,
                origin=inspect.currentframe(),
                extra_info={ "Exception": type(e), "Reason": str(e) }
            )

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

        # Reading frames rolling window size.
        self.frames_rolling_window_size:int = ConfigLoader.get([
            ConfigParameters.Major.HISTORY,
            ConfigParameters.Minor.FRAMES_ROLLING_WINDOW_SIZE
        ])
        if self.frames_rolling_window_size is None:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
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
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
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
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
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
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
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
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_INIT_ERROR,
                origin=inspect.currentframe(),
                extra_info={ "Max consecutive invalid frames before abort": "Not found in the configuration file" }
            )
            self.max_consecutive_invalid_before_abort = 60