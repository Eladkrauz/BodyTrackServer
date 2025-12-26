###############################################################
############## BODY TRACK // SERVER // MANAGEMENT #############
###############################################################
###################### CLASS: TestManager #####################
###############################################################

###############
### IMPORTS ###
###############
import threading, queue, requests, time, cv2, json, base64
import numpy as np
from Data.Session.ExerciseType import ExerciseType

######################
### ENDPOINT CLASS ###
######################
class Endpoint:
    REGISTER_NEW_SESSION = "http://localhost:8080/register/new/session"
    START_SESSION        = "http://localhost:8080/start/session"
    ANALYZE              = "http://localhost:8080/analyze"
    END_SESSION          = "http://localhost:8080/end/session"
    SESSION_SUMMARY      = "http://localhost:8080/session/summary"

##########################
### TEST MANAGER CLASS ###
##########################
class TestManager:
    """
    ### Description:
    The `TestManager` class is responsible for conducting test runs by
    registering sessions, sending video frames to the server for analysis,
    and displaying session summaries.
    """
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self) -> None:
        """
        ### Brief:
        The `init` method initializes the TestManager class.
        """
        pass

    ############
    ### TEST ###
    ############
    def test(self, exercise_type:ExerciseType, video_path:str) -> None:
        """
        ### Brief:
        The `test` method performs a test run by registering a new session,
        starting the session, reading frames from a video file, sampling them
        at a reduced rate, sending them to the server, and finally ending the session
        and displaying the session summary.

        ### Arguments:
        - `exercise_type` (ExerciseType): The type of exercise for the session.
        - `video_path` (str): The path to the video file to be processed.
        """
        # Session setup.
        registration_result = requests.post(
            Endpoint.REGISTER_NEW_SESSION,
            json={ 'exercise_type': exercise_type.value }
        ).json()
        session_id = registration_result['extra_info']['session_id']
        input("Continue to next step >>> ")

        # Start session.
        requests.post(
            Endpoint.START_SESSION,
            json={'session_id': session_id, 'extended_evaluation': False}
        )
        input("Continue to next step >>> ")

        # Video setup.
        cap = cv2.VideoCapture(video_path)
        original_fps = cap.get(cv2.CAP_PROP_FPS)
        print(f"Original FPS: {original_fps}")
        capture_interval = 1.0 / original_fps
        print(f"Capture Interval: {capture_interval:.4f} seconds")

        # Sampling configuration (25% reduction).
        REDUCTION_RATIO = 0
        target_fps = original_fps * (1.0 - REDUCTION_RATIO)
        sampling_interval = 1.0 / target_fps

        # Shared state
        frame_queue = queue.Queue(maxsize=8)
        stop_event = threading.Event()
        sent_frames = []
        dropped_frames = []
        last_sample_time = 0.0
        frame_id = 1

        # Sender thread.
        def sender():
            while not stop_event.is_set() or not frame_queue.empty():
                try:
                    fid, frame = frame_queue.get(timeout=0.1)
                    self.send_frame_to_server(session_id, fid, frame)
                except queue.Empty:
                    continue

        sender_thread = threading.Thread(target=sender, daemon=True)
        sender_thread.start()

        # Main loop: read frames, sample, and enqueue.
        while cap.isOpened():
            loop_start = time.perf_counter()

            ret, frame = cap.read()
            if not ret: break

            cv2.imshow("BodyTrack - Current Frame", frame)

            now = time.perf_counter()

            # Frame sampling logic.
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

            if cv2.waitKey(1) & 0xFF == ord('q'): break

            # Maintain real-time playback.
            elapsed = time.perf_counter() - loop_start
            sleep_time = capture_interval - elapsed
            if sleep_time > 0: time.sleep(sleep_time)

        # Shutdown.
        stop_event.set()
        sender_thread.join()
        cap.release()
        cv2.destroyAllWindows()

        requests.post(Endpoint.END_SESSION, json={ 'session_id': session_id })
        summary = requests.post(Endpoint.SESSION_SUMMARY, json={ 'session_id': session_id }).json()
        self.show(summary)

        # Final report.
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

    ########################
    ### TEST WITH ENTERS ###
    ########################
    def test_with_enters(self, exercise_type:ExerciseType, video_path:str) -> None:
        # Register a new session.
        registration_result = requests.post(
            Endpoint.REGISTER_NEW_SESSION,
            json={'exercise_type': exercise_type.value}
        ).json()
        session_id = registration_result['extra_info']['session_id']
        input("Continue to next step >>> ")

        # Start the session.
        requests.post(Endpoint.START_SESSION, json={'session_id': session_id, 'extended_evaluation': False}).json()
        input("Continue to next step >>> ")

        # Open the video file.
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

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
            frame_count += 1

        cap.release()
        cv2.destroyAllWindows()

        # End the session.
        requests.post(Endpoint.END_SESSION, json={'session_id': session_id}).json()
        self.show(requests.post(Endpoint.SESSION_SUMMARY, json={'session_id': session_id}).json())

    ############
    ### SHOW ###
    ############
    def show(self, result) -> None:
        """
        ### Brief:
        The `show` method pretty-prints a JSON result.

        ### Arguments:
        - `result` (dict): The JSON result to be printed.
        """
        print(json.dumps(result, indent=4))

    ############################
    ### SEND FRAME TO SERVER ###
    ############################
    def send_frame_to_server(self, session_id:str, frame_id:int, frame_content:np.ndarray) -> None:
        """
        ### Brief:
        The `send_frame_to_server` method encodes a video frame to WebP format,
        converts it to a base64 string, and sends it to the server for analysis.

        ### Arguments:
        - `session_id` (str): The ID of the session.
        - `frame_id` (int): The ID of the frame.
        - `frame_content` (np.ndarray): The video frame content.
        """
        _, buffer = cv2.imencode('.webp', frame_content)
        image_bytes = buffer.tobytes()
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        payload = {
            "session_id": session_id,
            "frame_id": frame_id,
            "frame_content": image_b64
        }
        self.show(requests.post(Endpoint.ANALYZE, json=payload).json())
        # requests.post(Endpoint.ANALYZE, json=payload)

