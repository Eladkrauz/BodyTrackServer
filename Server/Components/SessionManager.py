###############################################################
##################### BODY TRACK // SERVER ####################
###############################################################
#################### CLASS: SessionManager ####################
###############################################################

###############
### IMPORTS ###
###############
import inspect, threading
from threading import Lock
from types import FrameType
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

#################################
### SESSION STATUS ENUM CLASS ###
#################################
class SessionStatus(enum):
    """
    ### Description:
    The `SessionStatus` enum class represents the statuses a session can be in.
    """
    REGISTERED = auto()
    ACTIVE     = auto()
    ENDED      = auto()
    PAUSED     = auto()
    NONE       = auto()

##############################
### SEARCH TYPE ENUM CLASS ###
##############################
class SearchType(enum):
    IP = auto()
    ID = auto()

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
    ###########################
    ### SESSION DATA FIELDS ###
    ###########################
    session_id: SessionId
    client_info: Dict[str, Any]
    exercise_type: str
    time: Dict[str, Optional[datetime]] = field(default_factory=lambda: {
        "registered": datetime.now(),
        "started": None,
        "paused": None,
        "ended": None,
        "last_activity": datetime.now()
    })
    frames_received: int = 0
    analysis_data: Dict[str, Any] = field(default_factory=dict)

    #########################
    ### UPDATE TIME STAMP ###
    #########################
    def update_time_stamp(self, session_status:SessionStatus) -> None:
        """
        ### Brief:
        The `update_time_stamp` method updates the times of a `SessionData` object.

        ### Arguments:
        - `session_status` (SessionStatus): The type of time to be updated.
        """
        now = datetime.now()
        if    session_status is SessionStatus.REGISTERED: self.time['registered'] = now
        elif  session_status is SessionStatus.ACTIVE:     self.time['started']    = now
        elif  session_status is SessionStatus.PAUSED:     self.time['paused']     = now
        elif  session_status is SessionStatus.ENDED:      self.time['ended']      = now
        else: Error.handle(error=ErrorCode.SESSION_STATUS_IS_NOT_RECOGNIZED, origin=inspect.currentframe())
        self.time['last_activity'] = now

#############################
### SESSION MANAGER CLASS ###
#############################
class SessionManager:
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self):
        # Locks.
        self.registered_lock     :Lock = threading.Lock()
        self.active_sessions_lock:Lock = threading.Lock()
        self.paused_sessions_lock:Lock = threading.Lock()
        self.ended_sessions_lock :Lock = threading.Lock()

        # Sessions.
        self.id_generator:SessionIdGenerator = SessionIdGenerator()
        self.registered     :dict[SessionId, SessionData] = {}
        self.active_sessions:dict[SessionId, SessionData] = {}
        self.paused_sessions:dict[SessionId, SessionData] = {}
        self.ended_sessions :dict[SessionId, SessionData] = {}

        # Supported exercises.
        self.supported_exercises:list = ConfigLoader.get(key=[
            ConfigParameters.Major.SESSION,
            ConfigParameters.Minor.SUPPORTED_EXERCIES
        ])

        # Maximum clients at the same time.
        self.maximum_clients:int = ConfigLoader.get(key=[
            ConfigParameters.Major.SESSION,
            ConfigParameters.Minor.MAXIMUM_CLIENTS
        ])

    ############################
    ### REGISTER NEW SESSION ###
    ############################
    def register_new_session(self, exercise_type:str, client_info:dict) -> SessionId | ICD.ErrorType:
        """
        ### Brief:
        Registers a new session for a client, provided the exercise type is supported and the client is not already registered.

        ### Arguments:
        - `exercise_type` (str): The type of exercise requested by the client.
        - `client_info` (dict): A dictionary containing client metadata, including IP address and optionally a unique ID or user-agent.

        ### Returns:
        - `SessionId`: A unique session identifier if the registration is successful.
        - `ICD.ErrorType`: An appropriate error type enum if the registration fails (e.g., unsupported exercise, duplicate registration).

        ### Notes:
        - If the exercise type is not listed in the system configuration, an error will be handled and returned.
        - If the client is already in a registered, active or paused session, the registration is denied.
        - Uses a lock to ensure thread-safe access to the session registry.
        """
        # If exercise type is invalid or not supported.
        if not self._is_exercise_supported(exercise_type):
            Error.handle(
                error=ErrorCode.EXERCISE_TYPE_DOES_NOT_EXIST,
                origin=inspect.currentframe(),
                extra_info={
                    "Sent from:": client_info.get('id', 'N/A'), 
                    "Supported exercises are": self.supported_exercises,
                    "Provided": exercise_type
                },
                critical=False
            )
            return ICD.ErrorType.EXERCISE_TYPE_NOT_SUPPORTED
        
        # Searching if the client exists already.
        session_status:SessionStatus = self._search(key=client_info['ip'], search_type=SearchType.IP, include_ended=False)

        # If client is already registered.
        if session_status is not SessionStatus.NONE:
            error_to_return, error_to_log = self._session_status_to_error(session_status)
            Error.handle(error=error_to_log, origin=inspect.currentframe())
            return error_to_return
        
        session_id:SessionId = self.id_generator.generate_session_id()
        # In case an error occured with generating the ID.
        if session_id is None:
            return ICD.ErrorType.CANT_REGISTER_CLIENT_TO_SESSION
        
        # Otherwise.
        new_session:SessionData = SessionData(session_id=session_id, client_info=client_info, exercise_type=exercise_type)

        # Register the new client. Locking registered sessions dictionary to control concurrency.
        with self.registered_lock:
            self.registered[session_id] = new_session

        Log.info(f"Session ID {session_id} was registered successfully to client {new_session.client_info['ip']}")
        return session_id
    
    ##########################
    ### UNREGISTER SESSION ###
    ##########################
    def unregister_session(self, session_id:SessionId) -> ICD.ResponseType | ICD.ErrorType:
        """
        ### Brief:
        The `unregister_session` method unregisters a session that has not yet started (is still in the REGISTERED state).
        
        ### Arguments:
        - `session_id` (SessionId): The unique session ID to be unregistered.
        
        ### Returns:
        - `ICD.ResponseType`: If unregistration succeeds, returns `CLIENT_SESSION_IS_UNREGISTERED`.
        - `ICD.ErrorType`: If the session is already started, paused, ended, or invalid, returns an appropriate error type.
        """
        # Checking if the session id is valid and packing it.
        session_id:SessionId = self.id_generator.pack_string_to_session_id(session_id) 
        if session_id is None:
            return ICD.ErrorType.INVALID_SESSION_ID
        
        # If the client is registered - meaning it has not started a session yet.
        session_status:SessionStatus = self._search(key=session_id, search_type=SearchType.ID)
        if session_status is SessionStatus.REGISTERED:
            with self.registered_lock:                
                # Removing the session from the registered dictionary.
                self.registered.pop(session_id)
                return ICD.ResponseType.CLIENT_SESSION_IS_UNREGISTERED
            
        # If the client is not in the registered dictionary - can't be unregistered.    
        else:
            error_to_return, error_to_log = self._session_status_to_error(session_status)
            Error.handle(error=error_to_log, origin=inspect.currentframe())
            return error_to_return

    #####################
    ### START SESSION ###
    #####################
    def start_session(self, session_id:str) -> ICD.ResponseType | ICD.ErrorType:
        """
        ### Brief:
        The `start_session` method starts a session that is currently in the `REGISTERED` state, transitioning it to `ACTIVE`.
        
        ### Arguments:
        - `session_id` (str): The session ID string received from the client.
        
        ### Returns:
        - `ICD.ResponseType`: Returns `CLIENT_SESSION_IS_ACTIVE` if the session is successfully activated.
        - `ICD.ErrorType`: Returns an appropriate error if:
            - The session ID is invalid.
            - The session is not in the `REGISTERED` state.
            - The system has reached the maximum number of concurrent active sessions.
        """
        # Checking if the session id is valid and packing it.
        session_id:SessionId = self.id_generator.pack_string_to_session_id(session_id) 
        if session_id is None:
            return ICD.ErrorType.INVALID_SESSION_ID
        
        # If the client is registered - meaning it has not started a session yet.
        session_status:SessionStatus = self._search(key=session_id, search_type=SearchType.ID)
        if session_status is SessionStatus.REGISTERED:
            with self.active_sessions_lock:
                # If active sessions reached maximum concurrent clients.
                if self._is_active_sessions_full():
                    Error.handle(
                        error=ErrorCode.MAX_CLIENT_REACHED,
                        origin=inspect.currentframe(),
                        extra_info={
                            "Current amount": len(self.active_sessions),
                            "Allowed amount": self.maximum_clients
                        }
                    )
                    return ICD.ErrorType.MAX_CLIENT_REACHED
                
                # If the session has room to become active.
                else:
                    with self.registered_lock:
                        # Removing the session from the registered dictionary.
                        session_data:SessionData = self.registered.pop(session_id)
                        # Adding it to the active sessions dictionary.
                        self.active_sessions[session_id] = session_data

            # Updating fields of the session.
            self.active_sessions[session_id].update_time_stamp(SessionStatus.ACTIVE)
            return ICD.ResponseType.CLIENT_SESSION_IS_ACTIVE

        # If the client is not registered or already started - it can't start the session.
        else:
            error_to_return, error_to_log = self._session_status_to_error(session_status)
            Error.handle(error=error_to_log, origin=inspect.currentframe())
            return error_to_return

    #####################
    ### PAUSE SESSION ###
    #####################
    def pause_session(self, session_id:str) -> ICD.ResponseType | ICD.ErrorType:
        """
        ### Brief:
        The `pause_session` method pauses an active session and moves it to the `paused_sessions` dictionary.
        
        ### Arguments:
        - `session_id` (str): The session ID as a string (to be packed into a `SessionId` object).
        
        ### Returns:
        - `ICD.ResponseType.CLIENT_SESSION_IS_RESUMED` if the session was successfully paused.
        - A specific `ICD.ErrorType` if the session ID is invalid or the session is not in the `ACTIVE` state.
        
        ### Notes:
        - A session can only be paused if it is currently active.
        - Internally, the session is removed from `active_sessions` and inserted into `paused_sessions`.
        - The session's timestamp is updated with `SessionStatus.PAUSED`.
        """
        # Checking if the session id is valid and packing it.
        session_id:SessionId = self.id_generator.pack_string_to_session_id(session_id) 
        if session_id is None:
            return ICD.ErrorType.INVALID_SESSION_ID
        
        # Checking if the session is actually active.
        session_status:SessionStatus = self._search(key=session_id, search_type=SearchType.ID)
        if session_status is SessionStatus.ACTIVE: # If the session is active.
            with self.paused_sessions_lock:
                with self.active_sessions_lock:
                    # Removing the session from the active sessions dictionary.
                    session_data:SessionData = self.active_sessions.pop(session_id)
                    # Adding it to the active sessions dictionary.
                    self.paused_sessions[session_id] = session_data

                self.paused_sessions[session_id].update_time_stamp(SessionStatus.PAUSED)
                return ICD.ResponseType.CLIENT_SESSION_IS_RESUMED
        
        else: # If the session is not paused.
            error_to_return, error_to_log = self._session_status_to_error(session_status)
            Error.handle(error=error_to_log, origin=inspect.currentframe())
            return error_to_return

    ######################
    ### RESUME SESSION ###
    ######################
    def resume_session(self, session_id:str) -> ICD.ResponseType | ICD.ErrorType:
        """
        ### Brief:
        The `resume_session` method resumes a paused session and moves it back to the `active_sessions` dictionary.

        ### Arguments:
        - `session_id` (str): The session ID as a string (to be packed into a `SessionId` object).

        ### Returns:
        - `ICD.ResponseType.CLIENT_SESSION_IS_RESUMED` if the session was successfully resumed.
        - `ICD.ErrorType.MAX_CLIENT_REACHED` if the server has reached the maximum number of concurrent active sessions.
        - A specific `ICD.ErrorType` if the session ID is invalid or the session is not in the `PAUSED` state.

        ### Notes:
        - A session can only be resumed if it is currently paused.
        - The method ensures that the number of active sessions does not exceed `self.maximum_clients`.
        - Internally, the session is removed from `paused_sessions` and inserted back into `active_sessions`.
        - The session's timestamp is updated with `SessionStatus.ACTIVE` to reflect resumption.
        """
        # Checking if the session id is valid and packing it.
        session_id:SessionId = self.id_generator.pack_string_to_session_id(session_id) 
        if session_id is None:
            return ICD.ErrorType.INVALID_SESSION_ID
        
        # Checking if the session is actually paused.
        session_status:SessionStatus = self._search(key=session_id, search_type=SearchType.ID)
        if session_status is SessionStatus.PAUSED: # If the session is paused.
            with self.active_sessions_lock:
                # If active sessions reached maximum concurrent clients.
                if self._is_active_sessions_full():
                    Error.handle(
                        error=ErrorCode.MAX_CLIENT_REACHED,
                        origin=inspect.currentframe(),
                        extra_info={
                            "Current amount": len(self.active_sessions),
                            "Allowed amount": self.maximum_clients
                        }
                    )
                    return ICD.ErrorType.MAX_CLIENT_REACHED
                
                # If the session has room to become active.
                else:
                    with self.paused_sessions_lock:
                        # Removing the session from the paused sessions dictionary.
                        session_data:SessionData = self.paused_sessions.pop(session_id)
                        # Adding it to the active sessions dictionary.
                        self.active_sessions[session_id] = session_data

                    self.active_sessions[session_id].update_time_stamp(SessionStatus.ACTIVE)
                    return ICD.ResponseType.CLIENT_SESSION_IS_RESUMED
        
        else: # If the session is not paused.
            error_to_return, error_to_log = self._session_status_to_error(session_status)
            Error.handle(error=error_to_log, origin=inspect.currentframe())
            return error_to_return

    ###################
    ### END SESSION ###
    ###################
    def end_session(self, session_id:str) -> ICD.ResponseType | ICD.ErrorType:
        """
        ### Brief:
        The `end_session` method ends an active or paused session and moves it into the `ended_sessions` dictionary.

        ### Arguments:
        - `session_id` (str): The session ID as a string (to be packed into a `SessionId` object).

        ### Returns:
        - `ICD.ResponseType.CLIENT_SESSION_IS_RESUMED` if the session was successfully ended.
        - A specific `ICD.ErrorType` if:
            - The session ID is invalid.
            - The session is neither in the `ACTIVE` nor `PAUSED` state.

        ### Notes:
        - If the session is currently `ACTIVE`, it is removed from `active_sessions` and added to `ended_sessions`.
        - If the session is currently `PAUSED`, it is removed from `paused_sessions` and added to `ended_sessions`.
        - The session's timestamp is updated with `SessionStatus.ENDED` to reflect the termination time.
        - If the session is not found or is already ended or not started, an appropriate error will be logged and returned.
        """
        # Checking if the session id is valid and packing it.
        session_id:SessionId = self.id_generator.pack_string_to_session_id(session_id) 
        if session_id is None:
            return ICD.ErrorType.INVALID_SESSION_ID
        
        # Checking if the session is active or paused.
        session_status:SessionStatus = self._search(key=session_id, search_type=SearchType.ID)
        if session_status is SessionStatus.ACTIVE: # If the session is active.
            with self.active_sessions_lock:
                with self.ended_sessions_lock:
                    # Removing the session from the active sessions dictionary.
                    session_data:SessionData = self.active_sessions.pop(session_id)
                    # Adding it to the ended sessions dictionary.
                    self.ended_sessions[session_id] = session_data

                self.ended_sessions[session_id].update_time_stamp(SessionStatus.ENDED)
                return ICD.ResponseType.CLIENT_SESSION_IS_RESUMED
        elif session_status is SessionStatus.PAUSED: # If the session is active.
            with self.paused_sessions_lock:
                with self.ended_sessions_lock:
                    # Removing the session from the paused sessions dictionary.
                    session_data:SessionData = self.paused_sessions.pop(session_id)
                    # Adding it to the ended sessions dictionary.
                    self.ended_sessions[session_id] = session_data

                self.ended_sessions[session_id].update_time_stamp(SessionStatus.ENDED)
                return ICD.ResponseType.CLIENT_SESSION_IS_RESUMED
        
        else: # If the session is not active or paused.Ø
            error_to_return, error_to_log = self._session_status_to_error(session_status)
            Error.handle(error=error_to_log, origin=inspect.currentframe())
            return error_to_return
        
    #####################
    ### PROCESS FRAME ###
    #####################
    # def process_frame(self, session_id:str, frame:FrameData) -> FrameFeedback | ICD.ErrorType:
        # pass
        # TODO: To be implemented.

    ###############################################
    #################### TASKS ####################
    ###############################################
    # TODO: To be added here: tasks like - clearing the ended_sessions dictionary once in a while.

    ##########################################################
    #################### HELPER FUNCTIONS ####################
    ##########################################################

    ###############################
    ### IS ACTIVE SESSIONS FULL ###
    ###############################
    def _is_active_sessions_full(self) -> bool:
        """
        ### Brief:
        The `_is_active_sessions_full` method returns whether the number of active session at the moment has reached its maximum.
        
        ### Returns:
        `True` if the `active_sessions` dictionary is full, `False` if not.
        
        ### Notes:
        The `self.maximum_clients` value is based on the configuration file.
        """
        return len(self.active_sessions) >= self.maximum_clients

    ##############
    ### SEARCH ###
    ##############
    def _search(self, key: str | SessionId, search_type:SearchType, include_ended: bool = True) -> SessionStatus:
        """
        ### Brief:
        The `_search` method searches for a session by either IP address or Session ID.
        
        ### Arguments:
        - `key` (str | SessionId): The IP address or session ID to search for.
        - `search_type` (SearchType): Enum value indicating whether the key is an IP or ID.
        - `include_ended` (bool): Whether to include ended sessions in the search. Default is `True`.
        
        ### Returns:
        - `SessionStatus`: The status of the session if found, otherwise `SessionStatus.NONE`.
        
        ### Raises:
        - `ValueError`: If the type of `key` does not match the `search_type`.
        """
        client_ip = None
        session_id = None

        # Checking which kind of search is required - based on client ip address, or on session id number.
        if search_type is SearchType.IP:
            if not isinstance(key, str):
                raise ValueError("Expected string for IP address.")
            client_ip = key
        elif search_type is SearchType.ID:
            if not isinstance(key, SessionId):
                raise ValueError("Expected SessionId for session ID.")
            session_id = key
        else:
            Error.handle(
                error=ErrorCode.SEARCH_TYPE_IS_NOT_SUPPORTED,
                origin=inspect.currentframe(),
                extra_info={
                    'provided': SearchType(search_type).name,
                    'supported': f"{SearchType.IP.name} or {SearchType.ID.name}"
                }
            )
            raise None

        # Begin session search.
        if self._is_client_registered(client_ip, session_id):
            return SessionStatus.REGISTERED
        if self._is_client_in_active_session(client_ip, session_id):
            return SessionStatus.ACTIVE
        if self._is_client_in_paused_session(client_ip, session_id):
            return SessionStatus.PAUSED
        if include_ended and self._is_client_in_ended_session(client_ip, session_id):
            return SessionStatus.ENDED

        return SessionStatus.NONE

    ############################
    ### IS CLIENT REGISTERED ###
    ############################
    def _is_client_registered(self, client_ip:str, session_id:SessionId) -> bool:
        """
        ### Brief:
        The `_is_client_registered` method checks if a specific client is currently in the `registered` sessions dictionary.
        
        ### Arguments:
        - `client_ip` (str): The client IP address to be checked.
        - `session_id` (SessionId): The session id to be checked.
       
        ### Returns:
        - `bool`:
          - `True` if the client is in the `registered` sessions.
          - `False` if the client is not registered.
        
        ### Notes:
        - Only one of the arguments can be a value, the other one must be `None`.  
        """
        # Checking in registered sessions.
        with self.registered_lock:
            # Search based on the IP address.
            if client_ip is not None:
                for session in self.registered.values():
                    if session.client_info.get("ip") == client_ip:
                        return True
            # Search based on the Session Id number.
            else: return self.registered.get(session_id, None) is not None

    ###################################
    ### IS CLIENT IN ACTIVE SESSION ###
    ###################################
    def _is_client_in_active_session(self, client_ip:str, session_id:SessionId) -> bool:
        """
        ### Brief:
        The `_is_client_in_active_session` method checks if a specific client is currently in the `active_sessions`.
        
        ### Arguments:
        - `client_ip` (str): The client IP address to be checked.
        - `session_id` (SessionId): The session id to be checked.
        
        ### Returns:
        - `bool`:
          - `True` if the client is in the `active_sessions`.
          - `False` if the client is not active.
        
        ### Notes:
        - Only one of the arguments can be a value, the other one must be `None`.  
        """
        # Checking in active sessions.
        with self.active_sessions_lock:
            # Search based on the IP address.
            if client_ip is not None:
                for session in self.active_sessions.values():
                    if session.client_info.get("ip") == client_ip:
                        return True
            # Search based on the Session Id number.
            else: return self.active_sessions.get(session_id, None) is not None

    ###################################
    ### IS CLIENT IN PAUSED SESSION ###
    ###################################
    def _is_client_in_paused_session(self, client_ip:str, session_id:SessionId) -> bool:
        """
        ### Brief:
        The `_is_client_in_paused_session` method checks if a specific client is currently in the `paused_sessions`.
        
        ### Arguments:
        - `client_ip` (str): The client IP address to be checked.
        - `session_id` (SessionId): The session id to be checked.
        
        ### Returns:
        - `bool`:
          - `True` if the client is in the `paused_sessions`.
          - `False` if the client is not paused.
        
        ### Notes:
        - Only one of the arguments can be a value, the other one must be `None`.  
        """
        # Checking in paused sessions.
        with self.paused_sessions_lock:
            # Search based on the IP address.
            if client_ip is not None:
                for session in self.paused_sessions.values():
                    if session.client_info.get("ip") == client_ip:
                        return True
            # Search based on the Session Id number.
            else: return self.paused_sessions.get(session_id, None) is not None

    ##################################
    ### IS CLIENT IN ENDED SESSION ###
    ##################################
    def _is_client_in_ended_session(self, client_ip:str, session_id:SessionId) -> bool:
        """
        ### Brief:
        The `_is_client_in_ended_session` method checks if a specific client is currently in the `ended_sessions`.
        
        ### Arguments:
        - `client_ip` (str): The client IP address to be checked.
        - `session_id` (SessionId): The session id to be checked.
        
        ### Returns:
        - `bool`:
          - `True` if the client is in the `ended_sessions`.
          - `False` if the client is not ended.
        
        ### Notes:
        - Only one of the arguments can be a value, the other one must be `None`.  
        """
        # Checking in ended sessions.
        with self.ended_sessions_lock:
            # Search based on the IP address.
            if client_ip is not None:
                for session in self.ended_sessions.values():
                    if session.client_info.get("ip") == client_ip:
                        return True
            # Search based on the Session Id number.
            else: return self.ended_sessions.get(session_id, None) is not None
    
    ###############################
    ### SESSION STATUS TO ERROR ###
    ###############################
    def _session_status_to_error(self, status:SessionStatus) -> tuple[ICD.ErrorType, ErrorCode]:
        """
        ### Brief:
        The `_session_status_to_log_error_code` method converts a `SessionStatus` object into a tuple of `ICD.ErrorType` and `ErrorCode`.
        
        ### Arguments:
        - `status` (SessionStatus): The session status to be converted.
        
        ### Returns:
        - The converted `tuple`.
        """
        if status is SessionStatus.REGISTERED: return ICD.ErrorType.CLIENT_IS_ALREADY_REGISTERED, ErrorCode.CLIENT_IS_ALREADY_REGISTERED
        elif status is SessionStatus.ACTIVE:   return ICD.ErrorType.CLIENT_IS_ALREADY_ACTIVE,     ErrorCode.CLIENT_IS_ALREADY_ACTIVE
        elif status is SessionStatus.PAUSED:   return ICD.ErrorType.CLIENT_IS_ALREADY_PAUSED,     ErrorCode.CLIENT_IS_ALREADY_PAUSED
        elif status is SessionStatus.ENDED:    return ICD.ErrorType.CLIENT_IS_ALREADY_ENDED,      ErrorCode.CLIENT_IS_ALREADY_ENDED
        else:                                  return ICD.ErrorType.CLIENT_IS_NOT_REGISTERED,     ErrorCode.CLIENT_IS_NOT_REGISTERED

    #############################
    ### IS EXERCISE SUPPORTED ###
    #############################
    def _is_exercise_supported(self, exercise_type:str) -> bool:
        """
        ### Brief:
        The `_is_exercise_supported` method gets an exercise type and returns whether it's supported or not.
        
        ### Arguments:
        `exercise_type` (str): The exercise type.
        
        ### Returns:
        `True` if the exercise is supported, `False` if not.
        """
        if exercise_type is None:
            return False
        elif exercise_type not in self.supported_exercises:
            return False
        else:
            return True