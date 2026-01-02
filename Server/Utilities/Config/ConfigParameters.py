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
    The `ConfigParameters` enum class represents all the server configuration parameters,
    as described in the configuration file.
    """
    class Major(enum):
        """
        ### Description:
        The `Major` enum class represents the major sections of the server configuration file.
        """
        COMMUNICATION                           = "communication"
        FRAME                                   = "frame"
        SESSION                                 = "session"
        HISTORY                                 = "history"
        TASKS                                   = "tasks"
        LOG                                     = "log"
        POSE                                    = "pose"
        POSITION_SIDE                           = "position_side"
        JOINTS                                  = "joints"
        ERROR                                   = "error"
        PHASE                                   = "phase"
        FEEDBACK                                = "feedback"
        SUMMARY                                 = "summary"
        
    class Minor(enum):
        """
        ### Description:
        The `Minor` enum class represents the minor (individual) configuration parameters.
        """
        #####################
        ### COMMUNICATION ###
        #####################
        # The port number for server communication.
        PORT                                    = "port"
        # The host address for server communication.
        HOST                                    = "host"
        # The timeout in seconds for client connections.
        TIMEOUT_SECONDS                         = "timeout_seconds"

        #############
        ### FRAME ###
        #############
        # The height of the input frames.
        HEIGHT                                  = "height"
        # The width of the input frames.
        WIDTH                                   = "width"

        ###############
        ### SESSION ###
        ###############
        # Supported exercies.
        SUPPORTED_EXERCIES                      = "supported_exercises"
        # Maximum number of clients in active state.
        MAXIMUM_CLIENTS                         = "maximum_clients"
        # Minimum number of consecutive valid frames to initialize the session.
        NUM_OF_MIN_INIT_OK_FRAMES               = "num_of_min_init_ok_frames"
        # Minimum number of consecutive correct phase frames to initialize the session.
        NUM_OF_MIN_INIT_CORRECT_PHASE           = "num_of_min_init_correct_phase"

        ###############
        ### HISTORY ###
        ###############
        # The number of frames to keep in history.
        FRAMES_ROLLING_WINDOW_SIZE              = "frames_rolling_window_size"
        # The size of the bad frames log.
        BAD_FRAME_LOG_SIZE                      = "bad_frame_log_size"
        # The threshold of consecutive valid frames to consider recovery from a bad state.
        RECOVERY_OK_THRESHOLD                   = "recovery_ok_threshold"
        # The limit of bad stability frames before marking the camera as unstable.
        BAD_STABILITY_LIMIT                     = "bad_stability_limit"
        # The maximum number of consecutive invalid frames before aborting the session.
        MAX_CONSECUTIVE_INVALID_BEFORE_ABORT    = "max_consecutive_invalid_before_abort"
        # The angle in degrees below which motion is considered low.
        LOW_MOTION_ANGLE_DEGREES_THRESHOLD      = "low_motion_angle_degrees_threshold"

        #############
        ### TASKS ###
        #############
        # The interval in minutes for cleanup tasks.
        CLEANUP_INTERVAL_MINUTES                = "cleanup_interval_minutes"
        # The maximum registration time in minutes for a client.
        MAX_REGISTRATION_MINUTES                = "max_registration_minutes"
        # The maximum inactivity time in minutes for a client.
        MAX_INACTIVE_MINUTS                     = "max_inactive_minutes"
        # The maximum pause time in minutes for a client.
        MAX_PAUSE_MINUTES                       = "max_pause_minutes"
        # The maximum ended session retention time in minutes.
        MAX_ENDED_RETENTION                     = "max_ended_retention"
        # The interval in minutes for retrieving configuration updates.
        RETRIEVE_CONFIGURATION_MINUTES          = "retrieve_configuration_minutes"
  
        ###########
        ### LOG ###
        ###########
        # The path to the log directory.
        LOGGER_PATH                             = "logger_path"
        # The name of the logger file.
        LOGGER_NAME                             = "logger_name"
        # The name of the archive directory.
        ARCHIVE_DIR_NAME                        = "archive_dir_name"
        # The log level.
        LOG_LEVEL                               = "log_level"
        # The name of the debug directory.
        DEBUG_DIR_NAME                          = "debug_dir_name"

        ############
        ### POSE ###
        ############
        # The stability threshold for pose detection.
        STABILITY_THRESHOLD                     = "stability_threshold"
        # The maximum distance thresholds for bounding box size.
        BBOX_TOO_FAR                            = "bbox_too_far"
        # The minimum bounding box area.
        MINIMUM_BBOX_AREA                       = "minimum_bbox_area"
        # The required visibility threshold for pose landmarks.
        VISIBILITY_GOOD_THRESHOLD               = "visibility_good_threshold"
        # The required visibility ratio for valid pose.
        REQUIRED_VISIBILITY_RATIO               = "required_visibility_ratio"

        #####################
        ### POSITION SIDE ###
        #####################
        # The threshold for determining left/right/front position side.
        LANDMARK_VISIBILITY_THRESHOLD           = "landmark_visibility_threshold"
        # The ratio threshold for dominance of one side.
        DOMINANCE_RATIO_THRESHOLD               = "dominance_ratio_threshold"
        # The threshold for front symmetry.
        FRONT_SYMMETRY_THRESHOLD                = "front_symmetry_threshold"
        # The minimum required landmark ratio.
        MIN_REQUIRED_LANDMARK_RATIO             = "min_required_landmark_ratio"

        ##############
        ### JOINTS ###
        ##############
        # The visibility threshold for joints.
        VISIBILITY_THRESHOLD                    = "visibility_threshold"
        # The minimum required joints for a valid frame.
        MIN_VALID_JOINT_RATIO                   = "min_valid_joint_ratio"

        #############
        ### ERROR ###
        #############
        # The path to the error detector configuration file.
        ERROR_DETECTOR_CONFIG_FILE              = "error_thresholds_config_file"

        #############
        ### PHASE ###
        #############
        # The path to the phase detector configuration file.
        PHASE_DETECTOR_CONFIG_FILE              = "phase_thresholds_config_file"
        # The motion threshold to consider a phase as low motion.
        PHASE_LOW_MOTION_THRESHOLD              = "phase_low_motion_threshold"

        ################
        ### FEEDBACK ###
        ################
        # The pose quality feedback threshold.
        POSE_QUALITY_FEEDBACK_THRESHOLD         = "pose_quality_feedback_threshold"
        # The biomechanical feedback threshold.
        BIO_FEEDBACK_THRESHOLD                  = "biomechanical_feedback_threshold"
        # The cooldown frames between feedbacks.
        FEEDBACK_COOLDOWN_FRAMES                = "feedback_cooldown_frames"

        ###############
        ### SUMMARY ###
        ###############
        # The number of top errors to include in the summary.
        NUMBER_OF_TOP_ERRORS                    = "number_of_top_errors"
        # The maximum grade achievable.
        MAX_GRADE                               = "max_grade"