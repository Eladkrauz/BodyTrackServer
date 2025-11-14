############################################################
################# BODY TRACK // UTILITIES ##################
############################################################
################### CLASS: ErrorHandler ####################
############################################################

###############
### IMPORTS ###
###############
import sys, inspect
from os.path import basename
from enum import Enum as enum
from types import FrameType
from Utilities.Logger import Logger as Logger
from Common.ClientServerIcd import ClientServerIcd as ICD

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
    


    def __new__(cls, code:int, description:str, extra_info:dict = None, critical:bool = False):
        obj = object.__new__(cls)
        obj._value_ = code
        obj.description = description
        obj.extra_info = extra_info
        obj.critical = critical
        return obj

###########################
### ERROR HANDLER CLASS ###
###########################
class ErrorHandler:
    """
    ### Description:
    The `ErrorHandler` class serves as a centralized utility for managing and
    reporting errors across the server. It enables structured logging of issues
    using standardized error codes, detailed messages, and optional contextual
    information, while supporting both non-critical logging and critical failures
    that gracefully terminate the system.

    ### Notes:
    No need to get an instance of `ErrorHandler` before handling an error,
    the methods are class methods and do it themselves.
    """

    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self) -> 'ErrorHandler':
        pass

    ##############
    ### HANDLE ###
    ##############
    @classmethod
    def handle(cls, error:ErrorCode, origin:FrameType, extra_info:dict = None, do_not_log=False) -> None:
        """
        ### Brief:
        The `handle` method gets error information and logs it into the system logger.

        ### Arguments:
        - `error`: The error from `ErrorCode` enum class.
        - `origin`: The origin of the error. Use `inspect.currentframe()` to get the origin.
        - `extra_info`: An extra dictionary, can be added as extra information to the information of the error. Defaults to None.
        - `do_not_log`: A boolean indicating if to log the error or not. Defaults to False (meaning: log the error).

        ### Explanation:
        After importing the `ErrorHandler` and `ErrorCode`, call `handle` this way:
        ```
        from Utilities.ErrorHandler import ErrorHandler, ErrorCode
        ErrorHandler.handle(
            error=ErrorCode.ERROR_TYPE,
            origin=inpsect.currentframe(),
            extra_info={
                "More info": "...",
                "Even more info": "..."
            }, # Can be ignored.
            do_not_log=False # Ignore this argument. Only for internal use.
        )
        ```
        This is how a valid `ErrorCode` looks like:
        ```
        ERROR_NAME = (
            error_opcode, # An integer representing the error code.
            error_reason, # A string representing the error reason.
            extra_info,   # A dict containing extra info about the error. Can be None.
            abort         # A bool value. If True the system aborts after logging the error
        )
        ```
        For example:
        ```
        USER_ALREADY_EXISTS = (
            105,                                      # The opcode is 105.
            "The user already exists in the system.", # The reason for the error.
            None,                                     # No extra information.
            False                                     # The system won't abort.
        )
        ```
        ### Notes:
        - `do_not_log` and `extra_info` can be ignored and not sent as parameters.
        - Please make sure `extra_info` does not contain keys the same as the keys inside `ErrorCode.ERROR_TYPE` you sent.
        """
        if not isinstance(error, ErrorCode):
            raise TypeError("The provided error is not a valid ErrorCode object.")
        
        full_message = f"[Error {str(error.value)}] {error.description}"

        # Updating the extra info.
        if error.extra_info is None and extra_info is not None:
            error.extra_info = extra_info
        elif error.extra_info is not None and extra_info is not None:
            dict(error.extra_info).update(extra_info)

        if error.extra_info: # If extra info is provided, add it to the message.
            for key, value in dict(error.extra_info).items():
                full_message += f"\n{key}: {value}"

        full_message += f"\nOrigin: File - {basename(origin.f_code.co_filename)} | Function - {origin.f_code.co_name} | Line - {origin.f_lineno}"

        if error.critical: # If critical is True, log as critical and exit the program.
            full_message += "\nThis error is not recoverable."
            if do_not_log or not Logger.critical(full_message):
                print(full_message)
            sys.exit("Aborting system.")
        else: # If critical is False, log as error and continue.
            if not Logger.error(full_message):
                print(full_message)

    ######################
    ### IMIDIATE ABORT ###
    ######################
    @classmethod
    def imidiate_abort(cls, error:ErrorCode, origin:FrameType) -> None:
        """
        ### Brief:
        The `imidiate_abort` method prints an error and terminates the system.
        ### Arguments
        """
        cls.handle(error=error, origin=origin, do_not_log=True)

    ######################
    ### CONVERT TO ICD ###
    ######################
    @classmethod
    def convert_to_icd(cls, error_code:ErrorCode) -> ICD.ErrorType:
        """
        ### Brief:
        The `convert_to_icd` method dynamically converts an `ErrorCode` into
        the corresponding `ICD.ErrorType` based on matching enum names.

        ### Arguments:
        `error_code` (ErrorCode): The error code to be converted.

        ### Returns:
        The corresponding `ICD.ErrorType` object.

        ### Notes:
        If no matching `ICD.ErrorType` exists, returns `ICD.ErrorType.INTERNAL_SERVER_ERROR`
        and logs `ErrorCode.UNRECOGNIZED_ICD_ERROR_TYPE`.
        """
        try:
            # Try to access ICD.ErrorType member by name.
            return ICD.ErrorType[error_code.name]
        except Exception as e:
            # If not found, log and return default.
            cls.handle(
                error=ErrorCode.UNRECOGNIZED_ICD_ERROR_TYPE,
                origin=inspect.currentframe(),
                extra_info={ "Provided error": f"Value: {error_code.value}, Name: {error_code.name}" }
            )
            return ICD.ErrorType.INTERNAL_SERVER_ERROR