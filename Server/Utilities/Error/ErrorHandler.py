############################################################
####### BODY TRACK // SERVER // UTILITIES // ERROR #########
############################################################
################### CLASS: ErrorHandler ####################
############################################################

###############
### IMPORTS ###
###############
import sys
from typing import Any, Dict
from os.path import basename
from types import FrameType

from Utilities.Logger import Logger as Logger
from Utilities.Error.ErrorCode import ErrorCode

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
        The `handle` method processes an `ErrorCode` instance and logs a formatted,
        human-readable error message into the system logger.

        This method is responsible **only for logging and control-flow decisions**.
        It does **not** construct or return an `ErrorResponse` object.

        ### Arguments:
        - `error` (`ErrorCode`):
            A valid error code from the `ErrorCode` enum describing the failure.
        - `origin` (`FrameType`):
            The origin of the error. Use `inspect.currentframe()` to capture the
            file name, function name, and line number.
        - `extra_info` (`dict`, optional):
            Runtime-provided contextual information to enrich the error message.
            This data is merged with any static `extra_info` defined on the
            `ErrorCode` itself.
        - `do_not_log` (`bool`, optional):
            If set to `True`, suppresses logging via the system logger.
            Defaults to `False`.

        ### Behavior:
        - Builds a formatted error message using:
            - The numeric error code
            - The error description
            - Static `extra_info` defined on the `ErrorCode` (if any)
            - Runtime `extra_info` provided by the caller (if any)
            - Origin metadata (file, function, line)
        - Static and runtime `extra_info` are merged **without mutating** the
        `ErrorCode` enum instance.
        - If the error is marked as critical:
            - Logs the message as critical
            - Terminates the application
        - Otherwise:
            - Logs the message as a recoverable error
            - Execution continues

        ### Usage Example:
        ```python
        from Utilities.Error.ErrorHandler import ErrorHandler
        from Utilities.Error.ErrorCode import ErrorCode
        import inspect

        ErrorHandler.handle(
            error=ErrorCode.INVALID_SESSION_ID,
            origin=inspect.currentframe(),
            extra_info={
                "session_id": "abc123",
                "client_ip": "192.168.1.10"
            }
        )
        ```

        ### Notes:
        - This method **must not mutate** `ErrorCode` enum instances.
        - `extra_info` is intended for logging and diagnostics only.
        - Response serialization is handled elsewhere (e.g., Flask response layer).
        """
        if not isinstance(error, ErrorCode):
            raise TypeError("The provided error is not a valid ErrorCode object.")
        
        full_message = f"[Error {str(error.value)}] {error.description}"

        # Updating the extra info.
        extra_info_to_log:Dict[str, Any] = {}
        if error.extra_info is not None: extra_info_to_log.update(error.extra_info)
        if extra_info is not None:       extra_info_to_log.update(extra_info)

        if extra_info_to_log: # If extra info is provided, add it to the message.
            for key, value in extra_info_to_log.items():
                full_message += f"\n{key}: {value}"

        full_message += f"\nOrigin: File - {basename(origin.f_code.co_filename)} | Function - {origin.f_code.co_name} | Line - {origin.f_lineno}"

        if error.is_critical: # If critical is True, log as critical and exit the program.
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