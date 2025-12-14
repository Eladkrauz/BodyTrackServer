###############################################################
############## BODY TRACK // SERVER // MANAGEMENT #############
###############################################################
#################### CLASS: SessionManager ####################
###############################################################

###############
### IMPORTS ###
###############
# Python libraries.
import inspect, threading, time, psutil, os
import numpy   as np
from threading import RLock
from datetime  import datetime

# Utilities.
from Server.Utilities.SessionIdGenerator      import SessionIdGenerator, SessionId
from Server.Utilities.Error.ErrorHandler      import ErrorHandler
from Server.Utilities.Error.ErrorCode         import ErrorCode, ErrorResponse
from Server.Utilities.Logger                  import Logger

# Pipeline.
from Server.Pipeline.PipelineProcessor        import PipelineProcessor

# Data.
from Server.Data.Session.SessionStatus        import SessionStatus
from Server.Data.Session.SearchType           import SearchType
from Server.Data.Session.ExerciseType         import ExerciseType
from Server.Data.Session.SessionData          import SessionData
from Server.Data.Session.FrameData            import FrameData
from Server.Data.Session.AnalyzingState       import AnalyzingState
from Server.Data.Response.FeedbackResponse    import FeedbackCode, FeedbackResponse
from Server.Data.Response.ManagementResponse  import ManagementCode, ManagementResponse
from Server.Data.Response.CalibrationResponse import CalibrationCode, CalibrationResponse

#############################
### SESSION MANAGER CLASS ###
#############################
class SessionManager:
    """
    ### Description:
    The `SessionManager` class is responsible for managing client sessions in the Body Track server.
    It handles session registration, starting, pausing, resuming, ending, and frame analysis.
    It maintains session states and ensures thread-safe operations using locks.
    """
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self):
        """
        ### Brief:
        The `__init__` method initialized the `SessionManager` instance.
        """
        # The pipeline processor.
        self.pipeline_processor = PipelineProcessor()

        # Configurations.
        self.retrieve_configurations()

        # Sessions.
        self.id_generator:SessionIdGenerator       = SessionIdGenerator()
        self.sessions:dict[SessionId, SessionData] = {}
        self.sessions_lock:RLock                   = RLock()
        self.current_active_sessions:int           = 0
        self.ip_map:dict[str, SessionId]           = {}
        self.ip_map_lock:RLock                     = RLock()

        # Tasks.
        self._cleanup_thread = threading.Thread(target=self._cleanup_task, daemon=True)
        self._config_retrieve_thread = threading.Thread(target=self._retrieve_config_task, daemon=True)
        # self._cleanup_thread.start()
        # self._config_retrieve_thread.start()

        # Done initializing.
        Logger.info("Initialized successfully")

    #################################################################################################
    ############################## SESSION REGISTRATION AND MANAGEMENT ##############################
    #################################################################################################

    ############################
    ### REGISTER NEW SESSION ###
    ############################
    def register_new_session(self, exercise_type:str, client_info:dict) -> ManagementResponse | ErrorResponse:
        """
        ### Brief:
        The `register_new_session` method registers a new session for a client, provided the
        exercise type is supported and the client is not already registered.

        ### Arguments:
        - `exercise_type` (str): The type of exercise requested by the client.
        - `client_info` (dict): A dictionary containing client metadata, including IP address
                                and optionally a unique ID or user-agent.

        ### Returns:
        - `ManagementResponse`: A management response with the session identifier if successful.
        - `ErrorResponse`: An appropriate error response if the registration fails
                           (e.g., unsupported exercise, duplicate registration).

        ### Notes:
        - If the exercise type is not listed in the system configuration, an error will be handled and returned.
        - If the client is already in a registered, active or paused session, the registration is denied.
        - Uses a lock to ensure thread-safe access to the session registry.
        """
        # If exercise type is invalid or not supported.
        provided_type:str = exercise_type
        exercise_type:ExerciseType = self._is_exercise_supported(provided_type)
        if exercise_type is None:
            ErrorHandler.handle(
                error=ErrorCode.EXERCISE_TYPE_DOES_NOT_EXIST,
                origin=inspect.currentframe(),
                extra_info={
                    "Sent from:": client_info.get('id', 'N/A'), 
                    "Supported exercises are": self.supported_exercises,
                    "Provided": provided_type
                }
            )
            return ErrorResponse(ErrorCode.EXERCISE_TYPE_DOES_NOT_EXIST)

        # Searching if the client exists already.
        session_status:SessionStatus = self._search(key=client_info['ip'], search_type=SearchType.IP, include_ended=False)

        # If client is already registered.
        if session_status is not SessionStatus.NOT_IN_SYSTEM:
            with self.ip_map_lock:
                error_code:ErrorCode = self._session_status_to_error(session_status)
                print("ID:", self.ip_map.get(client_info['ip']).id)
                ErrorHandler.handle(error=error_code, origin=inspect.currentframe())
                return ErrorResponse(
                    error_code=error_code,
                    extra_info={ "session_id": self.ip_map.get(client_info['ip']).id }
                )
        
        # If the session is not registered - registering it.
        session_id:SessionId = self.id_generator.generate_session_id()
        # In case an error occured with generating the ID.
        if session_id is None:
            return ErrorResponse(ErrorCode.ERROR_GENERATING_SESSION_ID)
        
        # Otherwise.
        try:
            session_data:SessionData = SessionData(
                session_id=session_id,
                client_info=client_info,
                exercise_type=exercise_type
            )
        except Exception: # In case the SessionData object failed to initialize.
            return ErrorResponse(ErrorCode.ERROR_CREATING_SESSION_DATA)

        # Register the new client. Locking sessions dictionary to control concurrency.
        with self.sessions_lock:
            self.sessions[session_id] = session_data
            session_data.set_session_status(SessionStatus.REGISTERED)
        
        # Adding the ip -> id mapping to the ip_map dictionary.
        with self.ip_map_lock:
            self.ip_map[client_info["ip"]] = session_id

        Logger.info(f"Session ID {session_id} was registered successfully to client {session_data.client_info['ip']}")
        return ManagementResponse(
            management_code=ManagementCode.CLIENT_REGISTERED_SUCCESSFULLY,
            extra_info={ "session_id": session_id.id }
        )
    
    ##########################
    ### UNREGISTER SESSION ###
    ##########################
    def unregister_session(self, session_id:SessionId) -> ManagementResponse | ErrorResponse:
        """
        ### Brief:
        The `unregister_session` method unregisters a session that has not yet started (is still in the REGISTERED state).
        
        ### Arguments:
        - `session_id` (SessionId): The unique session ID to be unregistered.
        
        ### Returns:
        - `ManagementResponse`: If unregistration succeeds, returns `CLIENT_SESSION_IS_UNREGISTERED`.
        - `ErrorResponse`: If the session is already started, paused, ended, or invalid, returns an appropriate error type.
        """
        # Checking if the session id is valid and packing it.
        session_id:SessionId = self.id_generator.pack_string_to_session_id(session_id) 
        if session_id is None:
            return ErrorResponse(ErrorCode.INVALID_SESSION_ID)
        
        # If the client is registered - meaning it has not started a session yet.
        session_status:SessionStatus = self._search(key=session_id, search_type=SearchType.ID)
        if session_status is SessionStatus.REGISTERED:
            # Removing the session from the sessions dictionary.
            with self.sessions_lock:
                session_data:SessionData = self.sessions.pop(session_id, None)        

            # Removing the ip -> id mapping from the ip_map dictionary.
            with self.ip_map_lock:
                self.ip_map.pop(session_data.client_info.get("ip"), None)
            
            return ManagementResponse(ManagementCode.CLIENT_SESSION_IS_UNREGISTERED)
            
        # If the client is not in the registered dictionary - can't be unregistered.    
        else:
            error_code:ErrorCode = self._session_status_to_error(session_status)
            ErrorHandler.handle(error=error_code, origin=inspect.currentframe())
            return ErrorResponse(error_code)

    #####################
    ### START SESSION ###
    #####################
    def start_session(self, session_id:str, extended_evaluation:bool) -> ManagementResponse | ErrorResponse:
        """
        ### Brief:
        The `start_session` method starts a session that is currently in the `REGISTERED` state, transitioning it to `ACTIVE`.
        
        ### Arguments:
        - `session_id` (str): The session ID string received from the client.
        - `extended_evaluation` (bool): If `True`, calculate all biomechanical angles; 
        if `False`, calculate only those needed for evaluating correctness (core movement).
        
        ### Returns:
        - `ManagementResponse`: Returns `CLIENT_SESSION_IS_ACTIVE` if the session is successfully activated.
        - `ErrorResponse`: Returns an appropriate error if:
            - The session ID is invalid.
            - The session is not in the `REGISTERED` state.
            - The system has reached the maximum number of concurrent active sessions.
        """
        # Checking if the session id is valid and packing it.
        session_id:SessionId = self.id_generator.pack_string_to_session_id(session_id) 
        if session_id is None:
            return ErrorResponse(ErrorCode.INVALID_SESSION_ID)
        
        # Checking if the exetended evaluation parameter is valid.
        if extended_evaluation is None or not isinstance(extended_evaluation, bool):
            ErrorHandler.handle(
                error=ErrorCode.INVALID_EXTENDED_EVALUATION_PARAM,
                origin=inspect.currentframe()
            )
            return ErrorResponse(ErrorCode.INVALID_EXTENDED_EVALUATION_PARAM)
        
        # If the client is registered - meaning it has not started a session yet.
        session_status:SessionStatus = self._search(key=session_id, search_type=SearchType.ID)
        if session_status is SessionStatus.REGISTERED:
            with self.sessions_lock:
                # If active sessions reached maximum concurrent clients.
                if self._is_active_sessions_full():
                    ErrorHandler.handle(
                        error=ErrorCode.MAX_CLIENT_REACHED,
                        origin=inspect.currentframe(),
                        extra_info={
                            "Current amount": self.current_active_sessions,
                            "Allowed amount": self.maximum_clients
                        }
                    )
                    return ErrorResponse(ErrorCode.MAX_CLIENT_REACHED)
                
                # If the session has room to become active.
                else:
                    session_data:SessionData = self.sessions[session_id]
                    session_data.set_session_status(SessionStatus.ACTIVE)
                    self.current_active_sessions += 1
                    session_data.set_extended_evaluation(extended_evaluation)

                    # Marking exercise started in the history.
                    with session_data.lock:
                        self.pipeline_processor.start(session_data.get_history())

                    return ManagementResponse(ManagementCode.CLIENT_SESSION_IS_ACTIVE)

        # If the client is not registered or already started - it can't start the session.
        else:
            error_code:ErrorCode = self._session_status_to_error(session_status)
            ErrorHandler.handle(error=error_code, origin=inspect.currentframe())
            return ErrorResponse(error_code)

    #####################
    ### PAUSE SESSION ###
    #####################
    def pause_session(self, session_id:str) -> ManagementResponse | ErrorResponse:
        """
        ### Brief:
        The `pause_session` method pauses an active session and moves it to the `paused_sessions` dictionary.
        
        ### Arguments:
        - `session_id` (str): The session ID as a string (to be packed into a `SessionId` object).
        
        ### Returns:
        - `ManagementResponse` if the session was successfully paused.
        - A specific `ErrorResponse` if the session ID is invalid or the session is not in the `ACTIVE` state.
        
        ### Notes:
        - A session can only be paused if it is currently active.
        - The session's timestamp is updated with `SessionStatus.PAUSED`.
        """
        # Checking if the session id is valid and packing it.
        session_id:SessionId = self.id_generator.pack_string_to_session_id(session_id) 
        if session_id is None:
            return ErrorResponse(ErrorCode.INVALID_SESSION_ID)
        
        # Checking if the session is actually active.
        session_status:SessionStatus = self._search(key=session_id, search_type=SearchType.ID)
        if session_status is SessionStatus.ACTIVE: # If the session is active.
            with self.sessions_lock:
                session_data:SessionData = self.sessions[session_id]
                session_data.set_session_status(SessionStatus.PAUSED)
                self.current_active_sessions -= 1
                self.pipeline_processor.pause(session_data.get_history())
                return ManagementResponse(ManagementCode.CLIENT_SESSION_IS_PAUSED)
        # If the session is not active.
        else:
            error_code:ErrorCode = self._session_status_to_error(session_status)
            ErrorHandler.handle(error=error_code, origin=inspect.currentframe())
            return ErrorResponse(error_code)

    ######################
    ### RESUME SESSION ###
    ######################
    def resume_session(self, session_id:str) -> ManagementResponse | ErrorResponse:
        """
        ### Brief:
        The `resume_session` method resumes a paused session and moves it back to the `ACTIVE` status.

        ### Arguments:
        - `session_id` (str): The session ID as a string (to be packed into a `SessionId` object).

        ### Returns:
        - `ManagementResponse` if the session was successfully resumed.
        - `ErrorResponse` with `MAX_CLIENT_REACHED` if the server has reached the maximum number of concurrent active sessions.
        - A specific `ErrorResponse` if the session ID is invalid or the session is not in the `PAUSED` state.

        ### Notes:
        - A session can only be resumed if it is currently paused.
        - The method ensures that the number of active sessions does not exceed `self.maximum_clients`.
        - The session's timestamp is updated with `SessionStatus.ACTIVE` to reflect resumption.
        """
        # Checking if the session id is valid and packing it.
        session_id:SessionId = self.id_generator.pack_string_to_session_id(session_id) 
        if session_id is None:
            return ErrorResponse(ErrorCode.INVALID_SESSION_ID)
        
        # Checking if the session is actually paused.
        session_status:SessionStatus = self._search(key=session_id, search_type=SearchType.ID)
        if session_status is SessionStatus.PAUSED: # If the session is paused.
            with self.sessions_lock:
                # If active sessions reached maximum concurrent clients.
                if self._is_active_sessions_full():
                    ErrorHandler.handle(
                        error=ErrorCode.MAX_CLIENT_REACHED,
                        origin=inspect.currentframe(),
                        extra_info={
                            "Current amount": self.current_active_sessions,
                            "Allowed amount": self.maximum_clients
                        }
                    )
                    return ErrorResponse(ErrorCode.MAX_CLIENT_REACHED)
                
                # If the session has room to become active.
                else:
                    session_data:SessionData = self.sessions[session_id]
                    session_data.set_session_status(SessionStatus.ACTIVE)
                    self.current_active_sessions += 1
                    self.pipeline_processor.resume(session_data.get_history())
                    return ManagementResponse(ManagementCode.CLIENT_SESSION_IS_RESUMED)
                
        # If the session is not paused.
        else:
            error_code:ErrorCode = self._session_status_to_error(session_status)
            ErrorHandler.handle(error=error_code, origin=inspect.currentframe())
            return ErrorResponse(error_code)

    ###################
    ### END SESSION ###
    ###################
    def end_session(self, session_id:str) -> ManagementResponse | ErrorResponse:
        """
        ### Brief:
        The `end_session` method ends an active or paused session and moves it into the `ended_sessions` dictionary.

        ### Arguments:
        - `session_id` (str): The session ID as a string (to be packed into a `SessionId` object).

        ### Returns:
        - `ManagementResponse` if the session was successfully ended.
        - A specific `ErrorResponse` if:
            - The session ID is invalid.
            - The session is neither in the `ACTIVE` nor `PAUSED` state.

        ### Notes:
        - The session's timestamp is updated with `SessionStatus.ENDED` to reflect the termination time.
        - If the session is not found or is already ended or not started, an appropriate error will be logged and returned.
        """
        # Checking if the session id is valid and packing it.
        session_id:SessionId = self.id_generator.pack_string_to_session_id(session_id) 
        if session_id is None:
            return ErrorResponse(ErrorCode.INVALID_SESSION_ID)
        
        # Checking if the session is active or paused.
        session_status:SessionStatus = self._search(key=session_id, search_type=SearchType.ID)
        # If the session is active or paused.
        if session_status is SessionStatus.ACTIVE or session_status is SessionStatus.PAUSED:
            with self.sessions_lock:
                session_data:SessionData = self.sessions[session_id]
                session_data.set_session_status(SessionStatus.ENDED)
                self.current_active_sessions -= 1
            
            with self.ip_map_lock:
                self.ip_map.pop(session_data.client_info.get("ip"), None)

            # Marking exercise ended in the history.
            with session_data.lock:
                self.pipeline_processor.end(session_data.get_history())
                session_data.set_analyzing_state(AnalyzingState.DONE)
            
            # TODO: Add summary creation here using the final HistoryData values.
            return ManagementResponse(ManagementCode.CLIENT_SESSION_IS_ENDED)
            
        # If the session is not active or paused.
        else:
            error_code:ErrorCode = self._session_status_to_error(session_status)
            ErrorHandler.handle(error=error_code, origin=inspect.currentframe())
            return ErrorResponse(error_code)       

    ############################################################################
    ############################## FRAME ANALYSIS ##############################
    ############################################################################
        
    #####################
    ### ANALYZE FRAME ###
    #####################
    def analyze_frame(
            self, session_id:str, frame_id:int, frame_content:np.ndarray
        ) -> CalibrationResponse | FeedbackResponse | ErrorResponse:
        """
        ### Brief:
        The `analyze_frame` method recieves frames from the client and sends them to analysis.
        The analysis performed is based on the `AnalyzingState` of the session:

        #### `AnalyzingState.INIT`:
        This step means the session is not yet stable, and we are recieving frames that are not
        recorded in `HistoryData` of the session. This part is for making sure the user is visible, the
        lighting is okay and the visibility is good. We move from this step to the next after recieveing
        predefined amount of `PoseQuality.OK` frames after analysis in the `PoseQualityManager`.
        ##### Pipeline of this step:
        - `PoseAnalyzer`
        - `PoseQualityManager`

        #### `AnalyzingState.READY`:
        This step means the session is stable, and we are now recieving frames for determining if the
        user's position alings with the predefined `ExerciseType`'s initial position. We move from this
        step to the next after recieving predefined amount of `CORRECT_POSITION` from the `PhaseDetector`.
        ##### Pipeline of this step:
        - `PoseAnalyzer`
        - `PoseQualityManager`
        - `JointAnalyzer`
        - `PhaseDetector`

        #### `AnalyzingState.ACTIVE`:
        This step means the session is active after ensuring the user is in the correct inital position
        of the `ExerciseType`, and the frame is valid in terms of visibility.
        #### The pipeline of this step is the full pipeline - from analysis to feedback after phase and error detections.

        ### Arguments:
        - `session_id` (str): The session id `str` recieved from the `FlaskServer`, from the request's `JSON`.
        - `frame_id` (int): The frame id number.
        - `frame_content` (np.ndarray): The frame array content, after decoding.

        ### Returns:
        - `CalibrationResponse` or `FeedbackResponse` if the analysis performed successfully.
        - `ErrorResponse` if an error occured during analysis.
        """
        # Checking if the session id is valid and packing it.
        session_id:SessionId = self.id_generator.pack_string_to_session_id(session_id) 
        if session_id is None:
            return ErrorResponse(ErrorCode.INVALID_SESSION_ID)
        
        # Checking if the session is active.
        session_status:SessionStatus = self._search(key=session_id, search_type=SearchType.ID)
        if session_status is not SessionStatus.ACTIVE:
            error_code:ErrorCode = ErrorCode.CLIENT_IS_NOT_ACTIVE
            ErrorHandler.handle(
                error=error_code,
                origin=inspect.currentframe()
            )
            ErrorResponse(error_code)

        # Retrieving the session data.
        with self.sessions_lock:
            session_data:SessionData = self.sessions.get(session_id)
        
        ### STARTING ###
        with session_data.lock:
            # Updating the session's last activity time stamp.
            if session_data.update_time_stamp() is not None: # Updating last activity.
                error_code:ErrorCode = ErrorCode.SESSION_STATUS_IS_NOT_RECOGNIZED
                ErrorHandler.handle(error=error_code, origin=inspect.currentframe())
                return ErrorResponse(error_code)
            
            # Validating the frame.
            frame_data:FrameData | ErrorCode = self.pipeline_processor.validate_frame(
                session_id=session_id,
                frame_id=frame_id,
                content=frame_content
            )
            if isinstance(frame_data, ErrorCode): return ErrorResponse(frame_data)
            
            # Routing the frame to analysis based on the session analysis state.
            self.pipeline_processor.analyze_frame_in_ready_state(session_data, frame_data)
            
            state:AnalyzingState = session_data.analyzing_state
            if state is AnalyzingState.INIT:
                initial_analysis_result:CalibrationCode | ErrorCode \
                    = self.pipeline_processor.analyze_frame_in_init_state(session_data, frame_data)
                if isinstance(initial_analysis_result, CalibrationCode):
                    return CalibrationResponse(initial_analysis_result)
                else:
                    return ErrorResponse(initial_analysis_result)

            elif state is AnalyzingState.READY:
                position_analysis_result:CalibrationCode | ErrorCode \
                    = self.pipeline_processor.analyze_frame_in_ready_state(session_data, frame_data)
                if isinstance(position_analysis_result, CalibrationCode):
                    return CalibrationResponse(position_analysis_result)
                else:
                    return ErrorResponse(position_analysis_result)

            elif state is AnalyzingState.ACTIVE:
                full_pipeline_result:FeedbackCode | ErrorCode  \
                    = self.pipeline_processor.analyze_frame_full_pipeline(session_data, frame_data)
                if isinstance(full_pipeline_result, FeedbackCode):
                    return FeedbackResponse(full_pipeline_result)
                else:
                    return ErrorResponse(full_pipeline_result)

            elif state is AnalyzingState.DONE:
                error_code:ErrorCode = ErrorCode.TRYING_TO_ANALYZE_FRAME_WHEN_DONE
                ErrorHandler.handle(error=error_code, origin=inspect.currentframe())
                return ErrorResponse(error_code)
            
            elif state is AnalyzingState.FAILURE:
                error_code:ErrorCode = ErrorCode.TRYING_TO_ANALYZE_FRAME_WHEN_FAILED
                ErrorHandler.handle(error=error_code, origin=inspect.currentframe())
                return ErrorResponse(error_code)
    
    ##########################
    ### GET SESSION STATUS ###
    ##########################
    def get_session_status(self, session_id:str) -> ManagementResponse | ErrorResponse:
        """
        ### Brief:
        The `get_session_status` method returns the current status (as a `ManagementResponse`)
        of the provided session_id string. This is a routed `Flask` request.

        ### Arguments:
        `session_id` (str): The session id to be checked.

        ### Returns:
        - `ManagementResponse` with the relevant session status.
        - `ErrorResponse` if the `_search` method raised an error.

        ### Notes:
        Returns `CLIENT_SESSION_IS_NOT_IN_SYSTEM` if the session doesn't exist in any dictionary.
        """
        # Checking if the session id is valid and packing it.
        session_id:SessionId = self.id_generator.pack_string_to_session_id(session_id) 
        if session_id is None:
            return ErrorResponse(ErrorCode.INVALID_SESSION_ID)
        
        try:
            status = self._search(key=session_id, search_type=SearchType.ID)
            if status is SessionStatus.REGISTERED: return ManagementResponse(ManagementCode.CLIENT_SESSION_IS_REGISTERED)
            if status is SessionStatus.ACTIVE:     return ManagementResponse(ManagementCode.CLIENT_SESSION_IS_ACTIVE)
            if status is SessionStatus.PAUSED:     return ManagementResponse(ManagementCode.CLIENT_SESSION_IS_PAUSED)
            if status is SessionStatus.ENDED:      return ManagementResponse(ManagementCode.CLIENT_SESSION_IS_ENDED)
            else:                                  return ManagementResponse(ManagementCode.CLIENT_SESSION_IS_NOT_IN_SYSTEM)
        except Exception:
            return ErrorResponse(ErrorCode.SEARCH_TYPE_IS_NOT_SUPPORTED)

    ###############################################
    #################### TASKS ####################
    ###############################################

    ####################
    ### CLEANUP TASK ###
    ####################
    def _cleanup_task(self) -> None:
        """
        The `_cleanup_task` method periodically scans and removes stale sessions
        across all states:
        - Registered (never started)
        - Active (no frames recently)
        - Paused (never resumed)
        - Ended (expired retention window)
        """
        while True:
            Logger.info("Starting cleanup task.")
            now = datetime.now()
            remove_keys = []

            with self.sessions_lock:
                for session_id, session_data in self.sessions.items():
                    if session_data.session_status == SessionStatus.REGISTERED and \
                       (now - session_data.time["registered"]).total_seconds() > self.max_registration_minutes * 60:
                        remove_keys.append(session_id)
                    elif session_data.session_status == SessionStatus.ACTIVE and \
                         (now - session_data.time["last_activity"]).total_seconds() > self.max_inactive_minutes * 60:
                        remove_keys.append(session_id)
                    elif session_data.session_status == SessionStatus.PAUSED and \
                         session_data.time["paused"] is not None and \
                         (now - session_data.time["paused"]).total_seconds() > self.max_pause_minutes * 60:
                        remove_keys.append(session_id)
                    elif session_data.session_status == SessionStatus.ENDED and \
                        session_data.time["ended"] is not None and \
                        (now - session_data.time["ended"]).total_seconds() > self.max_ended_retention * 60:
                        remove_keys.append(session_id)
                    else:
                        continue
                
                # Removing identified stale sessions.
                for sid in remove_keys: self.sessions.pop(sid, None)
                Logger.info(f"Removed {len(remove_keys)} stale sessions.")
                    
            Logger.info("Finishing cleanup task.")

            # Sleep until next cycle.
            time.sleep(self.cleanup_interval_minutes * 60)

    ############################
    ### RETRIEVE CONFIG TASK ###
    ############################
    def _retrieve_config_task(self) -> None:
        """
        The `_retrieve_config_task` method periodically scans and updates
        server configurations from the `JSON` file.
        """
        while True:
            Logger.info("Starting retrieve configuration task.")
            self.retrieve_configurations()
            Logger.info("Starting retrieve configuration task.")

            # Sleep until next cycle.
            time.sleep(self.retrieve_configuration_minutes * 60)

    ##########################################################
    #################### HELPER FUNCTIONS ####################
    ##########################################################

    ###############################
    ### IS ACTIVE SESSIONS FULL ###
    ###############################
    def _is_active_sessions_full(self) -> bool:
        """
        ### Brief:
        The `_is_active_sessions_full` method returns whether the number of active sessions at the moment has reached its maximum.
        
        ### Returns:
        `True` if reached the maximum, `False` if not.
        
        ### Notes:
        The `self.maximum_clients` value is based on the configuration file.
        """
        return self.current_active_sessions >= self.maximum_clients

    ##############
    ### SEARCH ###
    ##############
    def _search(self, key:str | SessionId, search_type:SearchType, include_ended: bool = True) -> SessionStatus:
        """
        ### Brief:
        The `_search` method searches for a session by either IP address or Session ID.
        
        ### Arguments:
        - `key` (str | SessionId): The IP address or session ID to search for.
        - `search_type` (SearchType): Enum value indicating whether the key is an IP or ID.
        - `include_ended` (bool): Whether to include ended sessions in the search. Default is `True`.
        
        ### Returns:
        - `SessionStatus`: The status of the session if found, otherwise `SessionStatus.NOT_IN_SYSTEM`.
        
        ### Raises:
        - `ValueError`: If the type of `key` does not match the `search_type`.
        """
        session_id = None

        # Checking which kind of search is required - based on client ip address, or on session id number.
        if search_type is SearchType.IP:
            if not isinstance(key, str):
                raise ValueError("Expected string for IP address.")
            else:
                with self.ip_map_lock:
                    session_id = self.ip_map.get(key, None)
                    if session_id is None:
                        return SessionStatus.NOT_IN_SYSTEM
        elif search_type is SearchType.ID:
            if not isinstance(key, SessionId): raise ValueError("Expected SessionId for session ID.")
            else:                              session_id = key
        else:
            ErrorHandler.handle(
                error=ErrorCode.SEARCH_TYPE_IS_NOT_SUPPORTED,
                origin=inspect.currentframe(),
                extra_info={
                    'provided': SearchType(search_type).name,
                    'supported': f"{SearchType.IP.name} or {SearchType.ID.name}"
                }
            )
            return None
        
        session_data:SessionData = self.sessions.get(session_id, None)
        if session_data is None: return SessionStatus.NOT_IN_SYSTEM
        else:                    return session_data.get_session_status()
    
    ###############################
    ### SESSION STATUS TO ERROR ###
    ###############################
    def _session_status_to_error(self, status:SessionStatus) -> ErrorCode:
        """
        ### Brief:
        The `_session_status_to_log_error_code` method converts a `SessionStatus` object into an `ErrorCode`.
        
        ### Arguments:
        - `status` (SessionStatus): The session status to be converted.
        
        ### Returns:
        - The converted `ErrorCode`.
        """
        if   status is SessionStatus.REGISTERED: return ErrorCode.CLIENT_IS_ALREADY_REGISTERED
        elif status is SessionStatus.ACTIVE:     return ErrorCode.CLIENT_IS_ALREADY_ACTIVE
        elif status is SessionStatus.PAUSED:     return ErrorCode.CLIENT_IS_ALREADY_PAUSED
        elif status is SessionStatus.ENDED:      return ErrorCode.CLIENT_IS_ALREADY_ENDED
        else:                                    return ErrorCode.CLIENT_IS_NOT_REGISTERED

    #############################
    ### IS EXERCISE SUPPORTED ###
    #############################
    def _is_exercise_supported(self, exercise_type:str) -> ExerciseType | None:
        """
        ### Brief:
        The `_is_exercise_supported` method gets an exercise type and returns whether it's supported or not.
        If it is supported returns an `ExerciseType` object, or `None` if not supported.
        
        ### Arguments:
        `exercise_type` (str): The exercise type.
        
        ### Returns:
        `ExerciseType` object if supported, `None` if not.
        """
        if   exercise_type is None:                         return None
        elif exercise_type not in self.supported_exercises: return None
        else:
            try:    return ExerciseType.get(exercise_type)
            except: return None

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

        # Refresh the configuration data.
        ConfigLoader.refresh()

        # Supported exercises.
        self.supported_exercises:list = ConfigLoader.get([
            ConfigParameters.Major.SESSION,
            ConfigParameters.Minor.SUPPORTED_EXERCIES
        ])
        Logger.info(f"Supported exercises: {self.supported_exercises}")

        # Maximum clients at the same time.
        self.maximum_clients:int = ConfigLoader.get([
            ConfigParameters.Major.SESSION,
            ConfigParameters.Minor.MAXIMUM_CLIENTS
        ])
        Logger.info(f"Maximum clients: {self.maximum_clients}")

        # Cleanup background thread.
        self.cleanup_interval_minutes = ConfigLoader.get([
            ConfigParameters.Major.TASKS,
            ConfigParameters.Minor.CLEANUP_INTERVAL_MINUTES
        ])
        Logger.info(f"Cleanup interval minutes: {self.cleanup_interval_minutes}")
        self.max_registration_minutes = ConfigLoader.get([
            ConfigParameters.Major.TASKS,
            ConfigParameters.Minor.MAX_REGISTRATION_MINUTES
        ])
        Logger.info(f"Maximum registration minutes: {self.max_registration_minutes}")
        self.max_inactive_minutes = ConfigLoader.get([
            ConfigParameters.Major.TASKS,
            ConfigParameters.Minor.MAX_INACTIVE_MINUTS
        ])
        Logger.info(f"Maximum inactive minutes: {self.max_inactive_minutes}")
        self.max_pause_minutes = ConfigLoader.get([
            ConfigParameters.Major.TASKS,
            ConfigParameters.Minor.MAX_PAUSE_MINUTES
        ])
        Logger.info(f"Maximum pause minutes: {self.max_pause_minutes}")
        self.max_ended_retention = ConfigLoader.get([
            ConfigParameters.Major.TASKS,
            ConfigParameters.Minor.MAX_ENDED_RETENTION
        ])
        Logger.info(f"Maximum ended retention: {self.max_ended_retention}")

        # Retrieve configuration thread.
        self.retrieve_configuration_minutes = ConfigLoader.get([
            ConfigParameters.Major.TASKS,
            ConfigParameters.Minor.RETRIEVE_CONFIGURATION_MINUTES
        ])
        Logger.info(f"Retrieve configuration minutes: {self.retrieve_configuration_minutes}")

        # Run PipelineProcessor configuration retrieval.
        self.pipeline_processor.retrieve_configurations()

    ##############################################
    ### DEBUG / TELEMETRY EXPOSURE (SAFE) ########
    ##############################################
    def get_debug_state(self) -> dict:
        """
        Returns a safe representation of SessionManager internal state,
        used only for debugging and runtime monitoring.
        """
        with self.sessions_lock, self.ip_map_lock:
            registered_counter = 0
            active_counter     = 0
            paused_counter     = 0
            ended_counter      = 0

            session_summaries = {}
            for sid, session in self.sessions.items():
                session_summaries[sid.id] = {
                    "status": session.get_session_status().name,
                    "exercise_type": session.get_exercise_type().name,
                    "extended_evaluation": session.get_extended_evaluation(),
                    "analyzing_state": session.get_analyzing_state().name,
                    "last_activity": session.time.get("last_activity")
                }
                if session.get_session_status() is SessionStatus.REGISTERED:
                    registered_counter += 1
                elif session.get_session_status() is SessionStatus.ACTIVE:
                    active_counter += 1
                elif session.get_session_status() is SessionStatus.PAUSED:
                    paused_counter += 1
                elif session.get_session_status() is SessionStatus.ENDED:
                    ended_counter += 1

            return {
                # General information.
                "supported_exercises": list(self.supported_exercises),
                "maximum_clients": self.maximum_clients,
                "counters": {
                    "registered_sessions": registered_counter,
                    "active_sessions": active_counter,
                    "paused_sessions": paused_counter,
                    "ended_sessions": ended_counter
                },
                "total_sessions": len(self.sessions),

                # IP mapping.
                "ip_map": {
                    ip: sid.id for ip, sid in self.ip_map.items()
                },

                # Session details.
                "sessions": session_summaries,

                # Tasks configuration
                "cleanup_interval_minutes": self.cleanup_interval_minutes,
                "max_registration_minutes": self.max_registration_minutes,
                "max_inactive_minutes": self.max_inactive_minutes,
                "max_pause_minutes": self.max_pause_minutes,
                "max_ended_retention": self.max_ended_retention,

                # Memory.
                "memory_mb": psutil.Process(os.getpid()).memory_info().rss/1024/1024,

                # Timestamp.
                "timestamp": datetime.now().isoformat()
            }