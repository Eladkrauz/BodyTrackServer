############################################################
################# BODY TRACK // UTILITIES ##################
############################################################
################### CLASS: ErrorHandler ####################
############################################################

###############
### IMPORTS ###
###############
import sys
from os.path import basename
from enum import Enum as enum
from enum import auto
from types import FrameType
from Utilities.Logger import Logger as Logger

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

    # Flask.
    CANT_ADD_URL_RULE_TO_FLASK_SERVER       = (7, "URL rule could not be added.", None, True)

    # # Session Manager.
    # EXERCISE_TYPE_DOES_NOT_EXIST           = auto()
    ERROR_GENERATING_SESSION_ID             = (8, "Error while generating session ID.", None, False)

    # PoseAnalyzer
    ERROR_INITIALIZING_POSE                 = (9, "Error initializing PoseAnalyzer", None, False)
    FRAME_PREPROCESSING_ERROR               = (10, "Frame preprocessing Failed", None, False)
    FRAME_VALIDATION_ERROR                  = (11, "Frame validate error", None, False)
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
    - No need to get an instance of `ErrorHandler` before handling an error, the methods are class methods and do it themselves.
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
        - `cls`: The class object.
        - `error`: The error from `ErrorCode` enum class.
        - `origin`: The origin of the error. Use `inspect.currentframe()` to get the origin.
        - `extra_info`: An extra dictionary, can be added as extra information to the information of the error. Defaults to None.
        - `do_not_log`: A boolean indicating if to log the error or not. Defaults to False (meaning: log the error).
        ### Explanation:
        After importing the `ErrorHandler` and `ErrorCode`, call `handle` this way:
        ```python
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
        #### 
        ### Notes:
        - `do_not_log` and `extra_info` can be ignored and not sent as parameters.
        - Please make sure `extra_info` does not contain keys the same as the keys inside `ErrorCode.ERROR_TYPE` you sent.
        """
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