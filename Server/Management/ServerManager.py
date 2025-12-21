###############################################################
############## BODY TRACK // SERVER // MANAGEMENT #############
###############################################################
##################### CLASS: ServerManager ####################
###############################################################

###############
### IMPORTS ###
###############
from threading import Thread
import time

from Server.Communication.FlaskServer         import FlaskServer
from Server.Utilities.Logger                  import Logger
from Server.Utilities.Config.ConfigLoader     import ConfigLoader
from Server.Utilities.Config.ConfigParameters import ConfigParameters
from Server.Management.TestManager            import TestManager
from Server.Data.Session.ExerciseType         import ExerciseType

############################
### SERVER MANAGER CLASS ###
############################
class ServerManager:
    """
    ### Description:
    The `ServerManager` class is responsible for initializing and managing
    the server components, including configuration loading, logging setup,
    and starting the Flask server.
    """
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self) -> None:
        """
        ### Brief:
        The `init` method initializes the ServerManager class by setting up
        the configuration, logger, and Flask server.
        """
        # Initialize the ConfigLoader.
        ConfigLoader.initialize()
        # Initialize the Logger.
        Logger.initialize()
        Logger.info("###############################")
        Logger.info("##### INITIALIZING SERVER #####")
        Logger.info("###############################")
        # Initialize the Flask Server.
        self.flask_server = FlaskServer(
            host=ConfigLoader.get(key=[ConfigParameters.Major.COMMUNICATION, ConfigParameters.Minor.HOST]),
            port=ConfigLoader.get(key=[ConfigParameters.Major.COMMUNICATION, ConfigParameters.Minor.PORT])
        )
        Thread(target=self.flask_server.run, daemon=True).start()
        time.sleep(2)
        Logger.info("##############################################")
        Logger.info("##### SERVER IS INITIALIZED SUCCESSFULLY #####")
        Logger.info("##############################################")

        TestManager().test_with_enters(
            exercise_type=ExerciseType.BICEPS_CURL,
            video_path="/Users/eladkrauz/Desktop/Videos/try8.mp4"
        )

        # Keep the main thread alive.
        # Commented out to prevent infinite loop during testing.
        # while True: time.sleep(5)