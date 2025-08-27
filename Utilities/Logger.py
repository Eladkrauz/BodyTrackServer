############################################################
################# BODY TRACK // UTILITIES ##################
############################################################
###################### CLASS: Logger #######################
############################################################

###############
### IMPORTS ###
###############
import logging, os, inspect
from datetime import datetime
from Utilities.ConfigLoader import ConfigLoader as Loader
from Utilities.ErrorHandler import ErrorHandler, ErrorCode

class Logger:
    """
    ### Description:
    **The `Logger` class provides a centralized logging utility for the server.**
    It enables consistent and formatted output of informational, warning, error,
    and debug messages.
    
    It supports both console and file logging, making it suitable for real-time
    monitoring and post-execution diagnostics.
    ### Notes:
    - The logger is configured using the configuration parameters provided in the configuration file, parsed by the `ConfigLoader` class.
    - No need to get an instance of the `Logger` before logging, the methods are class methods and do it themselves.
    """
    _instance = None # The class object instance.

    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self) -> 'Logger':
        """
        ### Brief:
        The `__init__` method initializes the server logger. 
        The class functions as a **singleton** class.
        ### Arguments:
        - `log_file_path`: The path to the logger output file.
        ### Notes:
        - It archives existing log file if exists and starts a new log session.
        """
        # Extract parameters from the configuration file.
        logger_parameters = Loader.get('log')
        logger_path = logger_parameters['logger_path']
        logger_name = logger_parameters['logger_name']
        archive_dir = logger_parameters['archive_dir_name']
        log_level = logger_parameters['log_level']

        # Ensure log directory exists.
        os.makedirs(os.path.dirname(logger_path), exist_ok=True)

        # Archive existing log file if it exists.
        if os.path.exists(logger_path):
            with open(logger_path, mode='a') as f:
                f.write("\n#############################################################")
                f.write("\n##### This log file was archived on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " #####")
                f.write("\n#############################################################")

            archive_dir = os.path.join(os.path.dirname(logger_path), archive_dir)
            os.makedirs(archive_dir, exist_ok=True)

            # Create the archived log file.
            base_name = os.path.splitext(os.path.basename(logger_path))[0]
            extension = os.path.splitext(logger_path)[1]  # .log
            archived_file = os.path.join(archive_dir, f"{base_name}_{datetime.now().strftime("%d-%m-%Y_%H_%M")}{extension}")
            os.rename(logger_path, archived_file)

        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(log_level)

        with open(logger_path, mode='w') as f:
            f.write("#############################\n")
            f.write("##### BODY TRACK LOGGER #####\n")
            f.write("#############################\n")

        # Avoid adding handlers multiple times.
        if not self.logger.handlers:
            file_handler = logging.FileHandler(logger_path, mode='a')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))

            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    ####################
    ### GET INSTANCE ###
    ####################
    @classmethod
    def get_instance(cls) -> 'Logger':
        """
        ### Brief:
        The `get_instance` method returns an instance of the `Logger` object.
        It functions as a **singleton** instance creator.
        ### Arguments:
        - `cls`: The class object.
        ### Returns:
        - The `Logger` singleton object, or `None` if not configured.
        ### Notes:
        - In case the logger is not configured or failed to be configured, the method will raise an error.
        """
        if cls._instance is None:
            try:
                cls._instance = Logger()
            except Exception as e:
                ErrorHandler.handle(
                    opcode=ErrorCode.CANT_CONFIGURE_LOG,
                    origin=inspect.currentframe(),
                    message="Can't configure the logger.",
                    extra_info={
                        "Exception": f"{type(e)}",
                        "Reason": f"{str(e)}"
                    },
                    critical=False
                )
                
        return cls._instance

    ############
    ### INFO ###
    ############
    @classmethod
    def info(cls, msg: str) -> bool:
        """
        ### Brief:
        The `info` method logs an info message into the logger.
        ### Arguments:
        - `cls`: The class object.
        - `msg`: The message to be logged.
        ### Returns:
        - `True` if the message was logged, `False` if not.
        ### Notes:
        - In case the logger is not configured or failed to be configured, the message won't be logged.
        """
        logObject = cls.get_instance()
        if logObject is not None:
            logObject.logger.info(msg)
            return True
        return False

    #############
    ### DEBUG ###
    #############
    @classmethod
    def debug(cls, msg: str) -> bool:
        """
        ### Brief:
        The `debug` method logs a debug message into the logger.
        ### Arguments:
        - `cls`: The class object.
        - `msg`: The message to be logged.
        ### Returns:
        - `True` if the message was logged, `False` if not.
        ### Notes:
        - In case the logger is not configured or failed to be configured, the message won't be logged.
        """
        logObject = cls.get_instance()
        if logObject is not None:
            logObject.logger.debug(msg)
            return True
        return False        

    ###############
    ### WARNING ###
    ###############
    @classmethod
    def warning(cls, msg: str) -> bool:
        """
        ### Brief:
        The `warning` method logs a warning message into the logger.
        ### Arguments:
        - `cls`: The class object.
        - `msg`: The message to be logged.
        ### Returns:
        - `True` if the message was logged, `False` if not.
        ### Notes:
        - In case the logger is not configured or failed to be configured, the message won't be logged.
        """
        logObject = cls.get_instance()
        if logObject is not None:
            logObject.logger.warning(msg)
            return True
        return False

    #############
    ### ERROR ###
    #############
    @classmethod
    def error(cls, msg: str) -> bool:
        """
        ### Brief:
        The `error` method logs an error message into the logger.
        ### Arguments:
        - `cls`: The class object.
        - `msg`: The message to be logged.
        ### Returns:
        - `True` if the message was logged, `False` if not.
        ### Notes:
        - In case the logger is not configured or failed to be configured, the message won't be logged.
        """
        logObject = cls.get_instance()
        if logObject is not None:
            logObject.logger.error(msg)
            return True
        return False

    ################
    ### CRITICAL ###
    ################
    @classmethod
    def critical(cls, msg: str) -> bool:
        """
        ### Brief:
        The `critical` method logs a critical message into the logger.
        ### Arguments:
        - `cls`: The class object.
        - `msg`: The message to be logged.
        ### Returns:
        - `True` if the message was logged, `False` if not.
        ### Notes:
        - In case the logger is not configured or failed to be configured, the message won't be logged.
        """
        logObject = cls.get_instance()
        if logObject is not None:
            logObject.logger.critical(msg)
            return True
        return False