###############################################################
##################### BODY TRACK // SERVER ####################
###############################################################
#################### CLASS: SessionManager ####################
###############################################################

###############
### IMPORTS ###
###############
import inspect, threading
from datetime import datetime
from enum import Enum as enum
from enum import auto
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from Utilities.SessionIdGenerator import SessionIdGenerator, SessionId
from Utilities.ConfigLoader import ConfigLoader, ConfigParameters
from Utilities.ErrorHandler import ErrorHandler as Error
from Utilities.ErrorHandler import ErrorCode
from Common.ClientServerIcd import ClientServerIcd as ICD
from Utilities.Logger import Logger as Log

############################
### SESSION STATUS CLASS ###
############################
class SessionStatus(enum):
    """
    ### Description:
    The `SessionStatus` enum class represents the statuses a session can be in.
    """
    REGISTERED = auto()
    ACTIVE     = auto()
    IN_PROCESS = auto()
    ENDED      = auto()
    PAUSED     = auto()

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
    - `client_info` (dict[str, Any]): Metadata about the client device/IP.
    - `exercise_type` (str): The type of exercise (e.g., "squats", "pushups").
    - `time` (dict[str, datetime]): Timestamps about the sessions.
    - `frames_received` (int): Total number of frames received during the session.
    - `status` (str): Current session status, e.g., "active", "ended", "paused".
    - `analysis_data` (dict[str, Any]): Holds pose analysis results and feedback (optional).
    """
    session_id: SessionId
    client_info: Dict[str, Any]
    exercise_type: str
    time: Dict[str, Optional[datetime]] = field(default_factory=lambda: {
        "registered": datetime.now(),
        "started": None,
        "ended": None,
        "last_activity": None
    })
    frames_received: int = 0
    status: SessionStatus = SessionStatus.REGISTERED
    analysis_data: Dict[str, Any] = field(default_factory=dict)

#############################
### SESSION MANAGER CLASS ###
#############################
class SessionManager:
    def __init__(self):
        # Lock.
        self.lock = threading.Lock()
        # Sessions.
        self.id_generator = SessionIdGenerator()
        self.registered_sessions:dict[SessionId, SessionData] = {}
        self.active_sessions:dict[SessionId, SessionData] = {}
        self.paused_sessions:dict[SessionId, SessionData] = {}
        self.ended_sessions:dict[SessionId, SessionData] = {}

        # Supported exercises.
        self.supported_exercises = ConfigLoader.get(key=[
            ConfigParameters.Major.SESSION,
            ConfigParameters.Minor.SUPPORTED_EXERCIES
        ])

        # Maximum clients at the same time.
        self.maximum_clients = ConfigLoader.get(key=[
            ConfigParameters.Major.SESSION,
            ConfigParameters.Minor.MAXIMUM_CLIENTS
        ])

    ############################
    ### REGISTER NEW SESSION ###
    ############################
    def register_new_session(self, exercise_type:str, client_info:dict) -> SessionId | ICD.ErrorType:
        if exercise_type is None or exercise_type not in self.supported_exercises:
            Error.handle(
                opcode=ErrorCode.EXERCISE_TYPE_DOES_NOT_EXIST,
                origin=inspect.currentframe(),
                message="Exercise type is not configured in the system.",
                extra_info={
                    "Sent from:": client_info.get('id', 'N/A')
                },
                critical=False
            )
            return ICD.ErrorType.EXERCISE_TYPE_NOT_SUPPORTED
        
        session_id = self.id_generator.generate_session_id()
        if session_id is None: # In case an error occured with generating the ID.
            return ICD.ErrorType.CANT_REGISTER_CLIENT_TO_SESSION
        new_session = SessionData(
            session_id=session_id,
            client_info=client_info,
            exercise_type=exercise_type
        )

        # Register the new client.
        with self.lock:
            if len(self.registered_sessions) >= self.maximum_clients:
                return ICD.ErrorType.MAX_CLIENT_REACHED
            self.registered_sessions[session_id] = new_session

        Log.info(f"Session ID {session_id} was registered successfully to client {new_session.client_info['id']}")
        return session_id