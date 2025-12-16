###############################################################
############## BODY TRACK // SERVER // MANAGEMENT #############
###############################################################
##################### CLASS: ServerManager ####################
###############################################################

###############
### IMPORTS ###
###############
import threading, queue
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

        self.test_with_enters()
        # self.test()
        # Thread(target=self.test, daemon=True).start()
        # while True: time.sleep(5)

    def test_with_enters(self):
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
            input("Continue to next frame >>> ")
            # time.sleep(1)
            frame_count += 1

        cap.release()
        cv2.destroyAllWindows()

        # End the session.
        requests.post("http://localhost:8080/end/session", json={'session_id': session_id}).json()
        self.show(requests.post("http://localhost:8080/session/summary", json={'session_id': session_id}).json())


    
    ############
    ### TEST ###
    ############
    def test(self):
        # ---------------------------------------------------------
        # Session setup
        # ---------------------------------------------------------
        registration_result = requests.post(
            "http://localhost:8080/register/new/session",
            json={'exercise_type': 'biceps_curl'}
        ).json()

        session_id = registration_result['extra_info']['session_id']

        input("Continue to next step >>> ")

        requests.post(
            "http://localhost:8080/start/session",
            json={'session_id': session_id, 'extended_evaluation': False}
        )

        input("Continue to next step >>> ")

        # ---------------------------------------------------------
        # Video setup
        # ---------------------------------------------------------
        cap = cv2.VideoCapture("/Users/eladkrauz/Desktop/try6.mp4")

        original_fps = cap.get(cv2.CAP_PROP_FPS)
        capture_interval = 1.0 / original_fps

        # ---------------------------------------------------------
        # Sampling configuration (25% reduction)
        # ---------------------------------------------------------
        REDUCTION_RATIO = 0.8
        target_fps = original_fps * (1.0 - REDUCTION_RATIO)
        sampling_interval = 1.0 / target_fps

        # ---------------------------------------------------------
        # Shared state
        # ---------------------------------------------------------
        frame_queue = queue.Queue(maxsize=8)
        stop_event = threading.Event()

        sent_frames = []
        dropped_frames = []

        last_sample_time = 0.0
        frame_id = 1

        # ---------------------------------------------------------
        # Sender thread (I/O only, no pacing)
        # ---------------------------------------------------------
        def sender():
            while not stop_event.is_set() or not frame_queue.empty():
                try:
                    fid, frame = frame_queue.get(timeout=0.1)
                    self.send_frame_to_server(session_id, fid, frame)
                except queue.Empty:
                    continue

        sender_thread = threading.Thread(target=sender, daemon=True)
        sender_thread.start()

        # ---------------------------------------------------------
        # Capture + sampling loop (REAL-TIME CLOCK)
        # ---------------------------------------------------------
        while cap.isOpened():
            loop_start = time.perf_counter()

            ret, frame = cap.read()
            if not ret:
                break

            cv2.imshow("BodyTrack - Current Frame", frame)

            now = time.perf_counter()

            # --- SAMPLING DECISION (independent of queue) ---
            if now - last_sample_time >= sampling_interval:
                last_sample_time = now

                if not frame_queue.full():
                    frame_queue.put((frame_id, frame))
                    sent_frames.append(frame_id)
                else:
                    dropped_frames.append(frame_id)
            else:
                dropped_frames.append(frame_id)

            frame_id += 1

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # --- Maintain real-time playback ---
            elapsed = time.perf_counter() - loop_start
            sleep_time = capture_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        # ---------------------------------------------------------
        # Shutdown
        # ---------------------------------------------------------
        stop_event.set()
        sender_thread.join()

        cap.release()
        cv2.destroyAllWindows()

        requests.post(
            "http://localhost:8080/end/session",
            json={'session_id': session_id}
        )

        summary = requests.post(
            "http://localhost:8080/session/summary",
            json={'session_id': session_id}
        ).json()

        self.show(summary)

        # ---------------------------------------------------------
        # Final report
        # ---------------------------------------------------------
        total_frames = frame_id - 1

        print("\n========== FRAME REPORT ==========")
        print(f"Total frames read: {total_frames}")
        print(f"Frames sent ({len(sent_frames)}):")
        print(sent_frames)

        print(f"\nFrames dropped ({len(dropped_frames)}):")
        print(dropped_frames)

        effective_reduction = 100.0 * (1.0 - len(sent_frames) / total_frames)
        print(f"\nEffective reduction: {effective_reduction:.2f}%")
        print("==================================\n")


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

