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

        while True: time.sleep(5)

        # return
        def show(result):
            import json
            time.sleep(2)
            res = json.dumps(result, indent=4)
            print(res)
            # time.sleep(2)

        result = requests.post("http://localhost:8080/register/new/session", json={'exercise_type': 'squat'}).json()
        show(result)
        session_id = result['extra_info']['session_id']

        show(requests.post("http://localhost:8080/start/session", json={'session_id': session_id, 'extended_evaluation': False}).json())

        import base64
        with open("/Users/eladkrauz/Desktop/try2.webp", "rb") as image:
            image_bytes = image.read()

        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        payload = {
            "session_id": session_id,
            "frame_id": 1,
            "frame_content": image_b64
        }
        show(requests.post("http://localhost:8080/analyze", json=payload).json())