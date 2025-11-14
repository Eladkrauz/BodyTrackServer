############################################################
####### BODY TRACK // SERVER // UTILITIES // CONFIG ########
############################################################
################### CLASS: ConfigLoader ####################
############################################################

###############
### IMPORTS ###
###############
import json, os, inspect
from json import JSONDecodeError

from Server.Utilities.Error.ErrorHandler import ErrorHandler
from Server.Utilities.Error.ErrorCode import ErrorCode
from Server.Utilities.Config.ConfigParameters import ConfigParameters

###########################
### CONFIG LOADER CLASS ###
###########################
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
    _ready = False

    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self, config_path:str = "Server/Files/Config/ServerConfiguration.JSON") -> 'ConfigLoader':
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
            raise FileNotFoundError()

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
            except FileNotFoundError:
                ErrorHandler.imidiate_abort(error=ErrorCode.CONFIGURATION_FILE_DOES_NOT_EXIST, origin=inspect.currentframe())
            except JSONDecodeError as e:
                ErrorHandler.imidiate_abort(error=ErrorCode.JSON_FILE_DECODE_ERROR, origin=inspect.currentframe())
            except UnicodeDecodeError as e:
                ErrorHandler.imidiate_abort(error=ErrorCode.JSON_FILE_UNICODE_ERROR, origin=inspect.currentframe())

        return cls._instance

    ###########
    ### GET ###
    ###########
    @classmethod
    def get(cls, key:list[ConfigParameters], critical_value:bool) -> str:
        """
        ### Brief:
        The `get` method returns a configuration value by key.
        ### Arguments:
        - `cls`: The class object.
        - `key`: The key to fetch from the config file, as a list of enum elements of `ConfigParameters` enum class.
        - `critical_value`: A `bool` indicating if the value is critical for the server configuration. 
        ### Returns:
        - The value of the specified key, as configured in the configuration file.
        ### Notes:
        - If the requested key is missing and marked as critical, the system will invoke the `ErrorHandler` and may terminate.
        - Uses the `ConfigParameters` enum to ensure only predefined configuration keys are accessed, avoiding typos or inconsistent access.
        """
        try:
            config_loader = cls.get_instance()
            if not (isinstance(key, list) and not all(isinstance(k, ConfigParameters) for k in key)):
                ErrorHandler.handle(error=ErrorCode.CONFIGURATION_KEY_IS_INVALID, origin=inspect.currentframe())
            result = config_loader._config_data
            for k in key:
                value = k.value
                result = result[value]
            return result
        except KeyError as e:
            ErrorHandler.handle(error=ErrorCode.CONFIGURATION_PARAMETER_DOES_NOT_EXIST, origin=inspect.currentframe())

    ################
    ### IS READY ###
    ################
    @classmethod
    def is_ready(cls) -> bool:
        return cls._ready
    
    @classmethod
    def initialize(cls) -> None:
        cls.get_instance()
        cls._ready = True
        print("[INFO]: ConfigLoader is initialized.")