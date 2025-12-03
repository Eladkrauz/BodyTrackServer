############################################################
######### BODY TRACK // SERVER // DATA // HISTORY ##########
############################################################
################# CLASS: HistoryDictKey ####################
############################################################

#############################
### HISTORY MANAGER CLASS ###
#############################
class HistoryDictKey:
    # Valid frames.
    FRAMES                  = "frames"
    LAST_VALID_FRAME        = "last_valid_frame"
    CONSECUTIVE_OK_FRAMES   = "consecutive_ok_frames"
    ERROR_COUNTERS          = "error_counters"
    # Phase.
    PHASE_STATE             = "phase_state"
    PHASE_START_TIME        = "phase_start_time"
    PHASE_TRANSITIONS       = "phase_transitions"
    PHASE_DURATIONS         = "phase_durations"
    INITIAL_PHASE_COUNTER   = "initial_phase_counter"
    # Bad frames.
    BAD_FRAME_COUNTERS      = "bad_frame_counters"
    BAD_FRAME_STREAKS       = "bad_frame_streaks"
    BAD_FRAMES_LOG          = "bad_frames_log"
    FRAMES_SINCE_LAST_VALID = "frames_since_last_valid"
    # Repetitions.
    REP_COUNT               = "rep_count"
    REPETITIONS             = "repetitions"
    CURRENT_REP             = "current_rep"
    # Timestamps.
    EXERCISE_START_TIME     = "exercise_start_time"
    EXERCISE_END_TIME       = "exercise_end_time"
    # Others.
    IS_CAMERA_STABLE        = "is_camera_stable"

    #############
    ### FRAME ###
    #############
    class Frame:
        FRAME_ID  = "frame_id"
        TIMESTAMP = "timestamp"
        JOINTS    = "joints"
        ERRORS    = "errors"

    #################
    ### BAD FRAME ###
    #################
    class BadFrame:
        FRAME_ID  = "frame_id"
        TIMESTAMP = "timestamp"
        REASON    = "reason"

    ###################
    ### CURRENT REP ###
    ###################
    class CurrentRep:
        START_TIME = "start_time"
        HAS_ERROR  = "has_error"
        ERRORS     = "errors"

    ##################
    ### REPETITION ###
    ##################
    class Repetition:
        START_TIME = "start_time"
        END_TIME   = "end_time"
        DURATION   = "duration"
        IS_CORRECT = "is_correct"
        ERRORS     = "errors"

    ########################
    ### PHASE TRANSITION ###
    ########################
    class PhaseTransition:
        PHASE_FROM = "phase_from"
        PHASE_TO   = "phase_to"
        TIMESTAMP  = "timestamp"
        FRAME_ID   = "frame_id"
        JOINTS     = "joints"

    ######################
    ### PHASE DURATION ###
    ######################
    class PhaseDuration:
        PHASE       = "phase"
        START_TIME  = "start_time"
        END_TIME    = "end_time"
        DURATION    = "duration"
        FRAME_START = "frame_start"
        FRAME_END   = "frame_end"

    ###############
    ### SUMMARY ###
    ###############
    class Summary:
        TOTAL_DURATION  = "total_duration"
        TOTAL_REP_COUNT = "total_rep_count"
        REPS_HISTORY    = "reps_history"