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
from typing import Dict, List

from Utilities.Error.ErrorHandler import ErrorHandler
from Utilities.Error.ErrorCode import ErrorCode
from Utilities.Config.ConfigParameters import ConfigParameters

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
    _instance = None # Singleton instance.
    _config_path = "Server/Files/Config/ServerConfiguration.JSON"

    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self):
        """
        ### Brief:
        The `__init__` method initializes the `ConfigLoader` object. 
        The class functions as a **singleton** class.

        ### Arguments:
        - `config_path`: The path to the main server configuration file.
            - Defaults to `Utilities/Server/Files/Config/ServerConfiguration.JSON`.

        ### Raises:
        - `FileNotFoundError`: In case the specified file does not exist.
        - `JSONDecodeError`: In case the data being deserialized is not a valid JSON document.
        - `UnicodeDecodeError`: In case the data being deserialized does not contain UTF-8, UTF-16 or UTF-32 encoded data
        """
        self.refresh()

    ###############
    ### REFRESH ###
    ###############
    @classmethod
    def refresh(cls) -> None:
        """
        ### Brief:
        The `refresh` method reloads the configuration data from the configuration file.

        ### Notes:
        - This method can be called to update the configuration data at runtime if the configuration file changes.
        """
        try:
            cls._config_data = cls._get_json_data(cls._config_path)
        except FileNotFoundError:
            print("[ERROR]: Configuration file does not exist.")
            exit(1)
        except Exception as e:
            print("[ERROR]: An error occurred while loading the configuration file.")
            exit(1)

    ####################
    ### GET INSTANCE ###
    ####################
    @classmethod
    def get_instance(cls, main_config_file_path:str = None) -> 'ConfigLoader':
        """
        ### Brief:
        The `get_instance` method returns an instance of the `ConfigLoader` object.
        It functions as a **singleton** instance creator.

        ### Arguments:
        - `cls`: The class object.
        - `main_config_file_path` (str): The path to the main server config file. Defaults to None.

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
                if main_config_file_path is not None: cls._instance = ConfigLoader(main_config_file_path)
                else:                                 cls._instance = ConfigLoader()
            except FileNotFoundError:
                print("[FATAL]: Configuration file does not exist.")
                exit(1)
            except JSONDecodeError as e:
                print("[FATAL]: Configuration file is not a valid JSON document.")
                exit(1)
            except UnicodeDecodeError as e:
                print("[FATAL]: Configuration file contains invalid unicode data.")
                exit(1)
            except Exception as e:
                print("[FATAL]: Configuration internal error.")
                exit(1)

        return cls._instance

    ###########
    ### GET ###
    ###########
    @classmethod
    def get(cls,
            key:list[ConfigParameters] | None,
            critical_value:bool = True,
            different_file:str = None,
            read_all:bool = False
        ) -> str | Dict | List | int | float | None:
        """
        ### Brief:
        The `get` method returns a configuration value by key.

        ### Arguments:
        - `cls`: The class object.
        - `key`: The key to fetch from the config file, as a list of enum elements of `ConfigParameters` enum class.
        - `critical_value`: A `bool` indicating if the value is critical for the server configuration. Defaults to `True`.
        - `different_file`: A `str` of a different configuration file path. Defaults to `None`.
        - `read_all`: A `bool` indicating whether to read all content of file, or keys from it.

        ### Returns:
        - The value of the specified key, as configured in the configuration file.
        - If not found **and** not critical (`critical_value` set to `False`), returns `None`

        ### Notes:
        - If the requested key is missing and marked as critical, the system will invoke the `ErrorHandler` and may terminate.
        - Uses the `ConfigParameters` enum to ensure only predefined configuration keys are accessed, avoiding typos or inconsistent access.
        - The method works on 2 modes:
            1. `different_file` is `None` (was not sent as a parameter): Read the server config regular file.
            2. `different_file` is not `None`: Read this path's content and search the key inside it.
        """
        config_loader = cls.get_instance()
        try:
            if not read_all and (not (isinstance(key, list) or not all(isinstance(k, ConfigParameters) for k in key))):
                ErrorHandler.handle(error=ErrorCode.CONFIGURATION_KEY_IS_INVALID, origin=inspect.currentframe())

            # Deciding which file should be searched for key-value pair.
            if different_file is None: result = cls._config_data
            else:                      result = cls._get_json_data(different_file)

            # If read_all is True, we don't need to look for a specific key.
            if read_all: return result

            # Going deep in the dictionary to retrieve the required value of the given key.
            for k in key:
                value = k.value
                result = result[value]
            return result
        # If an error occured (for exmaple: the key does not exist in the dictionary).
        except KeyError as e:
            if critical_value: # If True - will abort system.
                ErrorHandler.handle(
                    error=ErrorCode.CRITICAL_CONFIG_PARAM_DOES_NOT_EXIST,
                    origin=inspect.currentframe(),
                    extra_info={ "key": key }
                )
            else:
                ErrorHandler.handle(
                    error=ErrorCode.CONFIG_PARAM_DOES_NOT_EXIST,
                    origin=inspect.currentframe(),
                    extra_info={ "key": key }
                )
                return None
    
    #####################
    ### GET JSON DATA ###
    #####################
    @classmethod
    def _get_json_data(cls, file_path:str) -> dict | None:
        """
        ### Brief:
        The `_get_json_data` method opens a file in the specifiec path (given as `file_path`),
        and returns the content of the `JSON` file.

        ### Arguments:
        - `file_path` (str): The `JSON` file to open and load its content.

        ### Returns:
        - `dict` with the content of the `JSON` file.

        ### Notes:
        - Called on initialization (`__init__`) to retrieve the main configuration file content.
        - Can be called in runtime also to retrieve content of different configuration files.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError()

        with open(file_path, 'r') as file:
            return dict(json.load(file))

    ##################
    ### INITIALIZE ###
    ##################
    @classmethod
    def initialize(cls) -> None:
        """
        ### Brief:
        The `initialize` method is the `ConfigLoader` signleton access method.
        It is called once and initializes the instance.
        """
        cls.get_instance()
        print("[INFO]: ConfigLoader is initialized.")