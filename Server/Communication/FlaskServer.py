############################################################
########## BODY TRACK // SERVER // COMMUNICATION ###########
############################################################
#################### CLASS: FlaskServer ####################
############################################################

###############
### IMPORTS ###
###############
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from threading import Thread
from typing import Dict
import inspect, ipaddress
import base64, cv2
import numpy as np
from threading import Thread
import os

from Communication.HttpCodes           import HttpCodes
from Management.SessionManager         import SessionManager
from Utilities.Logger                  import Logger
from Utilities.Error.ErrorHandler      import ErrorHandler
from Utilities.Error.ErrorCode         import ErrorCode, ErrorResponse
from Communication.Communication       import Communication
from Data.Response.ManagementResponse  import ManagementResponse, ManagementCode
from Data.Response.FeedbackResponse    import FeedbackResponse
from Data.Response.CalibrationResponse import CalibrationResponse
from Data.Response.SummaryResponse     import SummaryResponse

##########################
### FLASK SERVER CLASS ###
##########################
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
        CORS(self.app)          # Enable CORS for all routes.

        # Bind routes to handler functions.
        try:
            self.app.add_url_rule("/ping",                   view_func=self.ping,                    methods=["GET"])
            self.app.add_url_rule("/register/new/session",   view_func=self._register_new_session,   methods=["POST"])
            self.app.add_url_rule("/unregister/session",     view_func=self._unregister_session,     methods=["POST"])
            self.app.add_url_rule("/start/session",          view_func=self._start_session,          methods=["POST"])
            self.app.add_url_rule("/start_analysis",         view_func=self._start_session,          methods=["POST"])  # Alias for backward compatibility.
            self.app.add_url_rule("/pause/session",          view_func=self._pause_session,          methods=["POST"])
            self.app.add_url_rule("/resume/session",         view_func=self._resume_session,         methods=["POST"])
            self.app.add_url_rule("/end/session",            view_func=self._end_session,            methods=["POST"])
            self.app.add_url_rule("/analyze",                view_func=self._analyze_pose,           methods=["POST"])
            self.app.add_url_rule("/session/status",         view_func=self._session_status,         methods=["POST"])
            self.app.add_url_rule("/session/summary",        view_func=self._session_summary,        methods=["POST"])
            self.app.add_url_rule("/internal/telemetry",     view_func=self._telemetry,              methods=["GET"])
            self.app.add_url_rule("/terminate/server",       view_func=self._terminate_server,       methods=["POST"])
            self.app.add_url_rule("/refresh/configurations", view_func=self._refresh_configurations, methods=["GET"])
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.CANT_ADD_URL_RULE_TO_FLASK_SERVER,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception": f"{type(e)}",
                    "Reason": f"{str(e)}"
                }
            )

        Logger.info("Initialized successfully.")

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
        self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)

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
            Logger.info(f"Starting server on {self.host}:{self.port}")
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
    def _prepare_client_info(self) -> Dict[str, str] | ErrorCode:
        """
        ### Brief:
        The `_prepare_client_info` method validates and assembles client metadata including IP address and User-Agent string.

        ### Returns:
        - `dict[str, str]`: Dictionary with keys `'ip'` and `'user_agent'` if both are valid.
        - `ErrorCode`: Specific error enum if either IP or User-Agent is invalid.

        ### Notes:
        - Validates that `client_ip` is a proper IPv4/IPv6 address using the built-in `ipaddress` module.
        - Ensures that a `User-Agent` header was provided by the client.
        """
        # Checking the IP address.
        try:
            if request.headers.getlist("X-Forwarded-For"):
                # 'X-Forwarded-For' can be a list: [client, proxy1, proxy2].
                # The "real" client IP is the first one.
                client_ip = request.headers.getlist("X-Forwarded-For")[0]
            else:
                client_ip = request.remote_addr
            if client_ip is None: raise ValueError
            ipaddress.ip_address(client_ip)
        except ValueError:
            return ErrorCode.CLIENT_IP_IS_INVALID
        
        # Checking the User Agent.
        client_user_agent = request.headers.get("User-Agent", None)
        if client_user_agent is None:
            return ErrorCode.CLIENT_AGENT_IS_INVALID
        
        # If no errors occured.
        return {
            'ip': client_ip,
            'user_agent': client_user_agent
        }

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
        return jsonify(Communication.ping_response()), HttpCodes.OK

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
        data:dict = dict(request.get_json())
        if data is None:
            Logger.warning("Missing or invalid JSON in request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Extract required values.
        exercise_type:str = data.get("exercise_type", None)
        if exercise_type is None or (isinstance(exercise_type, bool) and exercise_type is False):
            Logger.warning("Missing 'exercise_type' in request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.MISSING_EXERCISE_TYPE_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Check received client information.
        client_info_result:Dict[str, str] | ErrorCode = self._prepare_client_info()
        if isinstance(client_info_result, ErrorCode): # It is an ErrorCode instance.
            return jsonify(Communication.error_response(client_info_result)), HttpCodes.BAD_REQUEST
        
        # If arrived here, the `client_info_result` of `_prepare_client_info` is a dictionary
        # containing information about the client.
        
        # Register client to SessionManager.
        registration_result:ManagementResponse | ErrorResponse = self.session_manager.register_new_session(exercise_type, client_info_result)
        # Checking the result.
        if isinstance(registration_result, ErrorResponse): # An error with registration.
            return jsonify(Communication.error_response(registration_result)), HttpCodes.SERVER_ERROR
        else: # The result is a valid SessionId.
            return jsonify(Communication.construct_response(registration_result)), HttpCodes.OK

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
        data:dict = dict(request.get_json())
        if data is None:
            Logger.warning("Missing or invalid JSON in request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST
        
        # Extract required values.
        session_id:str = data.get("session_id", None)
        if session_id is None:
            Logger.warning("Missing 'session_id' in request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.MISSING_SESSION_ID_IN_REQUEST)), HttpCodes.BAD_REQUEST
        
        # Trying to unregister the session.
        unregister_session_result:ManagementResponse | ErrorResponse = self.session_manager.unregister_session(session_id)
        if isinstance(unregister_session_result, ErrorCode): # If an error occured.
            return jsonify(Communication.error_response(unregister_session_result)), HttpCodes.BAD_REQUEST
        else: # If the session unregistered successfully.
            return jsonify(Communication.construct_response(unregister_session_result)), HttpCodes.OK        
    
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
        data:dict = dict(request.get_json())
        if data is None:
            Logger.warning("Missing or invalid JSON in request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Extract required values.
        session_id:str = data.get("session_id", None)
        if session_id is None:
            Logger.warning("Missing 'session_id' in request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.MISSING_SESSION_ID_IN_REQUEST)), HttpCodes.BAD_REQUEST
        extended_evaluation:bool = data.get("extended_evaluation", None)
        if extended_evaluation is None:
            Logger.warning("Missing 'extended_evaluation' in request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.INVALID_EXTENDED_EVALUATION_PARAM)), HttpCodes.BAD_REQUEST
        
        # Trying to start the session.
        start_session_result:ManagementResponse | ErrorResponse = self.session_manager.start_session(session_id, extended_evaluation)
        if isinstance(start_session_result, ErrorResponse):
            return jsonify(Communication.error_response(start_session_result)), HttpCodes.BAD_REQUEST
        else: # If the session started successfully.
            return jsonify(Communication.construct_response(start_session_result)), HttpCodes.OK
    
    ######################
    ### START ANALYSIS ###
    ######################
    def _start_analysis(self) -> tuple[Response, HttpCodes]:
        """
        ### Brief:
        The `_start_analysis` method starts the analysis of a previously started session.

        ### Returns:
        - `tuple`: A JSON response indicating the result and an appropriate HTTP code.
        """
        # Get request's JSON data.
        data:dict = dict(request.get_json())
        if data is None:
            Logger.warning("Missing or invalid JSON in request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Extract required values.
        session_id:str = data.get("session_id", None)
        if session_id is None:
            Logger.warning("Missing 'session_id' in request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.MISSING_SESSION_ID_IN_REQUEST)), HttpCodes.BAD_REQUEST
        
        # Trying to start the analysis of the session.
        start_analysis_result:ManagementResponse | ErrorResponse = self.session_manager.start_analysis(session_id)
        if isinstance(start_analysis_result, ErrorResponse): # If an error occured.
            return jsonify(Communication.error_response(start_analysis_result)), HttpCodes.BAD_REQUEST
        else: # If the session analysis started successfully.
            return jsonify(Communication.construct_response(start_analysis_result)), HttpCodes.OK    

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
        data:dict = dict(request.get_json())
        if data is None:
            Logger.warning("Missing or invalid JSON in request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Extract required values.
        session_id:str = data.get("session_id", None)
        if session_id is None:
            Logger.warning("Missing 'session_id' in request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.MISSING_SESSION_ID_IN_REQUEST)), HttpCodes.BAD_REQUEST
        
        # Trying to pause the session.
        pause_session_result:ManagementResponse | ErrorResponse = self.session_manager.pause_session(session_id)
        if isinstance(pause_session_result, ErrorResponse): # If an error occured.
            return jsonify(Communication.error_response(pause_session_result)), HttpCodes.BAD_REQUEST
        else: # If the session paused successfully.
            return jsonify(Communication.construct_response(pause_session_result)), HttpCodes.OK    

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
        data:dict = dict(request.get_json())
        if data is None:
            Logger.warning("Missing or invalid JSON in request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Extract required values.
        session_id:str = data.get("session_id", None)
        if session_id is None:
            Logger.warning("Missing 'session_id' in request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.MISSING_SESSION_ID_IN_REQUEST)), HttpCodes.BAD_REQUEST
        
        # Trying to resume the session.
        resume_session_result:ManagementResponse | ErrorResponse = self.session_manager.resume_session(session_id)
        if isinstance(resume_session_result, ErrorResponse): # If an error occured.
            return jsonify(Communication.error_response(resume_session_result)), HttpCodes.SERVER_ERROR
        else: # If the session resumed successfully.
            return jsonify(Communication.construct_response(resume_session_result)), HttpCodes.OK
        
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
        data:dict = dict(request.get_json())
        if data is None:
            Logger.warning("Missing or invalid JSON in request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Extract required values.
        session_id:str = data.get("session_id", None)
        if session_id is None:
            Logger.warning("Missing 'session_id' in request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.MISSING_SESSION_ID_IN_REQUEST)), HttpCodes.BAD_REQUEST
        
        # Trying to end the session.
        end_session_result:ManagementResponse | ErrorResponse = self.session_manager.end_session(session_id)
        if isinstance(end_session_result, ErrorResponse): # If an error occured.
            return jsonify(Communication.error_response(end_session_result)), HttpCodes.BAD_REQUEST
        else: # If the session ended successfully.
            return jsonify(Communication.construct_response(end_session_result)), HttpCodes.OK    

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
        data:dict = dict(request.get_json())
        if not data:
            Logger.warning("Missing or invalid JSON in analyze_pose request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Extract required fields.
        session_id:str  = data.get("session_id", None)
        frame_id:str    = data.get("frame_id", None)
        content_b64:str = data.get("frame_content", None)

        if session_id is None or frame_id is None or content_b64 is None:
            Logger.warning("Missing fields in analyze_pose request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.MISSING_FRAME_DATA_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Decode base64 to np.ndarray.
        try:
            frame_bytes:bytes = base64.b64decode(content_b64)
            np_arr:np.ndarray = np.frombuffer(frame_bytes, np.uint8)
            frame_content:np.ndarray = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)  # BGR frame
        except Exception as e:
            Logger.error(f"Frame decoding failed: {e}")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.FRAME_DECODING_FAILED)), HttpCodes.BAD_REQUEST

        # Call SessionManager to analyze.
        analysis_result:CalibrationResponse | FeedbackResponse | ErrorResponse = \
            self.session_manager.analyze_frame(
                session_id=session_id, frame_id=frame_id, frame_content=frame_content
            )

        # Handle errors.
        if isinstance(analysis_result, ErrorResponse):
            return jsonify(Communication.error_response(analysis_result)), HttpCodes.BAD_REQUEST
        
        # Returning CalibrationResponse or FeedbackResponse.
        else:
            return jsonify(Communication.construct_response(analysis_result)), HttpCodes.OK

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
        data:dict = dict(request.get_json())
        if not data:
            Logger.warning("Missing or invalid JSON in analyze_pose request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Extract required fields.
        session_id:str = data.get("session_id", None)
        if session_id is None:
            Logger.warning("Missing fields in analyze_pose request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.MISSING_FRAME_DATA_IN_REQUEST)), HttpCodes.BAD_REQUEST
        
        # Get the status.
        session_status_icd:ManagementResponse | ErrorResponse = self.session_manager.get_session_status(session_id)
        if isinstance(session_status_icd, ErrorResponse):
            return jsonify(Communication.error_response(session_status_icd)), HttpCodes.SERVER_ERROR
        else:
            return jsonify(Communication.construct_response(session_status_icd)), HttpCodes.OK
    
    #######################
    ### SESSION SUMMARY ###
    #######################
    def _session_summary(self) -> tuple[Response, HttpCodes]:
        """
        ### Brief:
        The `_session_summary` method receives a session id from the client, forwards it
        to the SessionManager and returns the session summary, or an error code.

        ### Returns:
        - JSON containing session summary if exists.
        - JSON with error info if does not exist.

        ### Use:
        Used by the client to retrieve the final summary of a session after it has ended.
        """
        # Get request's JSON data.
        data:dict = dict(request.get_json())
        if not data:
            Logger.warning("Missing or invalid JSON in analyze_pose request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Extract required fields.
        session_id:str = data.get("session_id", None)
        if session_id is None:
            Logger.warning("Missing fields in analyze_pose request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.MISSING_FRAME_DATA_IN_REQUEST)), HttpCodes.BAD_REQUEST
        
        # Get the summary.
        session_summary_icd:SummaryResponse | ErrorResponse = self.session_manager.get_session_summary(session_id)
        if isinstance(session_summary_icd, ErrorResponse):
            return jsonify(Communication.error_response(session_summary_icd)), HttpCodes.SERVER_ERROR
        else:
            return jsonify(Communication.construct_response(session_summary_icd)), HttpCodes.OK
    
    ##############################
    ### REFRESH CONFIGURATIONS ###
    ##############################
    def _refresh_configurations(self) -> tuple[Response, HttpCodes]:
        """
        ### Brief:
        The `_refresh_configurations` method refreshes the server configurations.

        ### Returns:
        - JSON response indicating success or failure, along with the appropriate HTTP code.

        ### Use:
        Used to reload server configurations without restarting the server.
        """
        self.session_manager.retrieve_configurations()
        return jsonify(Communication.construct_response(
            ManagementResponse(management_code=ManagementCode.CONFIGURATION_UPDATED_SUCCESSFULLY)
        )), HttpCodes.OK
    
    #################
    ### TELEMETRY ###
    #################
    def _telemetry(self):
        """
        ### Brief:
        The `telemetry` method provides internal server state information for debugging purposes.
        It returns it as a JSON response, and this information can be used to monitor server
        health and performance.
        """
        return jsonify(self.session_manager.get_debug_state()), HttpCodes.OK

    ########################
    ### TERMINATE SERVER ###
    ########################
    def _terminate_server(self) -> None:
        """
        ### Brief:
        The `_terminate_server` method stops the Flask server and exits the system.

        ### Use:
        Used for debugging purposes to gracefully shut down the server.
        """
        data:dict = dict(request.get_json())
        if not data:
            Logger.warning("Missing or invalid JSON in analyze_pose request")
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST

        # Extract required fields.
        password:str = data.get("password", None)
        if password is None:
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.INVALID_JSON_PAYLOAD_IN_REQUEST)), HttpCodes.BAD_REQUEST
        if password != "123456":
            return jsonify(Communication.error_response(error=None, error_code=ErrorCode.TERMINATION_INCORRECT_PASSWORD)), HttpCodes.UNAUTHORIZED
        
        Logger.info("###################################")
        Logger.info("##### SERVER IS SHUTTING DOWN #####")
        Logger.info("###################################")

        from Data.Response.ManagementResponse import ManagementCode
        response = jsonify(Communication.construct_response(
                ManagementResponse(management_code=ManagementCode.SERVER_IS_BEING_SHUTDOWN)
            )), HttpCodes.OK

        # Use a background thread to exit the system after the response is sent.
        def exit_system(): import time; time.sleep(1); os._exit(0)
        Thread(target=exit_system).start(); return response