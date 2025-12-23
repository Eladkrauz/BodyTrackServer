############################################################
####### BODY TRACK // SERVER // UTILITIES // ERROR #########
############################################################
##################### CLASS: ErrorCode #####################
############################################################

###############
### IMPORTS ###
###############
from enum import Enum as enum
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
class ErrorCode(enum):
    """
    ### Description:
    An enum class representing error codes.
    """
    # Configuration and management.
    CANT_CONFIGURE_LOG                          = auto(), "Logger can't get configured.",                                                        None, True
    CONFIGURATION_FILE_DOES_NOT_EXIST           = auto(), "Configuration file does not exist.", {
                                                        "The file should be located in": "Utilities/Config/ServerConfiguration.JSON",
                                                        "This is a critical error": "can't configure server."
                                                    },                                                                                                 True
    JSON_FILE_DECODE_ERROR                      = auto(), "Error parsing the configuration JSON file.", {
                                                        "Reason": "The data being deserialized is not a valid JSON document",
                                                        "This is a critical error": "can't configure server."
                                                    },                                                                                                 True
    JSON_FILE_UNICODE_ERROR                     = auto(), "Error parsing the configuration JSON file.", {
                                                       "Reason":    "The data being deserialized does not contain UTF-8,\
                                                                    UTF-16 or UTF-32 encoded data",
                                                       "This is a critical error": "can't configure server."
                                                    },                                                                                                 True
    CONFIG_PARAM_DOES_NOT_EXIST                 = auto(), "The key sent does not exist in the configuration file.",                             None, False
    CRITICAL_CONFIG_PARAM_DOES_NOT_EXIST        = auto(), "The key sent does not exist in the configuration file. Critical.",                   None,  True
    CONFIGURATION_KEY_IS_INVALID                = auto(), "The key sent is not a valid list of ConfigParameters",                               None,  True
    INVALID_JSON_PAYLOAD_IN_REQUEST             = auto(), "The JSON payload in the request is invalid.",                                        None, False
    MISSING_EXERCISE_TYPE_IN_REQUEST            = auto(), "The request does not contain an exercise type.",                                     None, False
    MISSING_SESSION_ID_IN_REQUEST               = auto(), "The request does not contain a session id.",                                         None, False
    MISSING_FRAME_DATA_IN_REQUEST               = auto(), "The request does not contain session id, frame id and content.",                     None, False
    CLIENT_IP_IS_INVALID                        = auto(), "The provided IP is invalid.",                                                        None, False
    CLIENT_AGENT_IS_INVALID                     = auto(), "The provided client agent is invalid.",                                              None, False
    JSON_CONFIG_FILE_ERROR                      = auto(), "Error with the JSON configuration file.",                                            None,  True
    INTERNAL_SERVER_ERROR                       = auto(), "An internal server error has occurred.",                                             None,  True

    # Flask and database management.
    CANT_ADD_URL_RULE_TO_FLASK_SERVER           = auto(), "URL rule could not be added.",                                                       None,  True
    UNRECOGNIZED_ICD_ERROR_TYPE                 = auto(), "The provided ICD error type is not recognized",                                      None,  True
    UNRECOGNIZED_ICD_RESPONSE_TYPE              = auto(), "The provided ICD response type is not recognized",                                   None,  True
    DATABASE_CONNECTION_FAILED                  = auto(), "The connection to the database has failed.",                                         None,  True
    DATABASE_SCHEMA_CREATION_FAILED             = auto(), "The creation of the database schema has failed.",                                    None,  True
    USER_ALREADY_EXISTS                         = auto(), "The user already exists in the system.",                                             None, False
    DATABASE_INSERT_FAILED                      = auto(), "Failed to insert to database.",                                                      None, False
    DATABASE_QUERY_FAILED                       = auto(), "Failed to query the database.",                                                      None, False
    DATABASE_UPDATE_FAILED                      = auto(), "Failed to update the database.",                                                     None, False
    DATABASE_DELETE_FAILED                      = auto(), "Failed to delete from the database.",                                                None, False
    USER_INVALID_CREDENTIALS                    = auto(), "The provided user credentials are invalid.",                                         None, False
    USER_IS_ALREADY_LOGGED_IN                   = auto(), "The user with the given credentials is already logged in.",                          None, False
    USER_IS_NOT_LOGGED_IN                       = auto(), "The user with the given credentials is not logged in.",                              None, False
    USER_NOT_FOUND                              = auto(), "The user with the given user id is not found in the system.",                        None, False
    FRAME_DECODING_FAILED                       = auto(), "The recieved frame failed to be decoded.",                                           None, False
    TERMINATION_INCORRECT_PASSWORD              = auto(), "The provided password for termination is incorrect.",                                None,  True
    
    # Session Manager.  
    EXERCISE_TYPE_DOES_NOT_EXIST                = auto(), "The provided exercise type is not supported in the system",                          None, False
    ERROR_GENERATING_SESSION_ID                 = auto(), "Error while generating session ID.",                                                 None, False
    MAX_CLIENT_REACHED                          = auto(), "The maximum of concurrent clients has reached.",                                     None, False
    INVALID_SESSION_ID                          = auto(), "The provided session ID is invalid.",                                                None, False
    CLIENT_IS_NOT_REGISTERED                    = auto(), "The client is not registered to the system.",                                        None, False
    CLIENT_IS_ALREADY_REGISTERED                = auto(), "The client is already registered to the system.",                                    None, False
    CLIENT_IS_NOT_ACTIVE                        = auto(), "The client is not in an active session.",                                            None, False
    CLIENT_IS_ALREADY_ACTIVE                    = auto(), "The client is already in an active session.",                                        None, False
    CLIENT_IS_NOT_PAUSED                        = auto(), "The client is not in a paused session.",                                             None, False
    CLIENT_IS_ALREADY_PAUSED                    = auto(), "The client is already in a paused session.",                                         None, False
    CLIENT_IS_NOT_ENDED                         = auto(), "The client is not in an ended session.",                                             None, False
    CLIENT_IS_ALREADY_ENDED                     = auto(), "The client is already in an ended session.",                                         None, False
    CLIENT_IS_ONLY_REGISTERED                   = auto(), "The client is only registered, did not start yet.",                                  None, False
    SEARCH_TYPE_IS_NOT_SUPPORTED                = auto(), "The provided search type is not supported.",                                         None,  True
    SESSION_STATUS_IS_NOT_RECOGNIZED            = auto(), "The provided session status is not recognized.",                                     None,  True
    FRAME_INITIAL_VALIDATION_FAILED             = auto(), "The initial validation process of the frame failed.",                                None, False
    INVALID_EXTENDED_EVALUATION_PARAM           = auto(), "The parameter of extended evaluation is not valid.",                                 None, False
    TRYING_TO_ANALYZE_FRAME_WHEN_DONE           = auto(), "Recieved a frame for analysis when the session is already done.",                    None, False
    TRYING_TO_ANALYZE_FRAME_WHEN_FAILED         = auto(), "Recieved a frame for analysis when the session has already failed.",                 None, False
    ERROR_CREATING_SESSION_DATA                 = auto(), "Error while creating a session data instance",                                       None, False
    SESSION_SHOULD_ABORT                        = auto(), "The session should be aborted due to reaching maximum number of bad frames.",        None, False
    CLIENT_NOT_IN_SYSTEM                        = auto(), "The client is not registered in the system.",                                        None, False

    # PoseAnalyzer.
    ERROR_INITIALIZING_POSE                     = auto(), "Error initializing PoseAnalyzer",                                                    None, False
    FRAME_PREPROCESSING_ERROR                   = auto(), "Frame preprocessing failed",                                                         None, False
    FRAME_VALIDATION_ERROR                      = auto(), "Frame validation failed",                                                            None, False
    FRAME_ANALYSIS_ERROR                        = auto(), "Frame analysis failed",                                                              None, False

    # JointAnalyzer.
    VECTOR_VALIDATION_FAILED                    = auto(), "Vector validation has failed.",                                                      None, False
    ANGLE_VALIDATION_FAILED                     = auto(), "Angle validation has failed.",                                                       None, False
    ANGLE_CALCULATION_FAILED                    = auto(), "Angle calculation has failed.",                                                      None, False
    JOINT_CALCULATION_ERROR                     = auto(), "Joint calculation has failed.",                                                      None, False
    DIMENSION_OF_ANGLE_IS_INVALID               = auto(), "The angle's dimension is invalid",                                                   None, False
    TOO_MANY_INVALID_ANGLES                     = auto(), "Too many invalid angles in the provided frame",                                      None, False
    CANT_CALCULATE_JOINTS_OF_UNSTALBE_FRAME     = auto(), "Tried to calculate joints for an unstable frame",                                    None, False

    # HistoryManager.
    HISTORY_MANAGER_INIT_ERROR                  = auto(), "Failed to initialize HistoryManager",                                                None, False
    EXERCISE_START_TIME_ALREADY_SET             = auto(), "Tried to set exercise start time which already set.",                                None, False
    EXERCISE_END_TIME_ALREADY_SET               = auto(), "Tried to set exercise end time which already set.",                                  None, False
    HISTORY_MANAGER_INTERNAL_ERROR              = auto(), "Internal HistoryManager error",                                                      None, False
    TRIED_TO_ADD_ERROR_TO_NONE_REP              = auto(), "Tried to add a new error to current rep's errors list, while it is None",            None, False
    TRIED_TO_END_A_NONE_REP                     = auto(), "Tried to end the current rep, while it is None",                                     None, False
    TRIED_TO_START_REP_WHILE_HAVE_ONE           = auto(), "Tried to start a new rep, while there is an active one",                             None, False
    ERROR_WITH_HANDLING_FRAMES_LIST             = auto(), "Failed to handle the frames list in HistoryManager.",                                None, False
    CANT_FIND_FRAME_IN_FRAMES_WINDOW            = auto(), "The provided frame id does not exist in the frames list.",                           None, False
    LAST_VALID_FRAME_IS_NONE                    = auto(), "The last valid frame is None (does not exist).",                                     None, False
    ERROR_WITH_HANDLING_BAD_FRAMES_LIST         = auto(), "Failed to handle the bad frames list in HistoryManager.",                            None, False

    # PoseQualityManager.
    FAILED_TO_INITIALIZE_QUALITY_MANAGER        = auto(), "Failed to initialize the PoseQualityManager",                                        None,  True
    QUALITY_CHECKING_ERROR                      = auto(), "Error during the run of PoseQualityManager",                                         None, False
    NO_PERSON_DETECTED_IN_FRAME                 = auto(), "No person detected in received frame",                                               None, False
    PARTIAL_BODY_IN_FRAME                       = auto(), "Only partial body is in frame",                                                      None, False
    TOO_FAR_IN_FRAME                            = auto(), "The person in frame is too far",                                                     None, False
    UNSTABLE_IN_FRAME                           = auto(), "The frame is unstable",                                                              None, False
    LAST_VALID_FRAME_MISSING                    = auto(), "The last valid frame is missing for comparison",                                     None, False
    
    # ErrorDetector.
    ERROR_DETECTOR_INVALID_ANGLE                = auto(), "Invalid angle value provided to ErrorDetector.",                                     None, False
    ERROR_DETECTOR_MISSING_THRESHOLD            = auto(), "Missing threshold entry in JSON for angle.",                                         None, False
    ERROR_DETECTOR_MAPPING_NOT_FOUND            = auto(), "Mapping from angle to error code not found.",                                        None, False
    ERROR_DETECTOR_UNSUPPORTED_PHASE            = auto(), "The provided exercise phase is not supported by ErrorDetector.",                     None, False
    ERROR_DETECTOR_INIT_ERROR                   = auto(), "Failed to initialize ErrorDetector.",                                                None,  True
    ERROR_DETECTOR_CONFIG_ERROR                 = auto(), "Error in ErrorDetector configuration.",                                              None, False   

    # PhaseDetector.
    PHASE_THRESHOLDS_CONFIG_FILE_ERROR          = auto(), "Error with the phase thresholds configuration file.",                                None,  True
    NO_VALID_FRAME_DATA_IN_SESSION              = auto(), "No valid frame data found in session for phase detection.",                          None, False
    PHASE_UNDETERMINED_IN_FRAME                 = auto(), "The phase could not be determined for the provided frame.",                          None, False
    TRIED_TO_DETECT_FRAME_FOR_UNSTABLE_STATE    = auto(), "Tried to detect phase for a frame when the session is in an unstable state.",        None, False

    # FeedbackFormatter.
    FEEDBACK_FORMATTER_INIT_ERROR               = auto(), "Failed to initialize FeedbackFormatter",                                             None,  True
    FEEDBACK_CONSTRUCTION_ERROR                 = auto(), "Error during feedback constructor",                                                  None, False
    POSE_QUALITY_FEEDBACK_SELECTION_ERROR       = auto(), "Error during pose quality feedback selection",                                       None, False
    BIOMECHANICAL_FEEDBACK_SELECTION_ERROR      = auto(), "Error during biomechanical feedback selection",                                      None, False
    FEEDBACK_CONFIG_RETRIEVAL_ERROR             = auto(), "Error retrieving feedback configuration.",                                           None, False   
    
    # SessionSummaryManager.
    SUMMARY_MANAGER_INIT_ERROR                  = auto(), "Failed to initialize SessionSummaryManager",                                         None,  True
    SUMMARY_MANAGER_CREATE_ERROR                = auto(), "Failed to create session summary",                                                   None, False
    SUMMARY_MANAGER_INTERNAL_ERROR              = auto(), "Internal SessionSummaryManager error",                                               None, False 

    # PositionSideDetector.
    FAILED_TO_INITIALIZE_SIDE_DETECTOR          = auto(), "Failed to initialize PositionSideDetector",                                          None,  True
    POSITION_SIDE_DETECTION_ERROR               = auto(), "Failed to detect position side from landmarks.",                                     None, False
    WRONG_EXERCISE_POSITION                     = auto(), "The detected position side is not suitable for the exercise type.",                  None, False
    POSITION_SIDE_DOES_NOT_EXIST                = auto(), "The position side could not be determined.",                                         None, False

    def __new__(cls, code:int, description:str, extra_info:dict = None, critical:bool = False):
        obj = object.__new__(cls)
        obj._value_ = code
        obj.description = description
        obj.extra_info = extra_info
        obj.critical = critical
        return obj
    
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