############################################################
################### BODY TRACK // SERVER ###################
############################################################
#################### CLASS: FlaskServer ####################
############################################################

###############
### IMPORTS ###
###############
from flask import Flask, request, jsonify, Response
from threading import Thread
from Components.SessionManager import SessionManager
from Utilities.Logger import Logger
from Utilities.ErrorHandler import ErrorHandler, ErrorCode
from Common.ClientServerIcd import ClientServerIcd as ICD
import inspect, ipaddress
import base64, cv2
import numpy as np

class HttpCodes():
    """
    ### Description:
    The `HttpCodes` class representes `HTTP` return codes.
    """
    OK           = 200
    CREATED      = 201
    BAD_REQUEST  = 400
    UNAUTHORIZED = 401
    NOT_FOUND    = 404
    SERVER_ERROR = 500

class FlaskServer:
    """
    ### Description:
    The `FlaskServer` class serves as the HTTP interface for the `BodyTrack` server.
    
    It uses `Flask` to handle incoming requests from the Android client.

    ### Notes:
    This class connects the networking layer with the internal components (like `SessionManager`
    and `PoseAnalyzer`), and manages the routing and responses. It is the entry point for all
    external communication with the server and ensures each request is properly handled and logged.
    """

    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self, host:str="0.0.0.0", port:int=8080) -> 'FlaskServer':
        """
        ### Brief:
        The `__init__` method initializes the `Flask` server with specified host and port. 
        
        ### Arguments:
        - `host`: The IP address to bind the server to (default: all interfaces).
        - `port`: The port on which to listen for incoming requests (default: 8080).
        
        ### Notes:
        - The default `host` IP address is 0.0.0.0 (all interfaces).
        - The default `port` is 8080.
        """
        self.host = host
        self.port = port
        self.app = Flask(__name__)  # Create a Flask app instance.

        # Bind routes to handler functions.
        try:
            self.app.add_url_rule("/ping",                 view_func=self.ping,                  methods=["GET"])
            self.app.add_url_rule("/register/new/session", view_func=self._register_new_session, methods=["POST"])
            self.app.add_url_rule("/unregister/session",   view_func=self._unregister_session,   methods=["POST"])
            self.app.add_url_rule("/start/session",        view_func=self._start_session,        methods=["POST"])
            self.app.add_url_rule("/pause/session",        view_func=self._pause_session,        methods=["POST"])
            self.app.add_url_rule("/resume/session",       view_func=self._resume_session,       methods=["POST"])
            self.app.add_url_rule("/end/session",          view_func=self._end_session,          methods=["POST"])
            self.app.add_url_rule("/analyze",              view_func=self._analyze_pose,         methods=["POST"])
            self.app.add_url_rule("/session/status",       view_func=self._session_status,       methods=["GET"])
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.CANT_ADD_URL_RULE_TO_FLASK_SERVER,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception": f"{type(e)}",
                    "Reason": f"{str(e)}"
                }
            )

        # Session Manager.
        self.session_manager = SessionManager()

    ###########
    ### RUN ###
    ###########
    def run(self) -> None:
        """
        ### Brief:
        The `run` method starts the `Flask` server in a blocking manner.
        """
        Logger.info(f"Starting server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port)

    #################
    ### RUN ASYNC ###
    #################
    def run_async(self) -> None:
        """
        ### Brief:
        The `run_async` method starts the `Flask` server in a separate thread so it doesn't block the main program.
        
        ### Notes:
        Useful if the server needs to run in parallel with other tasks.
        """        
        server_thread = Thread(target=self.run)
        server_thread.daemon = True  # Thread will exit when main program exits.
        try:
            server_thread.start()
        except RuntimeError as e:
            ErrorHandler.handle(
                error=ErrorCode.CANT_ADD_URL_RULE_TO_FLASK_SERVER,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception": f"{type(e)}",
                    "Reason": f"{str(e)}"
                }
            )

    ###########################
    ### PREPARE CLIENT INFO ###
    ###########################
    def _prepare_client_info(self, client_ip:str, client_user_agent:str) -> dict[str, str] | ICD.ErrorType:
        """
        ### Brief:
        The `_prepare_client_info` method validates and assembles client metadata including IP address and User-Agent string.

        ### Arguments:
        - `client_ip` (str): The IP address extracted from the `request` object.
        - `client_user_agent` (str): The User-Agent string from the `request` headers.

        ### Returns:
        - `dict[str, str]`: Dictionary with keys `'ip'` and `'user_agent'` if both are valid.
        - `ICD.ErrorType`: Specific error enum if either IP or User-Agent is invalid.

        ### Notes:
        - Validates that `client_ip` is a proper IPv4/IPv6 address using the built-in `ipaddress` module.
        - Ensures that a `User-Agent` header was provided by the client.
        """
        # Checking the IP address.
        try:
            if client_ip is None: raise ValueError
            ipaddress.ip_address(client_ip)
        except ValueError:
            return ICD.ErrorType.CLIENT_IP_IS_INVALID
        
        # Checking the User Agent.
        if client_user_agent is None:
            return ICD.ErrorType.CLIENT_AGENT_IS_INVALID
        
        # If no errors occured.
        return {
            'ip': client_ip,
            'user_agent': client_user_agent
        }
    
    #####################
    ### ERROR TO DICT ###
    #####################
    def _error_to_dict(self, error:ICD.ErrorType) -> dict:
        """
        ### Brief:
        The `_error_to_dict` method gets an `ICD.ErrorType` enum class object, and returns
        a dictionary containing relavant information about the error, to be returned to the client side.
        
        ### Arguments:
        - `error` (ICD.ErrorType): The error type to be added to the returned dictionary.
        
        ### Returns:
        - A dictionary containing relavant information about the provided error.
        
        ### Notes:
        - `error` must be a valid `ICD.ErrorType` object.
        """
        # In case the provided error type is unrecognized.
        if not isinstance(error, ICD.ErrorType):
            ErrorHandler.handle(error=ErrorCode.UNRECOGNIZED_ICD_ERROR_TYPE, origin=inspect.currentframe())
        else:
            return {
                'message_type': ICD.MessageType.ERROR.value,
                'opcode': error.value,
                'title': error.name,
                'description': error.description
            }
        
    ########################
    ### RESPONSE TO DICT ###
    ########################
    def _response_to_dict(self, response:ICD.ResponseType, information:dict = None) -> dict:
        """
        ### Brief:
        The `_response_to_dict` method gets an `ICD.ResponseType` enum class object, and returns
        a dictionary containing relavant information about the response, to be returned to the client side.
        
        ### Arguments:
        - `response` (ICD.ResponseType): The response type to be added to the returned dictionary.
        - `information` (dict): An extra information dictionary to be added to the respone. Defaults to None.
        
        ### Returns:
        - A dictionary containing relavant information about the provided response.
        
        ### Notes:
        - `response` must be a valid `ICD.ResponseType` object.
        - `information` can be ignored and not sent.
        """
        # In case the provided response type is unrecognized.
        if not isinstance(response, ICD.ResponseType):
            ErrorHandler.handle(error=ErrorCode.UNRECOGNIZED_ICD_RESPONSE_TYPE, origin=inspect.currentframe())
        else:
            dict_to_return = {
                'message_type': ICD.MessageType.RESPONSE.value,
                'opcode': response.value,
                'title': response.name,
                'description': response.description
            }
            if information is not None:
                dict_to_return.update(information)
            return dict_to_return  
              
    #######################################
    ########## ENDPOINT HANDLERS ##########
    #######################################

    ############
    ### PING ###
    ############
    def ping(self) -> tuple[Response, HttpCodes]:
        """
        ### Brief:
        The `ping` method represents a simple `GET` request to check if the server is reachable.
        
        ### Returns:
        - `tuple` containing the JSON response confirming server status, and a HTTP code.

        ### Use:
        Used by the client at startup or during connectivity checks to verify that the server is reachable.
        """
        Logger.info("Received ping request")
        return jsonify(self._response_to_dict(ICD.ResponseType.ALIVE)), HttpCodes.OK

    ############################
    ### REGISTER NEW SESSION ###
    ############################
    def _register_new_session(self) -> tuple[Response, HttpCodes]:
        """
        ### Brief:
        The `_register_new_session` method registers a new session in the system for a specific exercise type.

        ### Returns:
        - `tuple`: A JSON response indicating success or failure, along with the appropriate HTTP code.

        ### Notes:
        - The request must include a valid `exercise_type` in the JSON payload.
        - The method validates the client's IP and User-Agent before registration.
        - If the client is already registered, or if the exercise type is unsupported, appropriate errors are returned.
        - On success, a unique session ID is returned to the client.

        ### Use:
        Called when the user enters the exercise instructions screen to register a new session.
        """
        # Get request's JSON data.
        data = dict(request.get_json())
        if data is None:
            Logger.warning("Missing or invalid JSON in request")
            return jsonify(self._error_to_dict(ICD.ErrorType.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Extract required values.
        exercise_type = data.get("exercise_type", None)
        if exercise_type is None or (isinstance(exercise_type, bool) and exercise_type is False):
            Logger.warning("Missing 'exercise_type' in request")
            return jsonify(self._error_to_dict(ICD.ErrorType.MISSING_EXERCISE_TYPE_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Check received client information.
        client_info_result = self._prepare_client_info(
            client_ip=request.remote_addr,
            client_user_agent=request.headers.get("User-Agent", None)
        )
        if not isinstance(client_info_result, dict): # It is an ICD.ErrorType instance.
            return jsonify(self._error_to_dict(client_info_result)), HttpCodes.BAD_REQUEST
        
        # If arrived here, the `client_info_result` of `_prepare_client_info` is a dictionary
        # containing information about the client.

        # Register client to SessionManager.
        registration_result = self.session_manager.register_new_session(exercise_type, client_info_result)
        # Checking the result.
        if isinstance(registration_result, ICD.ErrorType): # An error with registration.
            if registration_result is ICD.ErrorType.EXERCISE_TYPE_NOT_SUPPORTED:
                return jsonify(self._error_to_dict(registration_result)), HttpCodes.BAD_REQUEST
            else:
                return jsonify(self._error_to_dict(registration_result)), HttpCodes.SERVER_ERROR
        else: # The result is a valid SessionId.
                return jsonify(self._response_to_dict(
                    response=ICD.ResponseType.CLIENT_REGISTERED_SUCCESSFULLY,
                    information={'session_id': registration_result.id})
                ), HttpCodes.OK

    ##########################
    ### UNREGISTER SESSION ###
    ##########################   
    def _unregister_session(self) -> tuple[Response, HttpCodes]:
        """
        ### Brief:
        The `_unregister_session` method removes a registered session before it starts.

        ### Returns:
        - `tuple`: A JSON response with a message and corresponding HTTP code.

        ### Notes:
        - The request must include a valid `session_id`.
        - This only applies to sessions in the `REGISTERED` state.
        - Returns an error if the session is already active, paused, ended, or doesn't exist.

        ### Use:
        Triggered when the user cancels or returns to the home screen before starting the session.
        """
        # Get request's JSON data.
        data = dict(request.get_json())
        if data is None:
            Logger.warning("Missing or invalid JSON in request")
            return jsonify(self._error_to_dict(ICD.ErrorType.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST
        
        # Extract required values.
        session_id = data.get("session_id", None)
        if session_id is None:
            Logger.warning("Missing 'session_id' in request")
            return jsonify(self._error_to_dict(ICD.ErrorType.MISSING_SESSION_ID_IN_REQUEST)), HttpCodes.BAD_REQUEST
        
        # Trying to unregister the session.
        unregister_session_result = self.session_manager.unregister_session(session_id)
        if isinstance(unregister_session_result, ICD.ErrorType): # If an error occured.
            return jsonify(self._error_to_dict(unregister_session_result)), HttpCodes.BAD_REQUEST
        else: # If the session unregistered successfully.
            return jsonify(self._response_to_dict(unregister_session_result)), HttpCodes.OK        
    
    #####################
    ### START SESSION ###
    #####################
    def _start_session(self) -> tuple[Response, HttpCodes]:
        """
        ### Brief:
        The `_start_session` method starts a previously registered session and moves it to the active state.

        ### Returns:
        - `tuple`: A JSON response indicating the result and an appropriate HTTP code.

        ### Notes:
        - The request must include a valid `session_id` in the JSON payload.
        - Only sessions in the `REGISTERED` state can be started.
        - Returns an error if the session is invalid, already started, or the server has reached the maximum number of concurrent sessions.

        ### Use:
        Called when the user starts exercising, activating the registered session.
        """
        # Get request's JSON data.
        data = dict(request.get_json())
        if data is None:
            Logger.warning("Missing or invalid JSON in request")
            return jsonify(self._error_to_dict(ICD.ErrorType.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Extract required values.
        session_id = data.get("session_id", None)
        if session_id is None:
            Logger.warning("Missing 'session_id' in request")
            return jsonify(self._error_to_dict(ICD.ErrorType.MISSING_SESSION_ID_IN_REQUEST)), HttpCodes.BAD_REQUEST
        
        # Trying to start the session.
        start_session_result = self.session_manager.start_session(session_id)
        if isinstance(start_session_result, ICD.ErrorType): # If an error occured.
            if isinstance(start_session_result, ICD.ErrorType.MAX_CLIENT_REACHED):
                return jsonify(self._error_to_dict(start_session_result)), HttpCodes.SERVER_ERROR
            else:
                return jsonify(self._error_to_dict(start_session_result)), HttpCodes.BAD_REQUEST
        else: # If the session started successfully.
            return jsonify(self._response_to_dict(start_session_result)), HttpCodes.OK
            
    #####################
    ### PAUSE SESSION ###
    #####################
    def _pause_session(self) -> tuple[Response, HttpCodes]:
        """
        ### Brief:
        The `_pause_session` method pauses a currently active session.

        ### Returns:
        - `tuple`: A JSON response with a message and corresponding HTTP code.

        ### Notes:
        - The request must include a valid `session_id`.
        - The session must be in the `ACTIVE` state.
        - Returns an error if the session is not found or is not currently active.

        ### Use:
        Sent when the user pauses a workout (temporarily suspends analysis).
        """
        # Get request's JSON data.
        data = dict(request.get_json())
        if data is None:
            Logger.warning("Missing or invalid JSON in request")
            return jsonify(self._error_to_dict(ICD.ErrorType.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Extract required values.
        session_id = data.get("session_id", None)
        if session_id is None:
            Logger.warning("Missing 'session_id' in request")
            return jsonify(self._error_to_dict(ICD.ErrorType.MISSING_SESSION_ID_IN_REQUEST)), HttpCodes.BAD_REQUEST
        
        # Trying to pause the session.
        pause_session_result = self.session_manager.pause_session(session_id)
        if isinstance(pause_session_result, ICD.ErrorType): # If an error occured.
            return jsonify(self._error_to_dict(pause_session_result)), HttpCodes.BAD_REQUEST
        else: # If the session unregistered successfully.
            return jsonify(self._response_to_dict(pause_session_result)), HttpCodes.OK    

    ######################
    ### RESUME SESSION ###
    ######################
    def _resume_session(self) -> tuple[Response, HttpCodes]:
        """
        ### Brief:
        The `_resume_session` method resumes a session that is currently paused.

        ### Returns:
        - `tuple`: A JSON response with a message and corresponding HTTP code.

        ### Notes:
        - The request must include a valid `session_id`.
        - The session must be in the `PAUSED` state.
        - Returns an error if the session is not found or if maximum client limit has been reached.

        ### Use:
        Triggered when the user resumes the workout after pausing.
        """
        # Get request's JSON data.
        data = dict(request.get_json())
        if data is None:
            Logger.warning("Missing or invalid JSON in request")
            return jsonify(self._error_to_dict(ICD.ErrorType.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Extract required values.
        session_id = data.get("session_id", None)
        if session_id is None:
            Logger.warning("Missing 'session_id' in request")
            return jsonify(self._error_to_dict(ICD.ErrorType.MISSING_SESSION_ID_IN_REQUEST)), HttpCodes.BAD_REQUEST
        
        # Trying to resume the session.
        resume_session_result = self.session_manager.resume_session(session_id)
        if isinstance(resume_session_result, ICD.ErrorType): # If an error occured.
            if isinstance(resume_session_result, ICD.ErrorType.MAX_CLIENT_REACHED):
                return jsonify(self._error_to_dict(resume_session_result)), HttpCodes.SERVER_ERROR
            else:
                return jsonify(self._error_to_dict(resume_session_result)), HttpCodes.BAD_REQUEST
        else: # If the session resumed successfully.
            return jsonify(self._response_to_dict(resume_session_result)), HttpCodes.OK
        
    ###################
    ### END SESSION ###
    ###################
    def _end_session(self) -> tuple[Response, HttpCodes]:
        """
        ### Brief:
        The `_end_session` method ends a session that is either active or paused.

        ### Returns:
        - `tuple`: A JSON response with a message and corresponding HTTP code.

        ### Notes:
        - The request must include a valid `session_id`.
        - This moves the session to the `ENDED` state.
        - Returns an error if the session is not found or already ended.

        ### Use:
        Called when the user finishes exercising or the session timer expires.
        """
        # Get request's JSON data.
        data = dict(request.get_json())
        if data is None:
            Logger.warning("Missing or invalid JSON in request")
            return jsonify(self._error_to_dict(ICD.ErrorType.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Extract required values.
        session_id = data.get("session_id", None)
        if session_id is None:
            Logger.warning("Missing 'session_id' in request")
            return jsonify(self._error_to_dict(ICD.ErrorType.MISSING_SESSION_ID_IN_REQUEST)), HttpCodes.BAD_REQUEST
        
        # Trying to end the session.
        end_session_result = self.session_manager.end_session(session_id)
        if isinstance(end_session_result, ICD.ErrorType): # If an error occured.
            return jsonify(self._error_to_dict(end_session_result)), HttpCodes.BAD_REQUEST
        else: # If the session ended successfully.
            return jsonify(self._response_to_dict(end_session_result)), HttpCodes.OK    

    ####################
    ### ANALYZE POSE ###
    ####################
    def _analyze_pose(self) -> tuple[Response, HttpCodes]:
        """
        ### Brief:
        The `_analyze_pose` method receives a video frame from the client, forwards it
        to the SessionManager for analysis, and returns the calculated feedback, or an error code.

        ### Expected Request JSON:
        ```
        {
            "session_id": "abc123",
            "frame_id": 17,
            "frame_content": "<base64 JPEG/PNG image>"
        }
        ```

        ### Returns:
        - JSON containing analysed frame feedback on success.
        - JSON with error info on error.

        ### Use:
        Used repeatedly during an active session to send each camera frame for pose analysis.
        """
        # Get request's JSON data.
        data = dict(request.get_json())
        if not data:
            Logger.warning("Missing or invalid JSON in analyze_pose request")
            return jsonify(self._error_to_dict(ICD.ErrorType.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Extract required fields.
        session_id:str  = data.get("session_id", None)
        frame_id:str    = data.get("frame_id", None)
        content_b64:str = data.get("frame_content", None)

        if session_id is None or frame_id is None or content_b64 is None:
            Logger.warning("Missing fields in analyze_pose request")
            return jsonify(self._error_to_dict(ICD.ErrorType.MISSING_FRAME_DATA_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Decode base64 to np.ndarray.
        try:
            frame_bytes:bytes = base64.b64decode(content_b64)
            np_arr:np.ndarray = np.frombuffer(frame_bytes, np.uint8)
            frame_content:np.ndarray = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)  # BGR frame
        except Exception as e:
            Logger.error(f"Frame decoding failed: {e}")
            return jsonify(self._error_to_dict(ICD.ErrorType.FRAME_DECODING_FAILED)), HttpCodes.BAD_REQUEST

        # Call SessionManager to analyze.
        analysis_result = self.session_manager.analyze_frame(session_id, frame_id, frame_content)

        # Handle errors.
        if isinstance(analysis_result, ICD.ErrorType):
            return jsonify(self._error_to_dict(analysis_result)), HttpCodes.BAD_REQUEST

        # Return success.
        return jsonify(self._response_to_dict(
            response=ICD.ResponseType.FRAME_ANALYZED_SUCCESSFULLY,
            information=analysis_result
        )), HttpCodes.OK
        '''
        The returned value from analyze_frame (in case of success) will be a dict:
        {
            'session_id': ...,
            'frame_id': ...,
            'feedback': { ... }        
        }
        '''

    ######################
    ### SESSION STATUS ###
    ######################
    def _session_status(self) -> tuple[Response, HttpCodes]:
        """
        ### Brief:
        The `_session_status` method receives a session id from the client, forwards it
        to the SessionManager and returns the session status, or an error code.

        ### Returns:
        - JSON containing session stauts if exists.
        - JSON with error info if does not exist.

        ### Use:
        Used by the client to periodically check whether their session is still
        active, paused, ended, or cleaned up by the server.
        """
        # Get request's JSON data.
        data = dict(request.get_json())
        if not data:
            Logger.warning("Missing or invalid JSON in analyze_pose request")
            return jsonify(self._error_to_dict(ICD.ErrorType.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Extract required fields.
        session_id:str = data.get("session_id", None)
        if session_id is None:
            Logger.warning("Missing fields in analyze_pose request")
            return jsonify(self._error_to_dict(ICD.ErrorType.MISSING_FRAME_DATA_IN_REQUEST)), HttpCodes.BAD_REQUEST
        
        # Get the status.
        session_status_icd = self.session_manager.get_session_status(session_id)
        if isinstance(session_status_icd, ICD.ErrorType):
            return jsonify(self._error_to_dict(session_status_icd)), HttpCodes.SERVER_ERROR
        else:
            return jsonify(self._response_to_dict(session_status_icd)), HttpCodes.OK