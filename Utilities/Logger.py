############################################################
################# BODY TRACK // UTILITIES ##################
############################################################
###################### CLASS: Logger #######################
############################################################
# The Logger class provides a centralized logging utility for the server,
# enabling consistent and formatted output of informational, warning, error,
# and debug messages. It supports both console and file logging, making it
# suitable for real-time monitoring and post-execution diagnostics.

###############
### IMPORTS ###
###############
import logging
import os
from datetime import datetime

#################
### CONSTANTS ###
#################
LOGGER_PATH="Utilities/Logs/ServerLogger.log"
LOGGER_NAME="BodyTrackLogger"
ARCHIVE_DIR_NAME="Archive"

class Logger:
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    _instance = None

    def __init__(self, log_file_path=LOGGER_PATH):
        """
        Initializes the server logger.
        Archives existing log file if present and starts a new log session.
        """
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        # Archive existing log file if it exists
        if os.path.exists(log_file_path):
            with open(log_file_path, mode='a') as f:
                f.write("\n#############################################################")
                f.write("\n##### This log file was archived on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " #####")
                f.write("\n#############################################################")

            archive_dir = os.path.join(os.path.dirname(log_file_path), ARCHIVE_DIR_NAME)
            os.makedirs(archive_dir, exist_ok=True)

            # Count existing archived versions
            base_name = os.path.splitext(os.path.basename(log_file_path))[0]  # ServerLogger
            extension = os.path.splitext(log_file_path)[1]  # .log

            existing_archives = [
                f for f in os.listdir(archive_dir)
                if f.startswith(base_name + "_") and f.endswith(extension)
            ]

            # Determine next index
            next_index = 1
            if existing_archives:
                indices = []
                for filename in existing_archives:
                    try:
                        idx = int(filename.replace(base_name + "_", "").replace(extension, ""))
                        indices.append(idx)
                    except ValueError:
                        continue
                if indices:
                    next_index = max(indices) + 1

            archived_file = os.path.join(archive_dir, f"{base_name}_{next_index}{extension}")
            os.rename(log_file_path, archived_file)

        self.logger = logging.getLogger(LOGGER_NAME)
        self.logger.setLevel(logging.DEBUG)

        with open(log_file_path, mode='w') as f:
            f.write("#############################\n")
            f.write("##### BODY TRACK LOGGER #####\n")
            f.write("#############################\n")

        # Avoid adding handlers multiple times.
        if not self.logger.handlers:
            file_handler = logging.FileHandler(log_file_path, mode='a')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))

            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    ####################
    ### GET INSTANCE ###
    ####################
    @classmethod
    def get_instance(cls, log_file_path=LOGGER_PATH):
        if cls._instance is None:
            cls._instance = Logger(log_file_path)
        return cls._instance

    ############
    ### INFO ###
    ############
    @classmethod
    def info(cls, msg: str):
        cls.get_instance().logger.info(msg)

    #############
    ### DEBUG ###
    #############
    @classmethod
    def debug(cls, msg: str):
        cls.get_instance().logger.debug(msg)
        

    ###############
    ### WARNING ###
    ###############
    @classmethod
    def warning(cls, msg: str):
        cls.get_instance().logger.warning(msg)

    #############
    ### ERROR ###
    #############
    @classmethod
    def error(cls, msg: str):
        cls.get_instance().logger.error(msg)

    ################
    ### CRITICAL ###
    ################
    @classmethod
    def critical(cls, msg: str):
        cls.get_instance().logger.critical(msg)