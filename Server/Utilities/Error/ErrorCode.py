############################################################
####### BODY TRACK // SERVER // UTILITIES // ERROR #########
############################################################
##################### CLASS: ErrorCode #####################
############################################################

###############
### IMPORTS ###
###############
from enum import IntEnum
from enum import auto
from typing import Dict, Any, Optional
from dataclasses import dataclass

#################################
### ERROR RESPONSE DICT ALIAS ###
#################################
ErrorResponseDict = Dict[str, Any]

########################
### ERROR CODE CLASS ###
########################
class ErrorCode(IntEnum):
    """
    ### Description:
    An enum class representing error codes.
    """
    _ignore_ = (
        "_error_descriptions",
        "_extra_info",
        "_critical_errors",
    )

    # Configuration and management.
    CANT_CONFIGURE_LOG                       = auto()
    CONFIGURATION_FILE_DOES_NOT_EXIST        = auto()
    JSON_FILE_DECODE_ERROR                   = auto()
    JSON_FILE_UNICODE_ERROR                  = auto()
    CONFIG_PARAM_DOES_NOT_EXIST              = auto()
    CRITICAL_CONFIG_PARAM_DOES_NOT_EXIST     = auto()
    CONFIGURATION_KEY_IS_INVALID             = auto()
    INVALID_JSON_PAYLOAD_IN_REQUEST          = auto()
    MISSING_EXERCISE_TYPE_IN_REQUEST         = auto()
    MISSING_SESSION_ID_IN_REQUEST            = auto()
    MISSING_FRAME_DATA_IN_REQUEST            = auto()
    CLIENT_IP_IS_INVALID                     = auto()
    CLIENT_AGENT_IS_INVALID                  = auto()
    JSON_CONFIG_FILE_ERROR                   = auto()
    INTERNAL_SERVER_ERROR                    = auto()

    # Flask and database management.
    CANT_ADD_URL_RULE_TO_FLASK_SERVER        = auto()
    UNRECOGNIZED_ICD_ERROR_TYPE              = auto()
    UNRECOGNIZED_ICD_RESPONSE_TYPE           = auto()
    DATABASE_CONNECTION_FAILED               = auto()
    DATABASE_SCHEMA_CREATION_FAILED          = auto()
    USER_ALREADY_EXISTS                      = auto()
    DATABASE_INSERT_FAILED                   = auto()
    DATABASE_QUERY_FAILED                    = auto()
    DATABASE_UPDATE_FAILED                   = auto()
    DATABASE_DELETE_FAILED                   = auto()
    USER_INVALID_CREDENTIALS                 = auto()
    USER_IS_ALREADY_LOGGED_IN                = auto()
    USER_IS_NOT_LOGGED_IN                    = auto()
    USER_NOT_FOUND                           = auto()
    FRAME_DECODING_FAILED                    = auto()
    TERMINATION_INCORRECT_PASSWORD           = auto()

    # Session Manager.  
    EXERCISE_TYPE_DOES_NOT_EXIST             = auto()
    ERROR_GENERATING_SESSION_ID              = auto()
    MAX_CLIENT_REACHED                       = auto()
    INVALID_SESSION_ID                       = auto()
    CLIENT_IS_NOT_REGISTERED                 = auto()
    CLIENT_IS_ALREADY_REGISTERED             = auto()
    CLIENT_IS_NOT_ACTIVE                     = auto()
    CLIENT_IS_ALREADY_ACTIVE                 = auto()
    CLIENT_IS_NOT_PAUSED                     = auto()
    CLIENT_IS_ALREADY_PAUSED                 = auto()
    CLIENT_IS_NOT_ENDED                      = auto()
    CLIENT_IS_ALREADY_ENDED                  = auto()
    CLIENT_IS_ONLY_REGISTERED                = auto()
    SEARCH_TYPE_IS_NOT_SUPPORTED             = auto()
    SESSION_STATUS_IS_NOT_RECOGNIZED         = auto()
    FRAME_INITIAL_VALIDATION_FAILED          = auto()
    INVALID_EXTENDED_EVALUATION_PARAM        = auto()
    TRYING_TO_ANALYZE_FRAME_WHEN_DONE        = auto()
    TRYING_TO_ANALYZE_FRAME_WHEN_FAILED      = auto()
    ERROR_CREATING_SESSION_DATA              = auto()
    SESSION_SHOULD_ABORT                     = auto()
    CLIENT_NOT_IN_SYSTEM                     = auto()

    # PoseAnalyzer.
    ERROR_INITIALIZING_POSE                  = auto()
    FRAME_PREPROCESSING_ERROR                = auto()
    FRAME_VALIDATION_ERROR                   = auto()
    FRAME_ANALYSIS_ERROR                     = auto()

    # JointAnalyzer.
    VECTOR_VALIDATION_FAILED                 = auto()
    ANGLE_VALIDATION_FAILED                  = auto()
    ANGLE_CALCULATION_FAILED                 = auto()
    JOINT_CALCULATION_ERROR                  = auto()
    DIMENSION_OF_ANGLE_IS_INVALID            = auto()
    TOO_MANY_INVALID_ANGLES                  = auto()
    CANT_CALCULATE_JOINTS_OF_UNSTALBE_FRAME  = auto()
    ANGLES_DICTIONARY_IS_EMPTY               = auto()

    # HistoryManager.
    HISTORY_MANAGER_INIT_ERROR               = auto()
    EXERCISE_START_TIME_ALREADY_SET          = auto()
    EXERCISE_END_TIME_ALREADY_SET            = auto()
    HISTORY_MANAGER_INTERNAL_ERROR           = auto()
    TRIED_TO_ADD_ERROR_TO_NONE_REP           = auto()
    TRIED_TO_END_A_NONE_REP                  = auto()
    TRIED_TO_START_REP_WHILE_HAVE_ONE        = auto()
    ERROR_WITH_HANDLING_FRAMES_LIST          = auto()
    CANT_FIND_FRAME_IN_FRAMES_WINDOW         = auto()
    LAST_VALID_FRAME_IS_NONE                 = auto()
    ERROR_WITH_HANDLING_BAD_FRAMES_LIST      = auto()

    # PoseQualityManager.
    FAILED_TO_INITIALIZE_QUALITY_MANAGER     = auto()
    QUALITY_CHECKING_ERROR                   = auto()
    NO_PERSON_DETECTED_IN_FRAME              = auto()
    PARTIAL_BODY_IN_FRAME                    = auto()
    TOO_FAR_IN_FRAME                         = auto()
    UNSTABLE_IN_FRAME                        = auto()
    LAST_VALID_FRAME_MISSING                 = auto()

    # ErrorDetector.
    ERROR_DETECTOR_INVALID_ANGLE             = auto()
    ERROR_DETECTOR_MISSING_THRESHOLD         = auto()
    ERROR_DETECTOR_MAPPING_NOT_FOUND         = auto()
    ERROR_DETECTOR_UNSUPPORTED_PHASE         = auto()
    ERROR_DETECTOR_INIT_ERROR                = auto()
    ERROR_DETECTOR_CONFIG_ERROR              = auto()

    # PhaseDetector.
    PHASE_THRESHOLDS_CONFIG_FILE_ERROR       = auto()
    NO_VALID_FRAME_DATA_IN_SESSION           = auto()
    PHASE_UNDETERMINED_IN_FRAME              = auto()
    TRIED_TO_DETECT_FRAME_FOR_UNSTABLE_STATE = auto()
    PHASE_IS_NONE_IN_FRAME                   = auto()

    # FeedbackFormatter.
    FEEDBACK_FORMATTER_INIT_ERROR            = auto()
    FEEDBACK_CONSTRUCTION_ERROR              = auto()
    POSE_QUALITY_FEEDBACK_SELECTION_ERROR    = auto()
    BIOMECHANICAL_FEEDBACK_SELECTION_ERROR   = auto()
    FEEDBACK_CONFIG_RETRIEVAL_ERROR          = auto()

    # SessionSummaryManager.
    SUMMARY_MANAGER_INIT_ERROR               = auto()
    SUMMARY_MANAGER_CREATE_ERROR             = auto()
    SUMMARY_MANAGER_INTERNAL_ERROR           = auto()

    # PositionSideDetector.
    FAILED_TO_INITIALIZE_SIDE_DETECTOR       = auto()
    POSITION_SIDE_DETECTION_ERROR            = auto()
    WRONG_EXERCISE_POSITION                  = auto()
    POSITION_SIDE_DOES_NOT_EXIST             = auto()

    @property
    def description(self) -> str:
        return _error_descriptions[self]

    @property
    def extra_info(self) -> Optional[Dict[str, Any]]:
        return _extra_info.get(self)

    @property
    def is_critical(self) -> bool:
        return self in _critical_errors
    
_error_descriptions = {
    # Configuration and management.
    ErrorCode.CANT_CONFIGURE_LOG:                       "Logger can't get configured.",
    ErrorCode.CONFIGURATION_FILE_DOES_NOT_EXIST:        "Configuration file does not exist.",
    ErrorCode.JSON_FILE_DECODE_ERROR:                   "Error parsing the configuration JSON file.",
    ErrorCode.JSON_FILE_UNICODE_ERROR:                  "Error parsing the configuration JSON file.",
    ErrorCode.CONFIG_PARAM_DOES_NOT_EXIST:              "The key sent does not exist in the configuration file.",
    ErrorCode.CRITICAL_CONFIG_PARAM_DOES_NOT_EXIST:     "The key sent does not exist in the configuration file. Critical.",
    ErrorCode.CONFIGURATION_KEY_IS_INVALID:             "The key sent is not a valid list of ConfigParameters",
    ErrorCode.INVALID_JSON_PAYLOAD_IN_REQUEST:          "The JSON payload in the request is invalid.",
    ErrorCode.MISSING_EXERCISE_TYPE_IN_REQUEST:         "The request does not contain an exercise type.",
    ErrorCode.MISSING_SESSION_ID_IN_REQUEST:            "The request does not contain a session id.",
    ErrorCode.MISSING_FRAME_DATA_IN_REQUEST:            "The request does not contain session id, frame id and content.",
    ErrorCode.CLIENT_IP_IS_INVALID:                     "The provided IP is invalid.",
    ErrorCode.CLIENT_AGENT_IS_INVALID:                  "The provided client agent is invalid.",
    ErrorCode.JSON_CONFIG_FILE_ERROR:                   "Error with the JSON configuration file.",
    ErrorCode.INTERNAL_SERVER_ERROR:                    "An internal server error has occurred.",
    
    # Flask and database management.
    ErrorCode.CANT_ADD_URL_RULE_TO_FLASK_SERVER:        "URL rule could not be added.",
    ErrorCode.UNRECOGNIZED_ICD_ERROR_TYPE:              "The provided ICD error type is not recognized",
    ErrorCode.UNRECOGNIZED_ICD_RESPONSE_TYPE:           "The provided ICD response type is not recognized",
    ErrorCode.DATABASE_CONNECTION_FAILED:               "The connection to the database has failed.",
    ErrorCode.DATABASE_SCHEMA_CREATION_FAILED:          "The creation of the database schema has failed.",
    ErrorCode.USER_ALREADY_EXISTS:                      "The user already exists in the system.",
    ErrorCode.DATABASE_INSERT_FAILED:                   "Failed to insert to database.",
    ErrorCode.DATABASE_QUERY_FAILED:                    "Failed to query the database.",
    ErrorCode.DATABASE_UPDATE_FAILED:                   "Failed to update the database.",
    ErrorCode.DATABASE_DELETE_FAILED:                   "Failed to delete from the database.",
    ErrorCode.USER_INVALID_CREDENTIALS:                 "The provided user credentials are invalid.",
    ErrorCode.USER_IS_ALREADY_LOGGED_IN:                "The user with the given credentials is already logged in.",
    ErrorCode.USER_IS_NOT_LOGGED_IN:                    "The user with the given credentials is not logged in.",
    ErrorCode.USER_NOT_FOUND:                           "The user with the given user id is not found in the system.",
    ErrorCode.FRAME_DECODING_FAILED:                    "The recieved frame failed to be decoded.",
    ErrorCode.TERMINATION_INCORRECT_PASSWORD:           "The provided password for termination is incorrect.",
    
    # Session Manager. 
    ErrorCode.EXERCISE_TYPE_DOES_NOT_EXIST:             "The provided exercise type is not supported in the system",
    ErrorCode.ERROR_GENERATING_SESSION_ID:              "Error while generating session ID.",
    ErrorCode.MAX_CLIENT_REACHED:                       "The maximum of concurrent clients has reached.",
    ErrorCode.INVALID_SESSION_ID:                       "The provided session ID is invalid.",
    ErrorCode.CLIENT_IS_NOT_REGISTERED:                 "The client is not registered to the system.",
    ErrorCode.CLIENT_IS_ALREADY_REGISTERED:             "The client is already registered to the system.",
    ErrorCode.CLIENT_IS_NOT_ACTIVE:                     "The client is not in an active session.",
    ErrorCode.CLIENT_IS_ALREADY_ACTIVE:                 "The client is already in an active session.",
    ErrorCode.CLIENT_IS_NOT_PAUSED:                     "The client is not in a paused session.",
    ErrorCode.CLIENT_IS_ALREADY_PAUSED:                 "The client is already in a paused session.",
    ErrorCode.CLIENT_IS_NOT_ENDED:                      "The client is not in an ended session.",
    ErrorCode.CLIENT_IS_ALREADY_ENDED:                  "The client is already in an ended session.",
    ErrorCode.CLIENT_IS_ONLY_REGISTERED:                "The client is only registered, did not start yet.",
    ErrorCode.SEARCH_TYPE_IS_NOT_SUPPORTED:             "The provided search type is not supported.",
    ErrorCode.SESSION_STATUS_IS_NOT_RECOGNIZED:         "The provided session status is not recognized.",
    ErrorCode.FRAME_INITIAL_VALIDATION_FAILED:          "The initial validation process of the frame failed.",
    ErrorCode.INVALID_EXTENDED_EVALUATION_PARAM:        "The parameter of extended evaluation is not valid.",
    ErrorCode.TRYING_TO_ANALYZE_FRAME_WHEN_DONE:        "Recieved a frame for analysis when the session is already done.",
    ErrorCode.TRYING_TO_ANALYZE_FRAME_WHEN_FAILED:      "Recieved a frame for analysis when the session has already failed.",
    ErrorCode.ERROR_CREATING_SESSION_DATA:              "Error while creating a session data instance",
    ErrorCode.SESSION_SHOULD_ABORT:                     "The session should be aborted due to reaching maximum number of bad frames.",
    ErrorCode.CLIENT_NOT_IN_SYSTEM:                     "The client is not registered in the system.",
    
    # PoseAnalyzer.
    ErrorCode.ERROR_INITIALIZING_POSE:                  "Error initializing PoseAnalyzer",
    ErrorCode.FRAME_PREPROCESSING_ERROR:                "Frame preprocessing failed",
    ErrorCode.FRAME_VALIDATION_ERROR:                   "Frame validation failed",
    ErrorCode.FRAME_ANALYSIS_ERROR:                     "Frame analysis failed",
    
    # JointAnalyzer.
    ErrorCode.VECTOR_VALIDATION_FAILED:                 "Vector validation has failed.",
    ErrorCode.ANGLE_VALIDATION_FAILED:                  "Angle validation has failed.",
    ErrorCode.ANGLE_CALCULATION_FAILED:                 "Angle calculation has failed.",
    ErrorCode.JOINT_CALCULATION_ERROR:                  "Joint calculation has failed.",
    ErrorCode.DIMENSION_OF_ANGLE_IS_INVALID:            "The angle's dimension is invalid",
    ErrorCode.TOO_MANY_INVALID_ANGLES:                  "Too many invalid angles in the provided frame",
    ErrorCode.CANT_CALCULATE_JOINTS_OF_UNSTALBE_FRAME:  "Tried to calculate joints for an unstable frame",
    ErrorCode.ANGLES_DICTIONARY_IS_EMPTY:               "The angles dictionary is empty.",
    
    # HistoryManager.
    ErrorCode.HISTORY_MANAGER_INIT_ERROR:               "Failed to initialize HistoryManager",
    ErrorCode.EXERCISE_START_TIME_ALREADY_SET:          "Tried to set exercise start time which already set.",
    ErrorCode.EXERCISE_END_TIME_ALREADY_SET:            "Tried to set exercise end time which already set.",
    ErrorCode.HISTORY_MANAGER_INTERNAL_ERROR:           "Internal HistoryManager error",
    ErrorCode.TRIED_TO_ADD_ERROR_TO_NONE_REP:           "Tried to add a new error to current rep's errors list, while it is None",
    ErrorCode.TRIED_TO_END_A_NONE_REP:                  "Tried to end the current rep, while it is None",
    ErrorCode.TRIED_TO_START_REP_WHILE_HAVE_ONE:        "Tried to start a new rep, while there is an active one",
    ErrorCode.ERROR_WITH_HANDLING_FRAMES_LIST:          "Failed to handle the frames list in HistoryManager.",
    ErrorCode.CANT_FIND_FRAME_IN_FRAMES_WINDOW:         "The provided frame id does not exist in the frames list.",
    ErrorCode.LAST_VALID_FRAME_IS_NONE:                 "The last valid frame is None (does not exist).",
    ErrorCode.ERROR_WITH_HANDLING_BAD_FRAMES_LIST:      "Failed to handle the bad frames list in HistoryManager.",
    
    # PoseQualityManager.
    ErrorCode.FAILED_TO_INITIALIZE_QUALITY_MANAGER:     "Failed to initialize the PoseQualityManager",
    ErrorCode.QUALITY_CHECKING_ERROR:                   "Error during the run of PoseQualityManager",
    ErrorCode.NO_PERSON_DETECTED_IN_FRAME:              "No person detected in received frame",
    ErrorCode.PARTIAL_BODY_IN_FRAME:                    "Only partial body is in frame",
    ErrorCode.TOO_FAR_IN_FRAME:                         "The person in frame is too far",
    ErrorCode.UNSTABLE_IN_FRAME:                        "The frame is unstable",
    ErrorCode.LAST_VALID_FRAME_MISSING:                 "The last valid frame is missing for comparison",
    
    # ErrorDetector.
    ErrorCode.ERROR_DETECTOR_INVALID_ANGLE:             "Invalid angle value provided to ErrorDetector.",
    ErrorCode.ERROR_DETECTOR_MISSING_THRESHOLD:         "Missing threshold entry in JSON for angle.",
    ErrorCode.ERROR_DETECTOR_MAPPING_NOT_FOUND:         "Mapping from angle to error code not found.",
    ErrorCode.ERROR_DETECTOR_UNSUPPORTED_PHASE:         "The provided exercise phase is not supported by ErrorDetector.",
    ErrorCode.ERROR_DETECTOR_INIT_ERROR:                "Failed to initialize ErrorDetector.",
    ErrorCode.ERROR_DETECTOR_CONFIG_ERROR:              "Error in ErrorDetector configuration.",
    
    # PhaseDetector.
    ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR:       "Error with the phase thresholds configuration file.",
    ErrorCode.NO_VALID_FRAME_DATA_IN_SESSION:           "No valid frame data found in session for phase detection.",
    ErrorCode.PHASE_UNDETERMINED_IN_FRAME:              "The phase could not be determined for the provided frame.",
    ErrorCode.TRIED_TO_DETECT_FRAME_FOR_UNSTABLE_STATE: "Tried to detect phase for a frame when the session is in an unstable state.",
    ErrorCode.PHASE_IS_NONE_IN_FRAME:                   "The detected phase in the provided frame is None.",
    
    # FeedbackFormatter.
    ErrorCode.FEEDBACK_FORMATTER_INIT_ERROR:            "Failed to initialize FeedbackFormatter",
    ErrorCode.FEEDBACK_CONSTRUCTION_ERROR:              "Error during feedback constructor",
    ErrorCode.POSE_QUALITY_FEEDBACK_SELECTION_ERROR:    "Error during pose quality feedback selection",
    ErrorCode.BIOMECHANICAL_FEEDBACK_SELECTION_ERROR:   "Error during biomechanical feedback selection",
    ErrorCode.FEEDBACK_CONFIG_RETRIEVAL_ERROR:          "Error retrieving feedback configuration.",
    
    # SessionSummaryManager.
    ErrorCode.SUMMARY_MANAGER_INIT_ERROR:               "Failed to initialize SessionSummaryManager",
    ErrorCode.SUMMARY_MANAGER_CREATE_ERROR:             "Failed to create session summary",
    ErrorCode.SUMMARY_MANAGER_INTERNAL_ERROR:           "Internal SessionSummaryManager error",
    
    # PositionSideDetector.
    ErrorCode.FAILED_TO_INITIALIZE_SIDE_DETECTOR:       "Failed to initialize PositionSideDetector",
    ErrorCode.POSITION_SIDE_DETECTION_ERROR:            "Failed to detect position side from landmarks.",
    ErrorCode.WRONG_EXERCISE_POSITION:                  "The detected position side is not suitable for the exercise type.",
    ErrorCode.POSITION_SIDE_DOES_NOT_EXIST:             "The position side could not be determined."
}

_extra_info = {
    ErrorCode.CONFIGURATION_FILE_DOES_NOT_EXIST: {
        "The file should be located in": ".../Server/Files/Config/ServerConfiguration.JSON",
        "This is a critical error": "can't configure server."
    },
    ErrorCode.JSON_FILE_DECODE_ERROR: {
        "Reason": "The data being deserialized is not a valid JSON document",
        "This is a critical error": "can't configure server."
    },
}

_critical_errors = {
    ErrorCode.CANT_CONFIGURE_LOG,
    ErrorCode.CONFIGURATION_FILE_DOES_NOT_EXIST,
    ErrorCode.JSON_FILE_DECODE_ERROR,
    ErrorCode.JSON_FILE_UNICODE_ERROR,
    ErrorCode.CRITICAL_CONFIG_PARAM_DOES_NOT_EXIST,
    ErrorCode.CONFIGURATION_KEY_IS_INVALID,
    ErrorCode.JSON_CONFIG_FILE_ERROR,
    ErrorCode.INTERNAL_SERVER_ERROR,
    ErrorCode.CANT_ADD_URL_RULE_TO_FLASK_SERVER,
    ErrorCode.UNRECOGNIZED_ICD_ERROR_TYPE,
    ErrorCode.UNRECOGNIZED_ICD_RESPONSE_TYPE,
    ErrorCode.DATABASE_CONNECTION_FAILED,
    ErrorCode.DATABASE_SCHEMA_CREATION_FAILED,
    ErrorCode.TERMINATION_INCORRECT_PASSWORD,
    ErrorCode.SEARCH_TYPE_IS_NOT_SUPPORTED,
    ErrorCode.SESSION_STATUS_IS_NOT_RECOGNIZED,
    ErrorCode.FAILED_TO_INITIALIZE_QUALITY_MANAGER,
    ErrorCode.ERROR_DETECTOR_INIT_ERROR,
    ErrorCode.PHASE_THRESHOLDS_CONFIG_FILE_ERROR,
    ErrorCode.FEEDBACK_FORMATTER_INIT_ERROR,
    ErrorCode.SUMMARY_MANAGER_INIT_ERROR,
    ErrorCode.FAILED_TO_INITIALIZE_SIDE_DETECTOR
}

@dataclass
############################
### ERROR RESPONSE CLASS ###
############################
class ErrorResponse:
    # Class fields.
    error_code:ErrorCode
    extra_info:Optional[Dict[str, Any]] = None

    ###############
    ### TO DICT ###
    ###############
    def to_dict(self) -> ErrorResponseDict:
        return_dict = {
            "code":        self.error_code.value,
            "description": self.error_code.description
        }
        if self.extra_info: return_dict["extra_info"] = self.extra_info
        return return_dict