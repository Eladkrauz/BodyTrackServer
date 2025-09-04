############################################################
################### BODY TRACK // SERVER ###################
############################################################
#################### CLASS: FlaskServer ####################
############################################################

###############
### IMPORTS ###
###############
from flask import Flask, request, jsonify
from threading import Thread
from Components.SessionManager import SessionManager
from Utilities.Logger import Logger
from Utilities.ErrorHandler import ErrorHandler, ErrorCode
from Common.ClientServerIcd import ClientServerIcd as ICD
import inspect, ipaddress
from enum import Enum as enum

class HttpCodes(enum):
    """
    ### Description:
    ** The `HttpCodes` enum class representes `HTTP` return codes.
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
    **The `FlaskServer` class serves as the HTTP interface for the `BodyTrack` server.**
    
    It uses `Flask` to handle incoming requests from the Android client, including:
    - `ping` for connection checks
    - `start_session` to initiate a tracking session per user
    - `analyze_pose` to send frame data for posture analysis
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
            self.app.add_url_rule("/ping", view_func=self.ping, methods=["GET"])
            self.app.add_url_rule("/session/start", view_func=self.start_session, methods=["POST"])
            self.app.add_url_rule("/session/end", view_func=self.end_session, methods=["POST"])
            self.app.add_url_rule("/analyze", view_func=self.analyze_pose, methods=["POST"])
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
                opcode=ErrorCode.CANT_ADD_URL_RULE_TO_FLASK_SERVER,
                origin=inspect.currentframe(),
                message="The method 'start' was called more than once on the same thread object.",
                extra_info={
                    "Exception": f"{type(e)}",
                    "Reason": f"{str(e)}"
                },
                critical=True
            )

    ###########################
    ### PREPARE CLIENT INFO ###
    ###########################
    def prepare_client_info(self, client_ip:str, client_user_agent:str) -> dict[str, str] | ICD.ErrorType:
        """
        ### Brief:
        The `prepare_client_info` method validates and assembles client metadata including IP address and User-Agent string.

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
        
    #######################################
    ########## ENDPOINT HANDLERS ##########
    #######################################

    ############
    ### PING ###
    ############
    def ping(self) -> tuple:
        """
        ### Brief:
        The `ping` method represents a simple `GET` request to check if the server is reachable.
        ### Returns:
        - `tuple` containing the JSON response confirming server status, and a HTTP success code.
        """
        client_ip = request.remote_addr or "unknown"
        client_user_agent = request.headers.get("User-Agent", "unknown")
        Logger.info("Received ping request")
        return jsonify({"status": "alive"}), HttpCodes.OK

    ############################
    ### REGISTER NEW SESSION ###
    ############################
    def register_new_session(self) -> tuple:
        """
        ### Brief:
        The `register_new_session` method register a new session for a client.
        ### Returns:
        - `tuple` containing the JSON response confirming session registered, and a HTTP success code.
        """
        # Get request's JSON data.
        data = dict(request.get_json())
        if data is None:
            Logger.warning("Missing or invalid JSON in request")
            return jsonify({ "error": ICD.ErrorType.INVALID_JSON_PAYLOAD_IN_REQUEST }), HttpCodes.BAD_REQUEST

        # Extract required values.
        exercise_type = data.get("exercise_type")
        if not exercise_type:
            Logger.warning("Missing 'exercise_type' in request")
            return jsonify({ "error": ICD.ErrorType.MISSING_EXERCISE_TYPE_IN_REQUEST }), HttpCodes.BAD_REQUEST

        # Check received client information.
        client_info = self.prepare_client_info(
            client_ip=request.remote_addr,
            client_user_agent=request.headers.get("User-Agent", None)
        )
        if not isinstance(client_info, dict):
            return jsonify({ "error": client_info.description }), client_info.value
        
        # Register client to SessionManager.
        session_id = self.ses
        return jsonify({"session": "started"}), HttpCodes.OK

    ###################
    ### END SESSION ###
    ###################
    def end_session(self):
        """
        ### Brief:
        The `end_session` method ends the current session.
        ### Returns:
        - `tuple` containing the JSON response confirming session end, and a HTTP success code.
        """
        Logger.info("Session end request received")
        # Future: Cleanup logic, save session log, etc.
        return jsonify({"session": "ended"}), HttpCodes.OK

    ####################
    ### ANALYZE POSE ###
    ####################
    def analyze_pose(self):
        """
        ### Brief:
        The `analyze_pose` method accepts a `POST` request containing an image frame and analyzes the user's pose.
        ### Returns:
        - `tuple` containing the JSON response with key pose data, feedback or error info, and a HTTP success code.
        """
        Logger.info("Received pose analysis request")

        # Ensure the request contains a file
        if 'frame' not in request.files:
            Logger.warning("Missing 'frame' in request files")
            return jsonify({"error": "Missing frame"}), HttpCodes.BAD_REQUEST

        frame = request.files['frame']

        # Save or process frame (placeholder for pose estimation logic)
        Logger.debug("Frame received, processing...")

        # Here you would call your PoseEstimator, ErrorDetector, etc.
        # For now, simulate with dummy data
        feedback = {
            "feedback": "Good posture!",
            "confidence": 0.91,
            "angles": {"knee": 88, "hip": 160}
        }

        return jsonify(feedback), HttpCodes.OK