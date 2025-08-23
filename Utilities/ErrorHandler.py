############################################################
################# BODY TRACK // UTILITIES ##################
############################################################
################### CLASS: ErrorHandler ####################
############################################################
# The ErrorHandler class serves as a centralized utility for managing and
# reporting errors across the server. It enables structured logging of issues
# using standardized error codes, detailed messages, and optional contextual
# information, while supporting both non-critical logging and critical failures
# that gracefully terminate the system. This ensures consistency, improves
# debuggability, and maintains robust system behavior throughout the application.

###############
### IMPORTS ###
###############
import sys, inspect
import os
from os.path import basename
from Utilities.Logger import Logger
from enum import Enum as enum

########################
### ERROR CODE CLASS ###
########################
class ErrorCode(enum):
    """
    An enum class representing error codes.
    """
    ERROR_CODE_1 = 1
    ERROR_CODE_2 = 2
    ERROR_CODE_3 = 3
    ERROR_CODE_4 = 4
    ERROR_CODE_5 = 5
    ERROR_CODE_6 = 6
    ERROR_CODE_7 = 7

###########################
### ERROR HANDLER CLASS ###
###########################
class ErrorHandler:
    """
    A centralized error handling utility for the server. 
    Allows structured error reporting with an opcode, message, context, and severity level.
    """

    _instance = None

    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self):
        """Private constructor. Use get_instance() instead."""
        self.logger = Logger.get_instance()

    ####################
    ### GET INSTANCE ###
    ####################
    @classmethod
    def get_instance(cls):
        """Returns the singleton instance of ErrorHandler."""
        if cls._instance is None:
            cls._instance = ErrorHandler()
        return cls._instance

    ##############
    ### HANDLE ###
    ##############
    @classmethod
    def handle(cls, opcode: ErrorCode, origin, message: str, extra_info: dict = None, critical: bool = False):
        handler = cls.get_instance()
        """
        Handles an error in a consistent, structured way.

        :param opcode: Numeric or string code identifying the error type
        :param message: Human-readable error message
        :param extra_info: Optional dictionary with additional debug info
        :param critical: If True, logs as critical and exits the program, otherwise logs as error and continues.
        """
        full_message = f"[Error {str(opcode.value)}] {message}"

        if extra_info: # If extra info is provided, add it to the message.
            for key, value in extra_info.items():
                full_message += f"\n{key}: {value}"

        full_message += f"\nOrigin: File - {basename(origin.f_code.co_filename)} | Function: {origin.f_code.co_name} | Line: {origin.f_lineno}"

        if critical: # If critical is True, log as critical and exit the program.
            full_message += "\nThis error is not recoverable. Aborting system."
            handler.logger.critical(full_message)
            sys.exit(f"Critical error occurred (code {str(opcode.value)}). Exiting.")
        else: # If critical is False, log as error and continue.
            handler.logger.error(full_message)