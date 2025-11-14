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
        TASKS         = "tasks"
        LOG           = "log"
        JOINTS        = "joints"
        
    class Minor(enum):
        # Communication.
        PORT = "port"
        HOST = "host"
        TIMEOUT_SECONDS = "timeout_seconds"

        # Frame.
        HEIGHT = "height"
        WIDTH = "width"

        # Session.
        SUPPORTED_EXERCIES = "supported_exercises"
        MAXIMUM_CLIENTS = "maximum_clients"

        # Tasks.
        CLEANUP_INTERVAL_MINUTES = "cleanup_interval_minutes"
        MAX_REGISTRATION_MINUTES = "max_registration_minutes"
        MAX_INACTIVE_MINUTS = "max_inactive_minutes"
        MAX_PAUSE_MINUTES = "max_pause_minutes"
        MAX_ENDED_RETENTION = "max_ended_retention"
  
        # Log.
        LOGGER_PATH = "logger_path"
        LOGGER_NAME = "logger_name"
        ARCHIVE_DIR_NAME = "archive_dir_name"
        LOG_LEVEL = "log_level"

        # Joints.
        VISIBILITY_THRESHOLD = "visibility_threshold"
        MIN_VALID_JOINT_RATIO = "min_valid_joint_ratio"