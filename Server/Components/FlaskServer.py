############################################################
################### BODY TRACK // SERVER ###################
############################################################
#################### CLASS: FlaskServer ####################
############################################################
# The FlaskServer class serves as the HTTP interface for the BodyTrack server.
# It uses Flask to handle incoming requests from the Android client, including:
#   - ping for connection checks
#   - start_session to initiate a tracking session per user
#   - analyze_pose to send frame data for posture analysis
#
# This class connects the networking layer with the internal components (like
# SessionManager and PoseAnalyzer), and manages the routing and responses.
# It is the entry point for all external communication with the server and ensures
# each request is properly handled and logged.

###############
### IMPORTS ###
###############
from flask import Flask, request, jsonify
from threading import Thread
from Components.SessionManager import SessionManager
from Components.PoseAnalyzer import PoseAnalyzer
from Utilities.Logger import Logger

class FlaskServer:
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        """
        Initializes the Flask server with specified host and port.

        :param host: The IP address to bind the server to (default: all interfaces).
        :param port: The port on which to listen for incoming requests (default: 8080).
        """
        self.host = host
        self.port = port
        self.app = Flask(__name__)  # Create a Flask app instance.

        # Bind routes to handler functions.
        self.app.add_url_rule("/ping", view_func=self.ping, methods=["GET"])
        self.app.add_url_rule("/session/start", view_func=self.start_session, methods=["POST"])
        self.app.add_url_rule("/session/end", view_func=self.end_session, methods=["POST"])
        self.app.add_url_rule("/analyze", view_func=self.analyze_pose, methods=["POST"])

    ###########
    ### RUN ###
    ###########
    def run(self):
        """
        Starts the Flask server in a blocking manner.
        """
        Logger.info(f"Starting server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port)

    #################
    ### RUN ASYNC ###
    #################
    def run_async(self):
        """
        Starts the Flask server in a separate thread so it doesn't block the main program.

        Useful if the server needs to run in parallel with other tasks.
        """
        server_thread = Thread(target=self.run)
        server_thread.daemon = True  # Thread will exit when main program exits
        server_thread.start()

    #######################################
    ########## ENDPOINT HANDLERS ##########
    #######################################

    ############
    ### PING ###
    ############
    def ping(self):
        """
        A simple GET request to check if the server is reachable.

        :return: A JSON response confirming server status
        """
        Logger.info("Received ping request")
        return jsonify({"status": "alive"}), 200

    #####################
    ### START SESSION ###
    #####################
    def start_session(self):
        """
        Starts a new session for a client. This could eventually register a client or initialize
        per-session tracking data.

        :return: A JSON response confirming session start
        """
        Logger.info("Session start request received")
        # Future: Assign session ID or client metadata if needed
        return jsonify({"session": "started"}), 200

    ###################
    ### END SESSION ###
    ###################
    def end_session(self):
        """
        Ends the current session. Could be used to clean up resources or stop logging.

        :return: A JSON response confirming session end
        """
        Logger.info("Session end request received")
        # Future: Cleanup logic, save session log, etc.
        return jsonify({"session": "ended"}), 200

    def analyze_pose(self):
        """
        Accepts a POST request containing an image frame and analyzes the user's pose.

        :return: A JSON response with key pose data, feedback, or error info
        """
        Logger.info("Received pose analysis request")

        # Ensure the request contains a file
        if 'frame' not in request.files:
            Logger.warning("Missing 'frame' in request files")
            return jsonify({"error": "Missing frame"}), 400

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

        return jsonify(feedback), 200