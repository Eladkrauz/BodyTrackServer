###############################################################
############# BODY TRACK // SERVER // DATA // DEBUG ###########
###############################################################
###################### CLASS: FrameTrace ######################
###############################################################
 
###############
### IMPORTS ###
###############
from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime

from Data.Debug.FrameEvent import FrameEvent

#########################
### FRAME TRACE CLASS ###
#########################
@dataclass
class FrameTrace:
    """
    ### Description:
    The `FrameTrace` class represents a detailed trace of events that occurred
    during the processing of a single frame in a system.
    """
    frame_id:  int
    timestamp: str              = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    events:    List[FrameEvent] = field(default_factory=list)
    streaks:   Dict[str, int]   = field(default_factory=dict)

    ###############
    ### TO DICT ###
    ###############
    def to_dict(self) -> Dict[str, Any]:
        """
        ### Brief:
        The `to_dict` method converts the `FrameTrace` instance into a dictionary format.

        ### Returns:
        A dictionary representation of the `FrameTrace` instance, including its frame ID,
        timestamp, and a list of events.
        """
        return {
            "frame_id":     self.frame_id,
            "timestamp":    self.timestamp,
            "events":       [ e.to_dict() for e in self.events ],
            "streaks":      self.streaks
        }
    
    #################
    ### ADD EVENT ###
    #################
    def add_event(
        self, stage:str, success:bool, result_type:str,
        result:Dict[str, Any], info:Dict[str, Any] = None
    ) -> None:
        """
        ### Brief:
        The `add_event` method adds a new `FrameEvent` to the `events` list of the `FrameTrace`.

        ### Parameters:
        - `stage` (str): The stage of processing (e.g., "JointAnalyzer", "PhaseDetector").
        - `success` (bool): Indicates whether the stage was successful.
        - `result_type` (str): The type of result (e.g., "angles", "phase", "exception").
        - `result` (Dict[str, Any]): A simple (JSON-safe) representation of the result.
        - `info` (Dict[str, Any], optional): Additional information about the event.
        """
        self.events.append(
            FrameEvent(
                stage=stage,
                success=success,
                result_type=result_type,
                result=result,
                info=info
            )
        )

    ##################
    ### ADD STREAK ###
    ##################
    def add_streak(self, streaks:Dict[str, int]) -> None:
        """
        ### Brief:
        The `add_streak` method adds streak information to the `streaks`
        dictionary of the `FrameTrace`.

        ### Arguments:
        - `streaks` (Dict[str, int]): A dictionary containing streak information.
        """
        self.streaks = streaks