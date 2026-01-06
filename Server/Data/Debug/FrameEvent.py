###############################################################
############# BODY TRACK // SERVER // DATA // DEBUG ###########
###############################################################
###################### CLASS: FrameEvent ######################
###############################################################
 
###############
### IMPORTS ###
###############
from dataclasses import dataclass
from typing import Dict, Any, Optional

#########################
### FRAME EVENT CLASS ###
#########################
@dataclass
class FrameEvent:
    """
    ### Description:
    The `FrameEvent` class represents a single event that occurs during the processing of a frame.
    """
    stage: str
    success: bool
    result_type: str
    result: Dict[str, Any]
    info: Optional[Dict[str, Any]] = None

    ###############
    ### TO DICT ###
    ###############
    def to_dict(self) -> Dict[str, Any]:
        """
        ### Brief:
        The `to_dict` method converts the `FrameEvent` instance into a dictionary format.

        ### Returns:
        A dictionary representation of the `FrameEvent` instance, including its stage,
        success status, result type, result data, and optional info.
        """
        return {
            "stage":        self.stage,
            "success":      self.success,
            "result_type":  self.result_type,
            "result":       self.result,
            "info":         self.info
        }