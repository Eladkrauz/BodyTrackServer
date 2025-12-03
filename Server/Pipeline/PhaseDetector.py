############################################################
############# BODY TRACK // SERVER // PIPELINE #############
############################################################
################### CLASS: PhaseDetector ###################
############################################################

###############
### IMPORTS ###
###############
from typing import Dict, Any

from Server.Data.Session.SessionData  import SessionData
from Server.Data.Phase.PhaseType      import PhaseType

from Server.Utilities.Error.ErrorCode import ErrorCode

############################
### PHASE DETECTOR CLASS ###
############################
class PhaseDetector:
    pass

    def __init__(self):
        pass

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

        # Reading frames rolling window size.
        self.frames_rolling_window_size:int = ConfigLoader.get([
            ConfigParameters.Major.HISTORY,
            ConfigParameters.Minor.FRAMES_ROLLING_WINDOW_SIZE
        ])
        if self.frames_rolling_window_size is None:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_INIT_ERROR,
                origin=inspect.currentframe(),
                extra_info={ "Frames rolling window size": "Not found in the configuration file" }
            )
            self.frames_rolling_window_size = None # Using unlimited.