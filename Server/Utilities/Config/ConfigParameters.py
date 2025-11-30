############################################################
####### BODY TRACK // SERVER // UTILITIES // CONFIG ########
############################################################
################# CLASS: ConfigParameters ##################
############################################################

###############
### IMPORTS ###
###############
from enum import Enum as enum

###############################
### CONFIG PARAMETERS CLASS ###
###############################
class ConfigParameters:
    """
    ### Description:
    The `ConfigParameters` enum class represents all the server configuration parameters, as described in the configuration file.
    """
    class Major(enum):
        COMMUNICATION = "communication"
        FRAME         = "frame"
        SESSION       = "session"
        HISTORY       = "history"
        TASKS         = "tasks"
        LOG           = "log"
        POSE          = "pose"
        JOINTS        = "joints"
        
    class Minor(enum):
        # Communication.
        PORT            = "port"
        HOST            = "host"
        TIMEOUT_SECONDS = "timeout_seconds"

        # Frame.
        HEIGHT  = "height"
        WIDTH   = "width"

        # Session.
        SUPPORTED_EXERCIES        = "supported_exercises"
        MAXIMUM_CLIENTS           = "maximum_clients"
        NUM_OF_MIN_INIT_OK_FRAMES = "num_of_min_init_ok_frames"

        # History.
        FRAMES_ROLLING_WINDOW_SIZE           = "frames_rolling_window_size"
        BAD_FRAME_LOG_SIZE                   = "bad_frame_log_size"
        RECOVERY_OK_THRESHOLD                = "recovery_ok_threshold"
        BAD_STABILITY_LIMIT                  = "bad_stability_limit"
        MAX_CONSECUTIVE_INVALID_BEFORE_ABORT = "max_consecutive_invalid_before_abort"

        # Tasks.
        CLEANUP_INTERVAL_MINUTES       = "cleanup_interval_minutes"
        MAX_REGISTRATION_MINUTES       = "max_registration_minutes"
        MAX_INACTIVE_MINUTS            = "max_inactive_minutes"
        MAX_PAUSE_MINUTES              = "max_pause_minutes"
        MAX_ENDED_RETENTION            = "max_ended_retention"
        RETRIEVE_CONFIGURATION_MINUTES = "retrieve_configuration_minutes"
  
        # Log.
        LOGGER_PATH         = "logger_path"
        LOGGER_NAME         = "logger_name"
        ARCHIVE_DIR_NAME    = "archive_dir_name"
        LOG_LEVEL           = "log_level"

        # Pose.
        STABILITY_THRESHOLD     = "stability_threshold"
        BBOX_TOO_FAR            = "bbox_too_far"
        BBOX_TOO_CLOSE          = "bbox_too_close"
        MEAN_VIS_THRESHOLD      = "mean_vis_threshold"
        PARTIAL_COUNT_THRESHOLD = "partial_count_threshold"
        MINIMUM_BBOX_AREA       = "minimum_bbox_area"

        # Joints.
        VISIBILITY_THRESHOLD    = "visibility_threshold"
        MIN_VALID_JOINT_RATIO   = "min_valid_joint_ratio"