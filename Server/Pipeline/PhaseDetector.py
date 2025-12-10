############################################################
############# BODY TRACK // SERVER // PIPELINE #############
############################################################
################### CLASS: PhaseDetector ###################
############################################################

###############
### IMPORTS ###
###############
from typing import Dict, Any
import inspect

from Server.Data.Session.SessionData  import SessionData
from Server.Data.Phase.PhaseType      import PhaseType

from Server.Utilities.Error.ErrorCode import ErrorCode
from Server.Utilities.Logger          import Logger

############################
### PHASE DETECTOR CLASS ###
############################
class PhaseDetector:
    pass

    def __init__(self):
        self.retrieve_configurations()

        Logger.info("Initialized successfully.")

    def determine_phase(self, session_data:SessionData) -> PhaseType | ErrorCode:
        pass

    def ensure_initial_phase_correct(self, session_data:SessionData, joints:Dict[str, Any]) -> bool | ErrorCode:
        pass


    ###############################
    ### RETRIEVE CONFIGURATIONS ###
    ###############################
    def retrieve_configurations(self) -> None:
        """
        ### Brief:
        The `retrieve_configurations` method gets the updated configurations from the
        configuration file.
        """
        from Server.Utilities.Config.ConfigLoader import ConfigLoader
        from Server.Utilities.Config.ConfigParameters import ConfigParameters

        # Load configuration file path.
        self.config_file_path:str = ConfigLoader.get(
            key=[
                ConfigParameters.Major.PHASE,
                ConfigParameters.Minor.PHASE_DETECTOR_CONFIG_FILE
            ]
        )

        # Load thresholds from the specific configuration file.
        self.thresholds:Dict[str, Any] = ConfigLoader.get(
            key=None,
            different_file=self.config_file_path,
            read_all=True
        )

        Logger.info("Configurations retrieved successfully.")