############################################################
######### BODY TRACK // SERVER // DATA // HISTORY ##########
############################################################
################## CLASS: HistoryData ######################
############################################################

###############
### IMPORTS ###
###############
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Optional, List, TYPE_CHECKING
from copy import deepcopy

from Server.Data.Pose.PoseQuality import PoseQuality
from Server.Data.History.HistoryDictKey import HistoryDictKey

if TYPE_CHECKING:
    from Server.Data.Phase.PhaseType import PhaseType
    from Server.Data.Pose.PoseQuality import PoseQuality

##########################
### HISTORY DATA CLASS ###
##########################
class HistoryData:
    """
    ### Description:
    The `HistoryData` maintains all session-level temporal and state information needed by:
    - `PhaseDetector` (state machine)
    - `ErrorDetector`
    - `FeedbackFormatter`
    - `SessionSummaryManager`

    ### Stored Elements:

    {
        `HistoryDictKey.FRAMES`:                        A `list` of Frame dictionaries
        `HistoryDictKey.LAST_VALID_FRAME`:              A `dict` which holds the last valid frame
        `HistoryDictKey.CONSECUTIVE_OK_FRAMES`:         An `int` which holds the number of consecutive OK frames
        `HistoryDictKey.ERROR_COUNTERS`:                A `dict` containing counters for detected errors.
        `HistoryDictKey.ERROR_STRIKES`:                 A `dict` containing consecutive counters for detected errors.
        `HistoryDictKey.LOW_MOTION_STREAK`:             An `int` which holds the number of consecutive low-motion frames

        `HistoryDictKey.PHASE_STATE`:                   The current exercise phase (`PhaseType` enum element)
        `HistoryDictKey.PHASE_TRANSITIONS`:             A `dict` for historical context of phase changes
        `HistoryDictKey.PHASE_DURATIONS`:               A `dict` for historical context of phase durations
        `HistoryDictKey.INITIAL_PHASE_COUNTER`:         An `int` which holds the number of consecutive frames with initial exercise phase

        `HistoryDictKey.BAD_FRAME_COUNTERS`:            A `dict` containing counters for bad frames
        `HistoryDictKey.BAD_FRAME_STREAKS`:             A `dict` containing consecutive counters for bad frames
        `HistoryDictKey.BAD_FRAMES_LOG`:                A `list` that stores minimal info about bad frames
        `HistoryDictKey.FRAMES_SINCE_LAST_VALID`:       A counter for tracking the gap between valid frames

        `HistoryDictKey.REP_COUNT`:                     A counter for tracking amount of repetitions
        `HistoryDictKey.REPETITIONS`:                   A `list` that stores finished repetitions
        `HistoryDictKey.CURRENT_REP`:                   A `dict` which stores current repetition info
        `HistoryDictKey.CURRENT_TRANSITION_INDEX`:      An `int` which stores the current transition index in the exercise phase sequence

        `HistoryDictKey.EXERCISE_START_TIME`:           The time when the session started
        `HistoryDictKey.EXERCISE_END_TIME`:             The time when the session ended
        `HistoryDictKey.EXERCISE_FINAL_DURATION`:       The total duration of the session
        `HistoryDictKey.PAUSE_SESSION_TIMESTAMP`:       The time when the session was paused
        `HistoryDictKey.PAUSES_DURATIONS`:              A counter for tracking total pause durations

        `HistoryDictKey.FRAMES_SINCE_LAST_FEEDBACK`:    A counter for tracking frames arrived since last feedback sent
        
        `HistoryDictKey.IS_CAMERA_STABLE`:              A `bool` indicating whether the camera is stable or not.
    }

    ### Frames (`list[dict]`):
    - One entry per **valid OK frame**.
    - Each entry contains: 

    {
        `HistoryDictKey.Frame.FRAME_ID`:  `int`,
        `HistoryDictKey.Frame.TIMESTAMP`: `datetime`,
        `HistoryDictKey.Frame.JOINTS`:    `dict[str, float]`
        `HistoryDictKey.Frame.ERRORS`:    `list[str]`
    }

    ### Last Valid Frame (`dict[str, Any]`):
    - Stores the last valid frame

    {
        `HistoryDictKey.Frame.FRAME_ID`:  `int`,
        `HistoryDictKey.Frame.TIMESTAMP`: `datetime`,
        `HistoryDictKey.Frame.JOINTS`:    `dict[str, float]`
        `HistoryDictKey.Frame.ERRORS`:    `list[str]`
    }

    - Used by:
        - `PhaseDetector` → compares angles across frames
        - `ErrorDetector` → continuity-based checks

    ### Consecutive Ok Frames (`int`):
    - Stores the amount of consecutive ok (valid) frames (where no bad frames arrived).

    ### Error Counters (`Dict[str, int]`):
    - Stores counters for errors detected (of valid frames).

    ### Error Streaks (`Dict[str, int]`):
    - Stores consecutive counters for errors detected (of valid frames).

    ### Low Motion Streak (`int`):
    - Stores the amount of consecutive low-motion frames.

    ### Phase State (`PhaseType`):
    - Tracks the current phase in the state machine (e.g., "down", "bottom", "up").
    - Only `PhaseDetector` updates this.
    - Used by:
        - `ErrorDetector` → errors depend on the phase
        - `FeedbackFormatter` → phase-specific coaching

    ### Phase Transitions (`dict[str, Any]`):
    - A `dict` for historical context of phase changes.
    - Each entry:

    {
        `HistoryDictKey.PhaseTransition.PHASE_FROM`: `PhaseType`,
        `HistoryDictKey.PhaseTransition.PHASE_TO`:    `PhaseType`,
        `HistoryDictKey.PhaseTransition.TIMESTAMP`:   `datetime`,
        `HistoryDictKey.PhaseTransition.FRAME_ID`:    `int`,
        `HistoryDictKey.PhaseTransition.JOINTS`:      `dict[str, float]`
    }

    ### Phase Durations (`dict[str, Any]`):
    - A `dict` for historical context of phase durations.
    - Each entry:

    {
        `HistoryDictKey.PhaseDuration.PHASE`: `PhaseType`,
        `HistoryDictKey.PhaseDuration.START_TIME`: `datetime`,
        `HistoryDictKey.PhaseDuration.END_TIME`: `datetime`,
        `HistoryDictKey.PhaseDuration.DURATION`: `float`,
        `HistoryDictKey.PhaseDuration.FRAME_START`: `int`,
        `HistoryDictKey.PhaseDuration.FRAME_END`: `int`
    }

    ### Initial Phase Counter (`int`):
    - An `int` which stores the number of consecutive frames where the user
    was positioned in the exercise's initial phase. Used for pre-analyzing logic
    by `PhaseDetector` and `SessionManager`.

    ### Bad Frame Counters (`dict[str, int]`):
    - A `dict` which stores counters of bad frames, classified to `PoseQuality` types.
    - When a valid frame recieved after some bad frames, the counters reset.

    ### Bad Frame Streaks (`dict[str, int]`):
    - A `dict` which stores consecutive counters for each bad frame type.

    ### Bad Frames Log (`list[dict]`):
    - A `list` that stores bad frames minimal information, in a `dict`:

    {
        `HistoryDictKey.BadFrame.FRAME_ID`:  `int`,
        `HistoryDictKey.BadFrame.TIMESTAMP`: `datetime`,
        `HistoryDictKey.BadFrame.REASON`:    `PoseQuality` element
    }

    ### Rep Count (`int`):
    - Used by:
        - Real-time feedback
        - Session summary
        - External interfaces

    ### Reptitions (`list[dict]`):
    - Each entry:

    {
        `HistoryDictKey.Repetition.START_TIME`: `datetime`,
        `HistoryDictKey.Repetition.END_TIME`: `datetime`,
        `HistoryDictKey.Repetition.DURATION`: `float`,
        `HistoryDictKey.Repetition.IS_CORRECT`: `bool`,
        `HistoryDictKey.Repetition.ERRORS`: `list[str]`
    }

    - Used for:
        - Summary screen
        - Tracking quality of every repetition
        - User progress analytics

    ### Current Rep (`dict[str, Any]`):
    - Each entry:

    {
        `HistoryDictKey.CurrentRep.START_TIME`: `datetime`,
        `HistoryDictKey.CurrentRep.HAS_ERROR`: `bool`,
        `HistoryDictKey.CurrentRep.ERRORS`: `list[str]`
    }

    ### Current Transition Index (`int`):
    - An `int` which stores the current transition index in the exercise phase sequence.

    ### Exercise Start Time (`datetime`):
    - Set when session starts.
    - Used for total duration and pacing analysis.

    ### Exercise End Time (`datetime`):
    - Set when session ends.
    - Used for calculating total exercise time.

    ### Exercise Final Duration (`float`):
    - The total duration of the session in seconds.

    ### Pause Session Timestamp (`datetime`):
    - The time when the session was paused.

    ### Pauses Durations (`float`):
    - A counter for tracking total pause durations.

    ### Frames Since Last Feedback (`int`):
    - A counter for tracking frames arrived since last feedback sent.

    ### Is Camera Stable (`bool`):
    - Indicates whether the camera is stable or not.
    """
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self):
        """
        ### Brief:
        The `__init__` method initializes the `HistoryData` instance.
        """
        self.history:Dict[str, Any] = {
            HistoryDictKey.FRAMES:                      [],
            HistoryDictKey.LAST_VALID_FRAME:            None,
            HistoryDictKey.CONSECUTIVE_OK_FRAMES:       0,
            HistoryDictKey.ERROR_COUNTERS:              {},
            HistoryDictKey.ERROR_STREAKS:               {},
            HistoryDictKey.LOW_MOTION_STREAK:           0,

            HistoryDictKey.PHASE_STATE:                 None,
            HistoryDictKey.PHASE_TRANSITIONS:           [],
            HistoryDictKey.PHASE_DURATIONS:             [],
            HistoryDictKey.INITIAL_PHASE_COUNTER:       0,

            HistoryDictKey.BAD_FRAME_COUNTERS:          { quality_enum.name: 0 for quality_enum in PoseQuality },
            HistoryDictKey.BAD_FRAME_STREAKS:           { quality_enum.name: 0 for quality_enum in PoseQuality },
            HistoryDictKey.BAD_FRAMES_LOG:              [],
            HistoryDictKey.FRAMES_SINCE_LAST_VALID:     0,

            HistoryDictKey.REP_COUNT:                   0,
            HistoryDictKey.REPETITIONS:                 [],
            HistoryDictKey.CURRENT_REP:                 None,
            HistoryDictKey.CURRENT_TRANSITION_INDEX:    0,

            HistoryDictKey.EXERCISE_START_TIME:         None,
            HistoryDictKey.EXERCISE_END_TIME:           None,
            HistoryDictKey.EXERCISE_FINAL_DURATION:     None,
            HistoryDictKey.PAUSE_SESSION_TIMESTAMP:     None,
            HistoryDictKey.PAUSES_DURATIONS:            0.0,

            HistoryDictKey.FRAMES_SINCE_LAST_FEEDBACK:  0,

            HistoryDictKey.IS_CAMERA_STABLE:            True
        }

    ####################################
    ### IS LAST FRAME ACTUALLY VALID ###
    ####################################
    def is_last_frame_actually_valid(self) -> bool:
        """
        ### Brief:
        The `is_last_frame_actually_valid` method returns whether the last valid frame is the actual
        last frame recieved.

        Used for the error detector to determine if it needs to detect errors or not.

        ### Returns:
        - `True` if the last valid frame is the actual last frame recieved.
        - `False` if not.
        """
        if len(self.history[HistoryDictKey.FRAMES]) == 0: return False
        if self.history[HistoryDictKey.LAST_VALID_FRAME] is None: return False
        last_valid_frame_id:int = self.history[HistoryDictKey.LAST_VALID_FRAME][HistoryDictKey.Frame.FRAME_ID]
        last_frames_element_id:int = self.history[HistoryDictKey.FRAMES][-1][HistoryDictKey.Frame.FRAME_ID]
        return last_valid_frame_id == last_frames_element_id
    
    ###################
    ### IS STATE OK ###
    ###################
    def is_state_ok(self) -> bool:
        """
        ### Brief:
        The `is_state_ok` method returns whether the current state is ok.
        Meaning: the camera state is stable - the amount of valid frames
        recieved is above the required threshold.

        ### Returns:
        - `True` if the state is ok.
        - `False` if the state is not ok.
        """
        return self.history[HistoryDictKey.IS_CAMERA_STABLE]

    ############################
    ### GET LAST VALID FRAME ###
    ############################
    def get_last_valid_frame(self) -> Optional[Dict[str, Any]]:
        """
        ### Brief:
        The `get_last_valid_frame` method returns the last valid frame `dict`.
        
        ### Returns:
        - A `dict` containing the last valid frame.
        """
        return self.history[HistoryDictKey.LAST_VALID_FRAME]
    
    #######################
    ### GET LAST ERRORS ###
    #######################
    def get_last_errors(self) -> Optional[list[str]]:
        """
        ### Brief:
        The `get_last_errors` method returns the errors list from the last valid frame.
        
        ### Returns:
        - A `list` containing the last errors list of the last valid frame.
        """
        if self.history[HistoryDictKey.LAST_VALID_FRAME] is None: return None
        else: return self.history[HistoryDictKey.LAST_VALID_FRAME][HistoryDictKey.Frame.ERRORS]

    ##########################
    ### GET ERROR COUNTERS ###
    ##########################
    def get_error_counters(self) -> Dict[str, int]:
        """
        ### Brief:
        The `get_error_counters` method returns the error counters `dict`.
        
        ### Returns:
        - A `Dict[str, int]` containing the error counters.
        """
        return self.history[HistoryDictKey.ERROR_COUNTERS]
    
    #########################
    ### GET ERROR STREAKS ###
    #########################
    def get_error_streaks(self) -> Dict[str, int]:
        """
        ### Brief:
        The `get_error_streaks` method returns the error streaks `dict`.
        
        ### Returns:
        - A `Dict[str, int]` containing the error streaks.
        """
        return self.history[HistoryDictKey.ERROR_STREAKS]
    
    #############################
    ### GET LOW MOTION STREAK ###
    #############################
    def get_low_motion_streak(self) -> int:
        """
        ### Brief:
        The `get_low_motion_streak` method returns the low motion streak counter.
        
        ### Returns:
        - An `int` containing the low motion streak counter.
        """
        return self.history[HistoryDictKey.LOW_MOTION_STREAK]

    #######################
    ### GET PHASE STATE ###
    #######################
    def get_phase_state(self) -> PhaseType | None:
        """
        ### Brief:
        The `get_phase_state` method returns the current phase state.
        
        ### Returns:
        - A `PhaseType` element of the current phase type.
        """
        return self.history[HistoryDictKey.PHASE_STATE]
    
    ##########################
    ### GET PREVIOUS PHASE ###
    ##########################
    def get_previous_phase(self) -> PhaseType | None:
        """
        ### Brief:
        The `get_previous_phase` method returns the previous phase state.
        
        ### Returns:
        - A `PhaseType` element of the previous phase type.

        ### Notes:
        - If `self.history[HistoryDictKey.PHASE_TRANSITIONS]` is `None`,
        meaning no transition has been made so far, returning `None`.
        """
        transitions = self.history[HistoryDictKey.PHASE_TRANSITIONS]
        if transitions is None or transitions == []: return None
        else: return transitions[-1][HistoryDictKey.PhaseTransition.PHASE_TO]
    
    #################################
    ### GET LAST PHASE TRANSITION ###
    #################################
    def get_last_phase_transition(self) -> Dict[str, Any]:
        """
        ### Brief:
        The `get_last_phase_transition` method returns the last phase transition.
        
        ### Returns:
        - A `Dict[str, Any]` containing info about the last transition (`HistoryDictKey.PhaseTransition`).
        """
        transitions:list = self.history[HistoryDictKey.PHASE_TRANSITIONS]
        return transitions[-1] if transitions else None
    
    #####################################
    ### GET PHASE TRANSITIONS HISTORY ###
    #####################################
    def get_phase_transitions_history(self) -> list:
        """
        ### Brief:
        The `get_phase_transitions_history` method returns the list of phase transitions.
        
        ### Returns:
        - A `list[Dict[str, Any]]` containing info about the all transition history (`HistoryDictKey.PhaseTransition`).
        """
        return deepcopy(self.history[HistoryDictKey.PHASE_TRANSITIONS])
    
    ###############################
    ### GET LAST PHASE DURATION ###
    ###############################
    def get_last_phase_duration(self) -> Dict[str, Any]:
        """
        ### Brief:
        The `get_last_phase_duration` method returns the last phase duration.
        
        ### Returns:
        - A `Dict[str, Any]` containing info about the last duration (`HistoryDictKey.PhaseDuration`).
        """
        transitions:list = self.history[HistoryDictKey.PHASE_DURATIONS]
        return transitions[-1] if transitions else None
    
    ###################################
    ### GET PHASE DURATIONS HISTORY ###
    ###################################
    def get_phase_durations_history(self) -> list:
        """
        ### Brief:
        The `get_phase_durations_history` method returns the list of phase durations.
        
        ### Returns:
        - A `list[Dict[str, Any]]` containing info about the all phase durations history (`HistoryDictKey.PhaseDuration`).
        """
        return deepcopy(self.history[HistoryDictKey.PHASE_DURATIONS])
    
    #################################
    ### GET INITIAL PHASE COUNTER ###
    #################################
    def get_initial_phase_counter(self) -> int:
        """
        ### Brief:
        The `get_initial_phase_counter` method returns the counter of correct initial phase.
        
        ### Returns:
        - An `int` which stores the counter of correct initial phase.
        """
        return self.history[HistoryDictKey.INITIAL_PHASE_COUNTER]

    #####################
    ### GET REP COUNT ###
    #####################
    def get_rep_count(self) -> int:
        """
        ### Brief:
        The `get_rep_count` method returns the number of completed repetitions.
        
        ### Returns:
        An `int` indicating the number of completed repetitions.
        """
        return self.history[HistoryDictKey.REP_COUNT]

    #######################
    ### GET REP HISTORY ###
    #######################
    def get_rep_history(self) -> List[Dict[str, Any]]:
        """
        ### Brief:
        The `get_rep_history` method returns detailed rep history.
        
        ### Returns:
        A `list` containing the completed repetitions.
        """
        return deepcopy(self.history[HistoryDictKey.REPETITIONS])

    ######################
    ### GET ALL FRAMES ###
    ######################
    def get_all_frames(self) -> List[Dict[str, Any]]:
        """
        ### Brief:
        The `get_all_frames` method returns the list of all valid frames so far,
        under the predefined rolling window size (which stored in `self.frames_rolling_window_size`).

        ### Returns:
        A `list` of all valid frames.
        """
        return deepcopy(self.history[HistoryDictKey.FRAMES])
    
    ###################################
    ### GET FRAMES SINCE LAST VALID ###
    ###################################
    def get_frames_since_last_valid(self) -> int:
        """
        ### Brief:
        The `get_frames_since_last_valid` method returns the number of frames since the last valid one.

        ### Returns:
        An `int` indicating the number of frames since the last valid one.
        """
        return self.history[HistoryDictKey.FRAMES_SINCE_LAST_VALID]

    ##############################
    ### GET BAD FRAME COUNTERS ###
    ##############################
    def get_bad_frame_counters(self) -> Dict[str, int]:
        """
        ### Brief:
        The `get_bad_frame_counters` method returns the counters of bad frames.

        ### Returns:
        A `dict` containing counters per bad-frame type, based on `PoseQuality`.
        """
        return self.history[HistoryDictKey.BAD_FRAME_COUNTERS]
    
    #############################
    ### GET BAD FRAME STREAKS ###
    #############################
    def get_bad_frame_streaks(self) -> Dict[str, int]:
        """
        ### Brief:
        The `get_bad_frame_streaks` method returns the streaks of bad frames.

        ### Returns:
        A `dict` containing streaks per bad-frame type, based on `PoseQuality`.
        """
        return self.history[HistoryDictKey.BAD_FRAME_STREAKS]
    
    #################################
    ### GET CONSECUTIVE OK STREAK ###
    #################################
    def get_consecutive_ok_streak(self) -> int:
        """
        ### Brief:
        The `get_consecutive_ok_streak` method returns the number of consecutive `OK` frames.

        ### Returns:
        An `int` indicating the number of consecutive `OK` frames.
        """
        return self.history[HistoryDictKey.CONSECUTIVE_OK_FRAMES]
    
    ######################################
    ### GET FRAMES SINCE LAST FEEDBACK ###
    ######################################
    def get_frames_since_last_feedback(self) -> int:
        """
        ### Brief:
        The `get_frames_since_last_feedback` method returns the number of frames since the last feedback sent.

        ### Returns:
        An `int` indicating the number of frames since the last feedback sent.
        """
        return self.history[HistoryDictKey.FRAMES_SINCE_LAST_FEEDBACK]

    #############################
    ### GET EXERCISE DURATION ###
    #############################
    def get_exercise_duration(self) -> Optional[float]:
        """
        ### Brief:
        The `get_exercise_duration` method returns the total exercise duration.

        ### Returns:
        A `float` indicating the total exercise duration in seconds.
        """
        return self.history[HistoryDictKey.EXERCISE_FINAL_DURATION]
    
    ###############################
    ### PAUSE SESSION TIMESTAMP ###
    ###############################
    def get_pause_session_timestamp(self) -> Optional[datetime]:
        """
        ### Brief:
        The `get_pause_session_timestamp` method returns the pause session timestamp.

        ### Returns:
        A `datetime` indicating the pause session timestamp.
        """
        return self.history[HistoryDictKey.PAUSE_SESSION_TIMESTAMP]
    
    ############################
    ### GET PAUSES DURATIONS ###
    ############################
    def get_pauses_durations(self) -> float:
        """
        ### Brief:
        The `get_pauses_durations` method returns the total pauses durations.

        ### Returns:
        A `float` indicating the total pauses durations in seconds.
        """
        return self.history[HistoryDictKey.PAUSES_DURATIONS]
    
    ####################################
    ### GET CURRENT TRANSITION INDEX ###
    ####################################
    def get_current_transition_index(self) -> int:
        """
        ### Brief:
        The `get_current_transition_index` method returns the current transition
        index in the exercise phase sequence.

        ### Returns:
        An `int` indicating the current transition index.
        """
        return self.history[HistoryDictKey.CURRENT_TRANSITION_INDEX]