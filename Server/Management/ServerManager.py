###############################################################
############## BODY TRACK // SERVER // MANAGEMENT #############
###############################################################
##################### CLASS: ServerManager ####################
###############################################################

###############
### IMPORTS ###
###############
from threading import Thread
import requests, time

from Server.Communication.FlaskServer import FlaskServer
from Server.Utilities.Logger import Logger
from Server.Utilities.Config.ConfigLoader import ConfigLoader
from Server.Utilities.Config.ConfigParameters import ConfigParameters

### MAIN EXECUTION ###
class ServerManager:
    def __init__(self) -> None:
        # Initialize the ConfigLoader.
        ConfigLoader.initialize()
        # Initialize the Logger.
        Logger.initialize()
        Logger.info("###############################")
        Logger.info("##### INITIALIZING SERVER #####")
        Logger.info("###############################")
        # Initialize the Flask Server.
        self.flask_server = FlaskServer(
            host=ConfigLoader.get(key=[ConfigParameters.Major.COMMUNICATION, ConfigParameters.Minor.HOST]),
            port=ConfigLoader.get(key=[ConfigParameters.Major.COMMUNICATION, ConfigParameters.Minor.PORT])
        )
        Thread(target=self.flask_server.run, daemon=True).start()
        time.sleep(2)
        Logger.info("##############################################")
        Logger.info("##### SERVER IS INITIALIZED SUCCESSFULLY #####")
        Logger.info("##############################################")

        def show(result):
            import json
            time.sleep(5)
            res = json.dumps(result, indent=4)
            print(res)
            time.sleep(2)

        show(requests.post("http://localhost:8080/start/session", json={'session_id': 'a1f58b88-bc32-455a-b9db-dc578afe1217', 'extended_evaluation': False}).json())
        return
        show(requests.get("http://localhost:8080/ping").json())
        result = requests.post("http://localhost:8080/register/new/session", json={'exercise_type': 'squat'}).json()
        show(result)
        session_id = result['extra_info']['session_id']
        print("SESSION ID:", session_id)
        show(requests.post("http://localhost:8080/register/new/session", json={'exercise_type': 'squat'}).json())
        show(requests.post("http://localhost:8080/session/status", json={'session_id': session_id}).json())
        show(requests.post("http://localhost:8080/start/session", json={'session_id': session_id, 'extended_evaluation': False}).json())
        show(requests.post("http://localhost:8080/session/status", json={'session_id': session_id}).json())
