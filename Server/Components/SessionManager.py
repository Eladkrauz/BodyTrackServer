###############################################################
##################### BODY TRACK // SERVER ####################
###############################################################
#################### CLASS: SessionManager ####################
###############################################################

###############
### IMPORTS ###
###############
# from Utilities.Logger import Logger
# from Utilities.ErrorHandler import ErrorHandler, ErrorCode
import inspect
from datetime import datetime
from enum import Enum as enum
from enum import auto
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from Utilities.SessionIdGeneratorMock import GenerateSessionId

############################
### SESSION STATUS CLASS ###
############################
class SessionStatus(enum):
    """
    ### Description:
    The `SessionStatus` enum class represents the statuses a session can be in.
    """
    ACTIVE = auto()
    ENDED  = auto()
    PAUSED = auto()

##########################
### SESSION DATA CLASS ###
##########################
@dataclass
class SessionData:
    """
    ### Brief:
    The `SessionData` represents metadata and runtime details for a single exercise session.

    ### Fields:
    - `session_id` (str): Unique session identifier.
    - `exercise_type` (str): The type of exercise (e.g., "squats", "pushups").
    - `start_time` (datetime): Timestamp when the session began.
    - `last_activity_time` (datetime): Last time we received any data for this session.
    - `frames_received` (int): Total number of frames received during the session.
    - `status` (str): Current session status, e.g., "active", "ended", "paused".
    - `analysis_data` (dict[str, Any]): Holds pose analysis results and feedback (optional).
    - `client_info` (dict[str, Any]): Optional metadata about the client device/IP.
    """
    session_id: str
    exercise_type: str
    start_time: datetime = field(default_factory=datetime.now)
    last_activity_time: datetime = field(default_factory=datetime.now)
    frames_received: int = 0
    status: SessionStatus = SessionStatus.ACTIVE
    analysis_data: Dict[str, Any] = field(default_factory=dict)
    client_info: Optional[Dict[str, Any]] = field(default_factory=dict)
