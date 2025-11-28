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
    - `FeedbackManager`
    - `RepCounter`
    - Final summary statistics / analytics

    ### Stored Elements:

    {
        `HistoryDictKey.FRAMES`:                  A `list` of Frame dictionaries
        `HistoryDictKey.LAST_VALID_FRAME`:        A `dict` which holds the last valid frame
        `HistoryDictKey.CONSECUTIVE_OK_FRAMES`:   An `int` which holds the number of consecutive OK frames

        `HistoryDictKey.PHASE_STATE`:             The current exercise phase (`PhaseType` enum element)
        'HistoryDictKey.PHASE_START_TIME`:        The time when the phase started
        `HistoryDictKey.PHASE_TRANSITIONS`:       A `dict` for historical context of phase changes
        `HistoryDictKey.PHASE_DURATIONS`:         A `dict` for historical context of phase durations

        `HistoryDictKey.BAD_FRAME_COUNTERS`:      A `dict` containing counters for bad frames
        `HistoryDictKey.BAD_FRAME_STREAKS`:       A `dict` containing consecutive counters for bad frames
        `HistoryDictKey.BAD_FRAMES_LOG`:          A `list` that stores minimal info about bad frames
        `HistoryDictKey.FRAMES_SINCE_LAST_VALID`: A counter for tracking the gap between valid frames

        `HistoryDictKey.REP_COUNT`:               A counter for tracking amount of repetitions
        `HistoryDictKey.REPETITIONS`:             A `list` that stores finished repetitions
        `HistoryDictKey.CURRENT_REP`:             A `dict` which stores current repetition info

        `HistoryDictKey.EXERCISE_START_TIME`:     The time when the session started
        `HistoryDictKey.EXERCISE_END_TIME`:       The time when the session ended
        
        `HistoryDictKey.IS_CAMERA_STABLE`:        A `bool` indicating whether the camera is stable or not.
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
        - `RepCounter` → angle trend-based detection

    ### Consecutive Ok Frames (`int`):
    - Stores the amount of consecutive ok (valid) frames (where no bad frames arrived).

    ### Phase State (`PhaseType`):
    - Tracks the current phase in the state machine (e.g., "down", "bottom", "up").
    - Only `PhaseDetector` updates this.
    - Used by:
        - `ErrorDetector` → errors depend on the phase
        - `RepCounter` → phase transitions mark rep boundaries
        - `FeedbackManager` → phase-specific coaching

    ### Phase Start Time (`datetime`):
    - Tracks the current phase start time.

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
    - Updated by `RepCounter` when a repetition is completed.
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

    ### Exercise Start Time (`datetime`):
    - Set when session starts.
    - Used for total duration and pacing analysis.

    ### Exercise End Time (`datetime`):
    - Set when session ends.
    - Used for calculating total exercise time.

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
            HistoryDictKey.FRAMES:                  [],
            HistoryDictKey.LAST_VALID_FRAME:        None,
            HistoryDictKey.CONSECUTIVE_OK_FRAMES:   0,

            HistoryDictKey.PHASE_STATE:             None,
            HistoryDictKey.PHASE_START_TIME:        None,
            HistoryDictKey.PHASE_TRANSITIONS:       [],
            HistoryDictKey.PHASE_DURATIONS:         [],

            HistoryDictKey.BAD_FRAME_COUNTERS:      { quality_enum.name: 0 for quality_enum in PoseQuality },
            HistoryDictKey.BAD_FRAME_STREAKS:       { quality_enum.name: 0 for quality_enum in PoseQuality },
            HistoryDictKey.BAD_FRAMES_LOG:          [],
            HistoryDictKey.FRAMES_SINCE_LAST_VALID: 0,

            HistoryDictKey.REP_COUNT:               0,
            HistoryDictKey.REPETITIONS:             [],
            HistoryDictKey.CURRENT_REP:             None,

            HistoryDictKey.EXERCISE_START_TIME:     None,
            HistoryDictKey.EXERCISE_END_TIME:       None,

            HistoryDictKey.IS_CAMERA_STABLE:        True
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
        last_valid_frame_id:int = self.history[HistoryDictKey.LAST_VALID_FRAME][HistoryDictKey.Frame.FRAME_ID]
        last_frames_element_id:int = self.history[HistoryDictKey.FRAMES][-1][HistoryDictKey.Frame.FRAME_ID]
        return last_valid_frame_id == last_frames_element_id

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

    #######################
    ### GET PHASE STATE ###
    #######################
    def get_phase_state(self) -> PhaseType:
        """
        ### Brief:
        The `get_phase_state` method returns the current phase state.
        
        ### Returns:
        - A `PhaseType` element of the current phase type.
        """
        return self.history[HistoryDictKey.PHASE_STATE]
    
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
    
    ############################
    ### GET IF CAMERA STABLE ###
    ############################
    def get_if_camera_stable(self) -> bool:
        """
        ### Brief:
        The `get_if_camera_stable` method returns whether the camera is stable or not.

        ### Returns:
        A `bool` indicating whether the camera is stable or not.
        """
        return self.history[HistoryDictKey.IS_CAMERA_STABLE]

    ###################
    ### GET SUMMARY ###
    ###################
    def get_summary(self) -> Dict[str, Any]:
        """
        ### Brief:
        The `get_summary` method returns a compact summary of the entire session.
        Useful for final exercise reporting.

        ### Returns:
        A `dict` containing a summary of the entire session
        """
        start_time:datetime = self.history[HistoryDictKey.EXERCISE_START_TIME]
        end_time:datetime   = self.history[HistoryDictKey.EXERCISE_END_TIME]

        # Calculating entire session time.
        if start_time and end_time: total_time = (end_time - start_time).total_seconds()
        else:                       total_time = None

        return {
            HistoryDictKey.Summary.TOTAL_DURATION:  total_time,
            HistoryDictKey.Summary.TOTAL_REP_COUNT: self.history[HistoryDictKey.REP_COUNT],
            HistoryDictKey.Summary.REPS_HISTORY:    self.history[HistoryDictKey.REPETITIONS]
        }