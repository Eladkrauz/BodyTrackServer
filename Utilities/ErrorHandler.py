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
    CANT_CONFIGURE_LOG                  = auto()
    CONFIGURATION_FILE_NOT_EXIST        = auto()
    CONFIGURATION_PARAMETER_NOT_EXIST   = auto()
    CANT_ADD_URL_RULE_TO_FLASK_SERVER   = auto()

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
    - The class functions as a **singleton** class, so no need to create multiple objects.
    - No need to get an instance of `ErrorHandler` before handling an error, the methods are class methods and do it themselves.
    """
    _instance = None

    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self) -> 'ErrorHandler':
        """
        ### Brief:
        The `__init__` method is a private constructor for the singleton `ErrorHandler` class.
        """

    ####################
    ### GET INSTANCE ###
    ####################
    @classmethod
    def get_instance(cls) -> 'ErrorHandler':
        """
        ### Brief:
        The `get_instance` method returns an instance of the `ErrorHandler` object.
        It functions as a **singleton** instance creator.
        ### Arguments:
        - `cls`: The class object.
        ### Returns:
        - The `ErrorHandler` singleton object.
        """
        if cls._instance is None:
            cls._instance = ErrorHandler()
        return cls._instance

    ##############
    ### HANDLE ###
    ##############
    @classmethod
    def handle(cls, opcode:ErrorCode, origin:FrameType, message:str, extra_info:dict = None, critical:bool = False) -> None:
        """
        ### Brief:
        The `handle` method gets error information and logs it into the system logger.
        ### Arguments:
        - `cls`: The class object.
        - `opcode`: The opcode of the error from `ErrorCode` enum class.
        - `origin`: The origin of the error. Use `inspect.currentframe()` to get the origin.
        - `message`: A string representing the error main message.
        - `extra_info`: An optional dictionary representing extra information. Defaults to `None`.
        - `critical`: `True` will terminate the system, `False` will just log the error. Defaults to `False`.
        ### Explanation:
        After importing the `ErrorHandler` and `ErrorCode`, call `handle` this way:
        ```python
        from Utilities.ErrorHandler import ErrorHandler, ErrorCode
        ErrorHandler.handle(
            opcode=ErrorCode.ERROR_TYPE,
            origin=inpsect.currentframe(),
            message="The main error message",
            extra_info={
                'Reason': 'reason of the error',
                'SomethingElse': 'write here'
                }, # Can be ignored.
            critical=False # Can be ignored.
        )
        ```
        #### 
        ### Notes:
        - `extra_info` and `critical` can be ignored and not sent as parameters.
        """
        full_message = f"[Error {str(opcode.value)}] {message}"

        if extra_info: # If extra info is provided, add it to the message.
            for key, value in extra_info.items():
                full_message += f"\n{key}: {value}"

        full_message += f"\nOrigin: File - {basename(origin.f_code.co_filename)} | Function: {origin.f_code.co_name} | Line: {origin.f_lineno}"

        if critical: # If critical is True, log as critical and exit the program.
            full_message += "\nThis error is not recoverable. Aborting system."
            if not Logger.critical(full_message):
                print(full_message)
            sys.exit(f"Critical error occurred (code {str(opcode.value)}). Exiting.")
        else: # If critical is False, log as error and continue.
            if not Logger.error(full_message):
                print(full_message)