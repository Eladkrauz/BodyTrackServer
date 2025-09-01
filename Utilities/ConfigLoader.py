############################################################
################# BODY TRACK // UTILITIES ##################
############################################################
################### CLASS: ConfigLoader ####################
############################################################

###############
### IMPORTS ###
###############
import json, os, inspect
from enum import Enum as enum
from json import JSONDecodeError
from Utilities.ErrorHandler import ErrorHandler, ErrorCode

class ConfigParameters(enum):
    """
    ### Description:
    The `ConfigParameters` enum class represents all the server configuration parameters, as described in the configuration file.
    """
    LOGGER_PATH = "logger_path"
    LOGGER_NAME = "logger_name"
    ARCHIVE_DIR_NAME = "archive_dir_name"
    LOG_LEVEL = "log_level"
    SUPPORTED_EXERCIES = "supported_exercises"

class ConfigLoader:
    """
    ### Description:
    The `ConfigLoader` class is responsible for reading and parsing 
    server configuration from a `JSON` file, storing key parameters,
    and making them accessible globally throughout the runtime.
    ### Notes:
    - The class functions as a **singleton** class.
    - The configuration file path is written hard coded in the class constructor.
    """
    _instance = None  # Singleton instance.

    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self, config_path:str = "Utilities/Config/ServerConfiguration.JSON") -> 'ConfigLoader':
        """
        ### Brief:
        The `__init__` method initializes the `ConfigLoader` object. 
        The class functions as a **singleton** class.
        ### Arguments:
        - `config_path`: The path to the configuration input file.
        ### Raises:
        - `FileNotFoundError`: In case the specified file does not exist.
        - `JSONDecodeError`: In case the data being deserialized is not a valid JSON document.
        - `UnicodeDecodeError`: In case the data being deserialized does not contain UTF-8, UTF-16 or UTF-32 encoded data
        ### Notes:
        - The `config_path` defaults to 'Utilities/Config/ServerConfiguration.JSON'.
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at: {config_path}")

        with open(config_path, 'r') as file:
            self._config_data = dict(json.load(file))

    ####################
    ### GET INSTANCE ###
    ####################
    @classmethod
    def get_instance(cls):
        """
        ### Brief:
        The `get_instance` method returns an instance of the `ConfigLoader` object.
        It functions as a **singleton** instance creator.
        ### Arguments:
        - `cls`: The class object.
        ### Returns:
        - The `ConfigLoader` singleton object.
        ### Notes:
        In case there is an error with the configuration file, the system is being terminated.
        - `FileNotFoundError`: In case the specified file does not exist.
        - `JSONDecodeError`: In case the data being deserialized is not a valid JSON document.
        - `UnicodeDecodeError`: In case the data being deserialized does not contain UTF-8, UTF-16 or UTF-32 encoded data
        """
        if cls._instance is None:
            try:
                cls._instance = ConfigLoader()
            except FileNotFoundError as e:
                ErrorHandler.handle(
                    opcode=ErrorCode.CONFIGURATION_FILE_NOT_EXIST,
                    origin=inspect.currentframe(),
                    message="Configuration file does not exist.",
                    extra_info={
                        "The file should be located in": "Utilities/Config/ServerConfiguration.JSON",
                        "This is a critical error": "can't configure server."
                    },
                    critical=True
                )
            except JSONDecodeError as e:
                ErrorHandler.handle(
                    opcode=ErrorCode.CONFIGURATION_FILE_NOT_EXIST,
                    origin=inspect.currentframe(),
                    message="Error parsing the configuration JSON file.",
                    extra_info={
                        "Reason": "The data being deserialized is not a valid JSON document",
                        "This is a critical error": "can't configure server."
                    },
                    critical=True
                )
            except UnicodeDecodeError as e:
                ErrorHandler.handle(
                    opcode=ErrorCode.CONFIGURATION_FILE_NOT_EXIST,
                    origin=inspect.currentframe(),
                    message="Error parsing the configuration JSON file.",
                    extra_info={
                        "Reason": "The data being deserialized does not contain UTF-8, UTF-16 or UTF-32 encoded data",
                        "This is a critical error": "can't configure server."
                    },
                    critical=True
                )

        return cls._instance

    ###########
    ### GET ###
    ###########
    @classmethod
    def get(cls, key:ConfigParameters, critical_value:bool) -> str:
        """
        ### Brief:
        The `get` method returns a configuration value by key.
        ### Arguments:
        - `cls`: The class object.
        - `key`: The key to fetch from the config file, as an enum element of `ConfigParameters` enum class.
        - `critical_value`: A `bool` indicating if the value is critical for the server configuration. 
        ### Returns:
        - The value of the specified key, as configured in the configuration file.
        ### Notes:
        - If the requested key is missing and marked as critical, the system will invoke the `ErrorHandler` and may terminate.
        - Uses the `ConfigParameters` enum to ensure only predefined configuration keys are accessed, avoiding typos or inconsistent access.
        """
        try:
            if not isinstance(key, str): key = key.value
            return cls.get_instance()._config_data[key]
        except KeyError as e:
            ErrorHandler.handle(
                opcode=ErrorCode.CONFIGURATION_PARAMETER_NOT_EXIST,
                origin=inspect.currentframe(),
                message=f"The paramter {key.value} does not exist in the configuration file.",
                extra_info={
                    "Please check": "the configuration file.",
                    "Critical" if critical_value else "Not critical": "Can't configure server. Terminating system." if critical_value else "Can configure server anyway. Unexpected behavior can be seen."
                },
                critical=critical_value
            )