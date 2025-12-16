###############################################################
############## BODY TRACK // SERVER // MANAGEMENT #############
###############################################################
##################### CLASS: ServerManager ####################
###############################################################

###############
### IMPORTS ###
###############
from threading import Thread
import requests, time, cv2, json

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

        self.test()
        # Thread(target=self.test, daemon=True).start()
        # while True: time.sleep(5)
    
    ############
    ### TEST ###
    ############
    def test(self):
        # Register a new session.
        registration_result = requests.post("http://localhost:8080/register/new/session", json={'exercise_type': 'squat'}).json()
        session_id = registration_result['extra_info']['session_id']
        
        input("Continue to next step >>> ")

        # Start the session.
        requests.post("http://localhost:8080/start/session", json={'session_id': session_id, 'extended_evaluation': False}).json()

        input("Continue to next step >>> ")

        # Open the video file.
        cap = cv2.VideoCapture("/Users/eladkrauz/Desktop/try4.mp4")
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print("Total frames:", total_frames)

        # Send frames to the server.
        frame_count = 1
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Show current frame
            cv2.imshow("BodyTrack - Current Frame", frame)

            self.send_frame_to_server(session_id, frame_count, frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            # input("Continue to next frame >>> ")
            # time.sleep(1)
            frame_count += 1

        cap.release()
        cv2.destroyAllWindows()

        # End the session.
        requests.post("http://localhost:8080/end/session", json={'session_id': session_id}).json()
        self.show(requests.post("http://localhost:8080/session/summary", json={'session_id': session_id}).json())



    ############
    ### SHOW ###
    ############
    def show(self, result):
        print(json.dumps(result, indent=4))

    ############################
    ### SEND FRAME TO SERVER ###
    ############################
    def send_frame_to_server(self, session_id:str, frame_id:int, frame_content):
            import base64
            _, buffer = cv2.imencode('.webp', frame_content)
            image_bytes = buffer.tobytes()
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            payload = {
                "session_id": session_id,
                "frame_id": frame_id,
                "frame_content": image_b64
            }
            self.show(requests.post("http://localhost:8080/analyze", json=payload).json())

