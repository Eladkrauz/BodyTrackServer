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
        self._retrieve_configurations()
        self._reset_bad_frame_counters()

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
        - `frame_id` (int): The frame number
        - `joints` (Dict[JointAngle, Any]): The angles dictionary from `JointAnalyzer`
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
            history_data[HistoryDictKey.FRAMES].append(new_frame)
            self._pop_frame_if_needed()

            # If the current frame is valid but not yet stable (lower than threshold),
            # keep info about the previous bad frames.
            if not self._is_valid_frame_in_threshold(): return

            # Updating last valid frame.
            history_data[HistoryDictKey.LAST_VALID_FRAME] = new_frame

            # Resetting counters.
            self._reset_bad_frame_counters()

            # If stable enough - restore confidence.
            self.ok_streak += 1; self.bad_streak = 0
            if self.ok_streak >= self.recovery_ok_threshold:
                history_data[HistoryDictKey.IS_CAMERA_STABLE] = True

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
    def add_frame_error(self, history_data:HistoryData, error_to_add:str, frame_id:int = -1) -> None:
        """
        ### Brief:
        The `add_frame_error` method adds an error to a frame.

        ### Arguments:
        - `error_to_add` (str): The error to be added.
        - `frame_id` (int): The frame id.
            - Defaults to -1.
            - In that case - adding to the last valid frame (which is `history_data[HistoryDictKey.FRAMES][-1]`).
            - Otherwise - searching for the relevant frame in the list and adding it.
        """
        # If frame_id was specified (generally not supposed to happen).
        if frame_id != -1:
            current_amount_of_frames = len(history_data[HistoryDictKey.FRAMES])
            for i in range(current_amount_of_frames - 1, -1, -1):
                iterated_frame_id = history_data[HistoryDictKey.FRAMES][i][HistoryDictKey.Frame.FRAME_ID]
                if iterated_frame_id == frame_id:
                    history_data[HistoryDictKey.FRAMES][i][HistoryDictKey.Frame.ERRORS].append(error_to_add)
                    return
            
            # If arrived here - did not find the frame in the list (probably it is too old).
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(
                error=ErrorCode.CANT_FIND_FRAME_IN_FRAMES_WINDOW,
                origin=inspect.currentframe()
            )
        # If not - adding the error to the last frame.
        else:
            last_valid_frame:dict = history_data[HistoryDictKey.LAST_VALID_FRAME]
            if last_valid_frame is None:
                from Server.Utilities.Error.ErrorHandler import ErrorHandler
                from Server.Utilities.Error.ErrorCode import ErrorCode
                ErrorHandler.handle(
                    error=ErrorCode.LAST_VALID_FRAME_IS_NONE,
                    origin=inspect.currentframe()
                )
            else:
                last_valid_frame[HistoryDictKey.Frame.ERRORS].append(error_to_add)

    ############################
    ### RECORD INVALID FRAME ###
    ############################
    def record_invalid_frame(self, history_data:HistoryData, frame_id:int, invalid_reason:PoseQuality) -> None:
        """
        ### Brief:
        The `record_invalid_frame` method adds a new invalid (not OK) frame record to history.

        This method is called only after:
            1. `PoseAnalyzer` produced landmarks
            2. `PoseQualityManager` returned something else but `PoseQuality.OK`

        ### Argumetns:
        - `frame_id` (int): The frame number
        - `invalid_reason` (PoseQuality): The reason why the frame is invalid
        """
        try:
            entry = {
                HistoryDictKey.BadFrame.FRAME_ID:  frame_id,
                HistoryDictKey.BadFrame.TIMESTAMP: datetime.now(),
                HistoryDictKey.BadFrame.REASON:    invalid_reason.value
            }
            history_data[HistoryDictKey.BAD_FRAMES_LOG].append(entry)
            self._pop_bad_frame_if_needed()

            # Increment total counters for this reason.
            history_data[HistoryDictKey.BAD_FRAME_COUNTERS][invalid_reason.name] += 1
            # Increase total invalid frames count.
            history_data[HistoryDictKey.FRAMES_SINCE_LAST_VALID] += 1
            # Increment bad frame streak.
            for pose_quality in history_data[HistoryDictKey.BAD_FRAME_STREAKS]:
                if pose_quality == invalid_reason.name:
                    history_data[HistoryDictKey.BAD_FRAME_STREAKS][pose_quality] += 1
                else:
                    history_data[HistoryDictKey.BAD_FRAME_STREAKS][pose_quality] = 0

            # Break the OK streak.
            history_data[HistoryDictKey.CONSECUTIVE_OK_FRAMES] = 0

            # If too many bad frames - system is unstable.
            self.bad_streak += 1; self.ok_streak = 0
            if self.bad_streak >= self.bad_stability_limit:
                history_data[HistoryDictKey.IS_CAMERA_STABLE] = False

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
    def record_phase_transition(self, history_data:HistoryData, old_phase:PhaseType, new_phase:PhaseType, frame_id:int, joints:Dict[str, float]) -> None:
        """
        ### Brief:
        The `record_phase_transition` method records a biomechanical phase transition event.
        This is triggered only when `PhaseDetector` identifies an actual movement state transition.

        ### Arguments:
        - `old_phase` (PhaseType): The previous phase.
        - `new_phase` (PhaseType): The new phase.
        - `frame_id` (int): The frame where the transition happened.
        - `joints` (dict[str, float]): Snapshot of key joint angles at transition moment.
        """
        now = datetime.now()

        # If we have a previous transition (it is not the first now) - compute duration.
        transitions:list = history_data[HistoryDictKey.PHASE_TRANSITIONS]
        if transitions:
            last = transitions[-1]
            start_time:datetime = last[HistoryDictKey.PhaseTransition.TIMESTAMP]
            duration = (now - start_time).total_seconds()

            # Store finished phase duration entry.
            history_data[HistoryDictKey.PHASE_DURATIONS].append({
                HistoryDictKey.PhaseDuration.PHASE:       last[HistoryDictKey.PhaseTransition.PHASE_TO],
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
        history_data[HistoryDictKey.PHASE_STATE] = new_phase
        history_data[HistoryDictKey.PHASE_START_TIME] = now

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
        """
        if history_data[HistoryDictKey.CURRENT_REP] is not None:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(error=ErrorCode.TRIED_TO_START_REP_WHILE_HAVE_ONE, origin=inspect.currentframe())
        else:
            new_rep = {
                HistoryDictKey.CurrentRep.START_TIME: datetime.now(),
                HistoryDictKey.CurrentRep.HAS_ERROR:  False,
                HistoryDictKey.CurrentRep.ERRORS:     []
            }

            history_data[HistoryDictKey.CURRENT_REP] = new_rep

    ################################
    ### ADD ERROR TO CURRENT REP ###
    ################################
    def add_error_to_current_rep(self, history_data:HistoryData, error_to_add:str) -> None:
        """
        ### Brief:
        The `add_error_to_current_rep` method adds a new detected error to the current repetition.

        ### Arguments:
        - `error_to_add` (str): The detected error to be added.
        """
        if history_data[HistoryDictKey.CURRENT_REP] is None:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(error=ErrorCode.TRIED_TO_ADD_ERROR_TO_NONE_REP, origin=inspect.currentframe())
        else:
            history_data[HistoryDictKey.CURRENT_REP][HistoryDictKey.CurrentRep.HAS_ERROR] = True
            history_data[HistoryDictKey.CURRENT_REP][HistoryDictKey.CurrentRep.ERRORS].append(error_to_add)

    #######################
    ### END CURRENT REP ###
    #######################
    def end_current_rep(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `end_current_rep` method finishes the current repetition.
        """
        if history_data[HistoryDictKey.CURRENT_REP] is None:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(error=ErrorCode.TRIED_TO_END_A_NONE_REP, origin=inspect.currentframe())
        else:
            # Finishing current rep and inserting it to the completed reps list.
            current_rep:dict = history_data[HistoryDictKey.CURRENT_REP]
            start_time:datetime = current_rep[HistoryDictKey.CurrentRep.START_TIME]
            end_time:datetime = datetime.now()
            completed_rep = {
                HistoryDictKey.Repetition.START_TIME: start_time,
                HistoryDictKey.Repetition.END_TIME:   end_time,
                HistoryDictKey.Repetition.DURATION:   (end_time - start_time).total_seconds(),
                HistoryDictKey.Repetition.IS_CORRECT: not current_rep[HistoryDictKey.CurrentRep.HAS_ERROR],
                HistoryDictKey.Repetition.ERRORS:     current_rep[HistoryDictKey.CurrentRep.ERRORS]
            }
            history_data[HistoryDictKey.REPETITIONS].append(completed_rep)
            history_data[HistoryDictKey.REP_COUNT] += 1
            history_data[HistoryDictKey.CURRENT_REP] = None

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
        """
        if history_data[HistoryDictKey.EXERCISE_START_TIME] is None:
            history_data[HistoryDictKey.EXERCISE_START_TIME] = datetime.now()
        else:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(
                error=ErrorCode.EXERCISE_START_TIME_ALREADY_SET,
                origin=inspect.currentframe(),
                extra_info={ "Already Set": history_data[HistoryDictKey.EXERCISE_START_TIME] }
            )

    #########################
    ### MARK EXERCISE END ###
    #########################
    def mark_exercise_end(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `mark_exercise_start` method sets the exercise end timestamp (only once).
        """
        try:
            # Prevent multiple calls.
            if history_data[HistoryDictKey.EXERCISE_END_TIME] is not None:
                from Server.Utilities.Error.ErrorHandler import ErrorHandler
                from Server.Utilities.Error.ErrorCode import ErrorCode
                ErrorHandler.handle(
                    error=ErrorCode.EXERCISE_END_TIME_ALREADY_SET,
                    origin=inspect.currentframe(),
                    extra_info={ "Already Set": history_data[HistoryDictKey.EXERCISE_END_TIME] }
                )
                return

            # Mark end time.
            end_timestamp = datetime.now()
            history_data[HistoryDictKey.EXERCISE_END_TIME] = end_timestamp

            # Finalize last open phase.
            transitions:list = history_data[HistoryDictKey.PHASE_TRANSITIONS]
            durations:list   = history_data[HistoryDictKey.PHASE_DURATIONS]
            repetitions:list = history_data[HistoryDictKey.REPETITIONS]
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
            current_rep:dict = history_data[HistoryDictKey.CURRENT_REP]
            if current_rep is not None:
                start_time = current_rep[HistoryDictKey.CurrentRep.START_TIME]

                completed_rep = {
                    HistoryDictKey.Repetition.START_TIME: start_time,
                    HistoryDictKey.Repetition.END_TIME:   end_timestamp,
                    HistoryDictKey.Repetition.DURATION:   (end_timestamp - start_time).total_seconds(),
                    HistoryDictKey.Repetition.IS_CORRECT: False,  # Incomplete rep = not correct.
                    HistoryDictKey.Repetition.ERRORS:     current_rep.get(HistoryDictKey.CurrentRep.ERRORS, [])
                }
                repetitions.append(completed_rep)
                history_data[HistoryDictKey.REP_COUNT] += 1

                # Clear current rep.
                history_data[HistoryDictKey.CURRENT_REP] = None

        except Exception as e:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode

            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_INTERNAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={"Exception": type(e), "Reason": str(e)}
            )

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

        ### Returns:
        - `True` if the current consecutive amount has reached the minimum threshold.
        - `False` if not.
        """
        history_data[HistoryDictKey.CONSECUTIVE_OK_FRAMES] += 1
        return history_data[HistoryDictKey.CONSECUTIVE_OK_FRAMES] >= self.recovery_ok_threshold
    
    ################################
    ### RESET BAD FRAME COUNTERS ###
    ################################
    def _reset_bad_frame_counters(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `_reset_bad_frame_counters` method resets all bad frame counters (to 0).
        """
        for quality_enum in PoseQuality:
            history_data[HistoryDictKey.BAD_FRAME_COUNTERS][quality_enum.name] = 0
            history_data[HistoryDictKey.BAD_FRAME_STREAKS][quality_enum.name] = 0

        history_data[HistoryDictKey.FRAMES_SINCE_LAST_VALID] = 0

    ###########################
    ### POP FRAME IF NEEDED ###
    ###########################
    def _pop_frame_if_needed(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `_pop_frame_if_needed` checks if the current amount of stored frames is bigger
        than the allowed amount as configured in the configuration file.
        Pops frame/s (from the begining, which are the oldest).
        """
        if self.frames_rolling_window_size is None: return # Failed to read from configuration file.
        try:
            while len(history_data[HistoryDictKey.FRAMES]) > self.frames_rolling_window_size:
                history_data[HistoryDictKey.FRAMES].pop(0)
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
        """
        if self.bad_frame_log_size is None: return # Failed to read from configuration file.
        try:
            while len(history_data[HistoryDictKey.BAD_FRAMES_LOG]) > self.bad_frame_log_size:
                history_data[HistoryDictKey.BAD_FRAMES_LOG].pop(0)
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
    def _retrieve_configurations(self) -> None:
        """
        ### Brief:
        The `_retrieve_configurations` method gets the updated configurations from the
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