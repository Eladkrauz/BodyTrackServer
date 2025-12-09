############################################################
####### BODY TRACK // SERVER // UTILITIES // ERROR #########
############################################################
################### CLASS: ErrorHandler ####################
############################################################

###############
### IMPORTS ###
###############
import sys, inspect
from os.path import basename
from types import FrameType

from Server.Utilities.Logger import Logger as Logger
from Server.Utilities.Error.ErrorCode import ErrorCode

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
        from Server.Utilities.Error.ErrorHandler import ErrorHandler
        from Server.Utilities.Error.ErrorCode import ErrorCode
        ErrorHandler.handle(
            error=ErrorCode.ERROR_TYPE,
            origin=inpsect.currentframe(),
            extra_info={
                "More info": "...",
                "Even more info": "..."
            }, # Can be ignored.
            do_not_log=False, # Ignore this argument. Only for internal use.
            do_not_abort=False, # Ignore this argument too.
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
        - `do_not_log`, `do_not_abort` and `extra_info` can be ignored and not sent as parameters.
        - Please make sure `extra_info` does not contain keys the same as the keys inside `ErrorCode.ERROR_TYPE` you sent.
        """
        if not isinstance(error, ErrorCode):
            raise TypeError("The provided error is not a valid ErrorCode object.")
        
        full_message = f"[Error {str(error.value)}] {error.description}"

        # Updating the extra info.
        if error.extra_info is None and extra_info is not None:
            error.extra_info = extra_info
        elif error.extra_info is not None and extra_info is not None:
            error.extra_info.update(extra_info)

        if error.extra_info: # If extra info is provided, add it to the message.
            for key, value in error.extra_info.items():
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

        ### Arguments:
        - `error` (ErrorCode): The error code to be printed. (not logged!)
        - `origin` (FrameType): The origin of where the error happened.
        """
        cls.handle(error=error, origin=origin, do_not_log=True)