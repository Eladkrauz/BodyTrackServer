############################################################
################# BODY TRACK // UTILITIES ##################
############################################################
################### CLASS: ConfigLoader ####################
############################################################
# The ConfigLoader class is responsible for reading and parsing
# server configuration from a JSON file, storing key parameters,
# and making them accessible globally throughout the runtime.

###############
### IMPORTS ###
###############
import json
import os
import re
from typing import Optional

class ConfigLoader:
    _instance = None  # Singleton instance.

    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self, config_path: str = "Utilities/Config/ServerConfiguration.JSON"):
        """
        Initializes the configuration loader by reading and parsing a JSON config file.

        :param config_path: The file path to the JSON configuration file (default = 'config/server_config.json')
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at: {config_path}")

        with open(config_path, 'r') as file:
            self._config_data = json.load(file)

    ####################
    ### GET INSTANCE ###
    ####################
    @classmethod
    def get_instance(cls):
        """
        Singleton access method to ensure one config loader across the application.
        :param config_path: Optional custom path for the config file.
        :return: The singleton instance of ConfigLoader.
        """
        if cls._instance is None:
            cls._instance = ConfigLoader()
        return cls._instance

    ###########
    ### GET ###
    ###########
    @classmethod
    def get(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        loader = cls.get_instance()
        """
        brief: Returns a configuration value by key, or a default if not found.
        param key: The key to fetch from the config.
        param default: Optional fallback value.
        return: The config value or default.
        """
        return loader._config_data.get(key, default)

    #################
    ### PRINT ALL ###
    #################
    @classmethod
    def print_all(cls):
        loader = cls.get_instance()
        ret_val = "Current Configuration File Constants:"
        """Prints all config keys and values (for debug purposes)."""
        for key, value in loader._config_data.items():
            ret_val += f"\n{key}: {value}"
        return ret_val
