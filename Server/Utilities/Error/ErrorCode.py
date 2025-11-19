############################################################
####### BODY TRACK // SERVER // UTILITIES // ERROR #########
############################################################
##################### CLASS: ErrorCode #####################
############################################################

###############
### IMPORTS ###
###############
from enum import Enum as enum

########################
### ERROR CODE CLASS ###
########################
class ErrorCode(enum):
    """
    ### Description:
    An enum class representing error codes.
    """
    # Configuration.
    CANT_CONFIGURE_LOG                      = (1, "Logger can't get configured.")
    CONFIGURATION_FILE_DOES_NOT_EXIST       = (2, "Configuration file does not exist.", {"The file should be located in": "Utilities/Config/ServerConfiguration.JSON", "This is a critical error": "can't configure server."}, True)
    JSON_FILE_DECODE_ERROR                  = (3, "Error parsing the configuration JSON file.", {"Reason": "The data being deserialized is not a valid JSON document", "This is a critical error": "can't configure server."}, True)
    JSON_FILE_UNICODE_ERROR                 = (4, "Error parsing the configuration JSON file.", {"Reason": "The data being deserialized does not contain UTF-8, UTF-16 or UTF-32 encoded data", "This is a critical error": "can't configure server."}, True)
    CONFIGURATION_PARAMETER_DOES_NOT_EXIST  = (5, "The key sent does not exist in the configuration file.", {"Please check": "the configuration file.", "Critical": "Can't configure server. Terminating system."}, True)
    CONFIGURATION_KEY_IS_INVALID            = (6, "The key sent is not a valid list of ConfigParameters", None, True)

    # Flask and database management.
    CANT_ADD_URL_RULE_TO_FLASK_SERVER       = (100, "URL rule could not be added.", None, True)
    UNRECOGNIZED_ICD_ERROR_TYPE             = (101, "The provided ICD error type is not recognized", None, True)
    UNRECOGNIZED_ICD_RESPONSE_TYPE          = (102, "The provided ICD response type is not recognized", None, True)
    DATABASE_CONNECTION_FAILED              = (103, "The connection to the database has failed.", None, True)
    DATABASE_SCHEMA_CREATION_FAILED         = (104, "The creation of the database schema has failed.", None, True)
    USER_ALREADY_EXISTS                     = (105, "The user already exists in the system.", None, False)
    DATABASE_INSERT_FAILED                  = (106, "Failed to insert to database.", None, False)
    DATABASE_QUERY_FAILED                   = (107, "Failed to query the database.", None, False)
    DATABASE_UPDATE_FAILED                  = (108, "Failed to update the database.", None, False)
    DATABASE_DELETE_FAILED                  = (109, "Failed to delete from the database.", None, False)
    USER_INVALID_CREDENTIALS                = (110, "The provided user credentials are invalid.", None, False)
    USER_IS_ALREADY_LOGGED_IN               = (111, "The user with the given credentials is already logged in.", None, False)
    USER_IS_NOT_LOGGED_IN                   = (112, "The user with the given credentials is not logged in.", None, False)
    USER_NOT_FOUND                          = (113, "The user with the given user id is not found in the system.", None, False)

    # Session Manager.
    EXERCISE_TYPE_DOES_NOT_EXIST            = (200, "The provided exercise type is not supported in the system", None, False)
    ERROR_GENERATING_SESSION_ID             = (201, "Error while generating session ID.", None, False)
    MAX_CLIENT_REACHED                      = (202, "The maximum of concurrent clients has reached.", None, False)
    INVALID_SESSION_ID                      = (203, "The provided session ID is invalid.", None, False)
    CLIENT_IS_NOT_REGISTERED                = (204, "The client is not registered to the system.", None, False)
    CLIENT_IS_ALREADY_REGISTERED            = (205, "The client is already registered to the system.", None, False)
    CLIENT_IS_NOT_ACTIVE                    = (206, "The client is not in an active session.", None, False)
    CLIENT_IS_ALREADY_ACTIVE                = (207, "The client is already in an active session.", None, False)
    CLIENT_IS_NOT_PAUSED                    = (208, "The client is not in a paused session.", None, False)
    CLIENT_IS_ALREADY_PAUSED                = (209, "The client is already in a paused session.", None, False)
    CLIENT_IS_NOT_ENDED                     = (210, "The client is not in an ended session.", None, False)
    CLIENT_IS_ALREADY_ENDED                 = (211, "The client is already in an ended session.", None, False)
    CLIENT_IS_ONLY_REGISTERED               = (212, "The client is only registered, did not start yet.", None, False)
    SEARCH_TYPE_IS_NOT_SUPPORTED            = (213, "The provided search type is not supported.", None, True)
    SESSION_STATUS_IS_NOT_RECOGNIZED        = (214, "The provided session status is not recognized.", None, True)
    FRAME_INITIAL_VALIDATION_FAILED         = (215, "The initial validation process of the frame failed.", None, False)
    INVALID_EXTENDED_EVALUATION_PARAM       = (216, "The parameter of extended evaluation is not valid.", None, False)

    # PoseAnalyzer.
    ERROR_INITIALIZING_POSE                 = (300, "Error initializing PoseAnalyzer", None, False)
    FRAME_PREPROCESSING_ERROR               = (301, "Frame preprocessing failed", None, False)
    FRAME_VALIDATION_ERROR                  = (302, "Frame validation failed", None, False)
    FRAME_ANALYSIS_ERROR                    = (303, "Frame analysis failed", None, False)

    # JointAnalyzer.
    VECTOR_VALIDATION_FAILED                = (400, "Vector validation has failed.", None, False)
    ANGLE_VALIDATION_FAILED                 = (401, "Angle validation has failed.", None, False)
    ANGLE_CALCULATION_FAILED                = (402, "Angle calculation has failed.", None, False)
    JOINT_CALCULATION_ERROR                 = (403, "Joint calculation has failed.", None, False)
    LANDMARK_VISIBILITY_IS_INVALID          = (404, "The landmark's visibility is invalid", None, False)
    DIMENSION_OF_ANGLE_IS_INVALID           = (405, "The angle's dimension is invalid", None, False)
    TOO_MANY_INVALID_ANGLES                 = (406, "Too many invalid angles in the provided frame", None, False)

    # HistoryManager.
    HISTORY_MANAGER_INIT_ERROR              = (500, "Failed to initialize HistoryManager", None, False)

    # PoseQualityManager.
    FAILED_TO_INITIALIZE_QUALITY_MANAGER    = (600, "Failed to initialize the PoseQualityManager", None, True)
    
    def __new__(cls, code:int, description:str, extra_info:dict = None, critical:bool = False):
        obj = object.__new__(cls)
        obj._value_ = code
        obj.description = description
        obj.extra_info = extra_info
        obj.critical = critical
        return obj