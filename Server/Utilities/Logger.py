############################################################
############ BODY TRACK // SERVER // UTILITIES #############
############################################################
###################### CLASS: Logger #######################
############################################################

###############
### IMPORTS ###
###############
import logging, os, inspect, json
from datetime import datetime

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
    _ready = False

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
        self.retrieve_configurations()

        # Ensure log directory exists.
        os.makedirs(os.path.dirname(self.logger_path), exist_ok=True)

        # Archive existing log file if it exists.
        if os.path.exists(self.logger_path):
            with open(self.logger_path, mode='a') as f:
                f.write("\n#############################################################")
                f.write("\n##### This log file was archived on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " #####")
                f.write("\n#############################################################")

            self.archive_dir = os.path.join(os.path.dirname(self.logger_path), self.archive_dir)
            os.makedirs(self.archive_dir, exist_ok=True)

            # Create the archived log file.
            base_name = os.path.splitext(os.path.basename(self.logger_path))[0]
            extension = os.path.splitext(self.logger_path)[1]  # .log
            archived_file = os.path.join(self.archive_dir, f"{base_name}_{datetime.now().strftime('%d-%m-%Y_%H-%M')}{extension}")
            os.rename(self.logger_path, archived_file)

        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(self.log_level)

        with open(self.logger_path, mode='w') as f:
            f.write("#############################\n")
            f.write("##### BODY TRACK LOGGER #####\n")
            f.write("#############################\n")

        # Avoid adding handlers multiple times.
        if not self.logger.handlers:
            file_handler = logging.FileHandler(self.logger_path, mode='a')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))

            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    ####################
    ### GET INSTANCE ###
    ####################
    @classmethod
    def _get_instance(cls) -> 'Logger':
        """
        ### Brief:
        The `_get_instance` method returns an instance of the `Logger` object.
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
                print("Can't configure the logger.")
                raise e
                
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
        logObject = cls._get_instance()
        if logObject is not None and cls._ready:
            logObject.logger.info(f"{cls._who_called()}: {msg}")
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
        logObject = cls._get_instance()
        if logObject is not None and cls._ready:
            logObject.logger.debug(f"{cls._who_called()}: {msg}")
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
        logObject = cls._get_instance()
        if logObject is not None and cls._ready:
            logObject.logger.warning(f"{cls._who_called()}: {msg}")
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
        logObject = cls._get_instance()
        if logObject is not None and cls._ready:
            logObject.logger.error(f"{cls._who_called()}: {msg}")
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
        logObject = cls._get_instance()
        if logObject is not None and cls._ready:
            logObject.logger.critical(f"{cls._who_called()}: {msg}")
            return True
        return False
    
    ##################
    ### INITIALIZE ###
    ##################
    @classmethod
    def initialize(cls) -> None:
        """
        ### Brief:
        The `initialize` method initializes the logger singleton instance.
        """
        cls._get_instance()
        cls._ready = True
        print("[INFO]: Logger is initialized.")

    ###############################
    ### RETRIEVE CONFIGURATIONS ###
    ############################### 
    def retrieve_configurations(self) -> None:
        """
        ### Brief:
        The `retrieve_configurations` method gets the updated configurations from the
        configuration file.
        """
        from Utilities.Config.ConfigLoader import ConfigLoader
        from Utilities.Config.ConfigParameters import ConfigParameters

        self.logger_path:str = ConfigLoader.get([
            ConfigParameters.Major.LOG,
            ConfigParameters.Minor.LOGGER_PATH
        ])
        self.logger_name:str = ConfigLoader.get([
            ConfigParameters.Major.LOG,
            ConfigParameters.Minor.LOGGER_NAME
        ])
        self.archive_dir:str = ConfigLoader.get([
            ConfigParameters.Major.LOG,
            ConfigParameters.Minor.ARCHIVE_DIR_NAME
        ])
        self.log_level:str = ConfigLoader.get([
            ConfigParameters.Major.LOG,
            ConfigParameters.Minor.LOG_LEVEL
        ])
        self.debug_sessions_dir:str = ConfigLoader.get([
            ConfigParameters.Major.LOG,
            ConfigParameters.Minor.DEBUG_DIR_NAME
        ])

    ############################
    ### SAVE DEBUG JSON FILE ###
    ############################
    @classmethod
    def save_debug_json_file(cls, file_name:str, content:dict) -> None:
        """
        ### Brief:
        The `save_debug_json_file` method saves a debug JSON file
        into the debug sessions directory.

        ### Arguments:
        - `file_name` (str): The name of the JSON file to save (without extension).
        - `content` (dict): The content to save into the JSON file.
        """
        logger_path:str = cls.logger_path
        logger_dir = logger_path.removesuffix("/ServerLogger.log")
        with open(f"{logger_dir}/{cls.debug_sessions_dir}/{file_name}.json", "w", encoding="utf-8") as f:
            json.dump(content, f, indent=4, ensure_ascii=False)

    ##################
    ### WHO CALLED ###
    ##################
    @classmethod
    def _who_called(cls):
        """
        ### Brief:
        The `_who_called` method retrieves the name of the class that called the logger.
        """
        list_of_callers = inspect.stack()[2:]
        for frameinfo in list_of_callers:
            loc = frameinfo.frame.f_locals
            if 'self' in loc:
                return loc['self'].__class__.__name__
            if 'cls' in loc:
                return loc['cls'].__name__
        return "UnknownClass"