############################################################
################ BODY TRACK // COMPONENTS ##################
############################################################
################### CLASS: PoseAnalyzer ####################
############################################################

###############
### IMPORTS ###
###############
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.python.solutions import pose as mp_pose
import inspect
from Utilities.ErrorHandler import ErrorHandler, ErrorCode
from Utilities.Logger import Logger
from typing import Optional


class PoseAnalyzer:
    """
    ### Description:
    The `PoseAnalyzer` class is responsible for analyzing raw image frames 
    and extracting body landmarks (2D keypoints) using MediaPipe Pose.
    ### Notes:
    - Uses the MediaPipe library for pose estimation.
    - Provides a simple and safe interface for pose analysis.
    - Integrates OpenCV (cv2) for image preprocessing and MediaPipe for detection.
    - In case of unexpected errors, logs the issue and falls back gracefully.
    """

    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self) -> 'PoseAnalyzer':
        """
        ### Brief:
        The `__init__` method initializes the `PoseAnalyzer` class.
        """
        try:
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(static_image_mode=False, 
            model_complexity=1, 
            smooth_landmarks=True, 
            enable_segmentation=False, 
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_drawing_styles = mp.solutions.drawing_styles
            Logger.info("PoseAnalyzer initialized successfully.")
        except ValueError as e:
            ErrorHandler.handle(
                opcode=ErrorCode.CANT_ADD_URL_RULE_TO_FLASK_SERVER,
                origin=inspect.currentframe(),
                message="Invalid parameter passed to Mediapipe Pose.",
                extra_info={"Reason": str(e)},
                critical=True
            )
        except RuntimeError as e:
            ErrorHandler.handle(
                opcode=ErrorCode.ERROR_INITIALIZING_POSE,
                origin=inspect.currentframe(),
                message="Failed to initialize PoseAnalyzer.",
                extra_info={"Reason": str(e)},
                critical=True
            )
        except OSError as e:
            ErrorHandler.handle(
                opcode=ErrorCode.ERROR_INITIALIZING_POSE,
                origin=inspect.currentframe(),
                message="OSError while accessing Mediapipe model files.",
                extra_info={"Reason": str(e)},
                critical=True
            )
        except MemoryError as e:
            ErrorHandler.handle(
                opcode=ErrorCode.ERROR_INITIALIZING_POSE,
                origin=inspect.currentframe(),
                message="MemoryError while initializing Mediapipe Pose.",
                extra_info={"Reason": str(e)},
                critical=True
            )
        except Exception as e:
            ErrorHandler.handle(
                opcode=ErrorCode.ERROR_INITIALIZING_POSE,
                origin=inspect.currentframe(),
                message="Unexpected error while initializing Mediapipe Pose.",
                extra_info={"Exception": str(type(e)), "Reason": str(e)},
                critical=True
            )


    ########################
    ### VALIDATE FRAME   ###
    ########################
    @staticmethod
    def validate_frame(frame: np.ndarray) -> bool:
        """
        ### Brief:
        Validates that the input frame is a proper image suitable 
        for further processing in the PoseAnalyzer pipeline.

        ### Arguments:
        - `frame` (np.ndarray): Input image frame to validate.

        ### Returns:
        - `bool`: 
          - True if the frame is valid.
          - False if the frame is invalid (with errors logged).
        """
        # 1. Check if frame is None
        if frame is None:
            ErrorHandler.handle(
                opcode=ErrorCode.FRAME_PROCESSING_ERROR,
                origin=inspect.currentframe(),
                message="Frame validation failed: frame is None.",
                extra_info={"Reason": "No frame data provided."},
                critical=False
            )
            Logger.error("Frame validation failed: frame is None.")
            return False

        # 2. Check if frame is a numpy array
        if not isinstance(frame, np.ndarray):
            ErrorHandler.handle(
                opcode=ErrorCode.FRAME_PROCESSING_ERROR,
                origin=inspect.currentframe(),
                message="Frame validation failed: not a NumPy array.",
                extra_info={"Type": str(type(frame))},
                critical=False
            )
            Logger.error(f"Frame validation failed: not a NumPy array ({type(frame)}).")
            return False

        # 3. Check shape: must be 3D (H, W, C) with 3 channels (BGR)
        if frame.ndim != 3 or frame.shape[2] != 3:
            ErrorHandler.handle(
                opcode=ErrorCode.FRAME_PROCESSING_ERROR,
                origin=inspect.currentframe(),
                message="Frame validation failed: invalid dimensions.",
                extra_info={"Shape": str(frame.shape)},
                critical=False
            )
            Logger.error(f"Frame validation failed: invalid shape {frame.shape}.")
            return False

        # If all checks passed
        Logger.info("Frame validation passed successfully.")
        return True


    ########################
    ####PreProcess Frame####
    ########################
    def preprocess_frame(frame: np.ndarray, target_size: tuple[int, int] = (640, 480)) -> np.ndarray | None:
        """
        ### Brief:
        Preprocesses an input frame before sending it to the MediaPipe Pose model.

        ### Steps:
        1. Validate the input frame.
        2. Resize to the target resolution.
        3. Convert color space from BGR (OpenCV default) to RGB.
        4. Cast to uint8 for compatibility with MediaPipe.

        ### Arguments:
        - `frame` (np.ndarray): Raw frame captured from client video.
        - `target_size` (tuple[int,int]): Desired width and height for resizing.

        ### Returns:
        - `np.ndarray` (RGB, uint8): The processed frame ready for model input.
        - Returns `None` if preprocessing fails.
        """
        #צריך להוסיף בדיקה שנשלח פריים תקין בכלל לפני 
        try:
            resized = cv2.resize(frame, target_size)
        except cv2.error as e:
            ErrorHandler.handle(
                opcode=ErrorCode.FRAME_PROCESSING_ERROR,
                origin=inspect.currentframe(),
                message="OpenCV error during frame resizing.",
                extra_info={"Reason": str(e)},
                critical=False
            )
            Logger.error("Frame preprocessing failed at resize step.")
            return None

            # 3. Convert color space BGR → RGB
        try:
            converted = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        except cv2.error as e:
            ErrorHandler.handle(
                opcode=ErrorCode.FRAME_PROCESSING_ERROR,
                origin=inspect.currentframe(),
                message="OpenCV error during color conversion (BGR→RGB).",
                extra_info={"Reason": str(e)},
                critical=False
            )
            Logger.error("Frame preprocessing failed at color conversion step.")
            return None

        # 4. Cast to uint8
        try:
            processed = converted.astype(np.uint8)
        except (ValueError, TypeError) as e:
            ErrorHandler.handle(
                opcode=ErrorCode.FRAME_PROCESSING_ERROR,
                origin=inspect.currentframe(),
                message="Failed to cast frame to uint8.",
                extra_info={"Reason": str(e)},
                critical=False
            )
            Logger.error("Frame preprocessing failed at uint8 cast step.")
            return None
        Logger.info("Frame preprocessing completed successfully.")
        return processedFrame

        


    #####################
    ### analyze_frame ###
    #####################       
    def analyze_frame(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        ### Brief:
        Processes a single video frame by converting it to RGB and running MediaPipe Pose
        detection on it. Extracts the body landmarks (if detected) and returns the results.

        ### Arguments:
        - `frame` (numpy.ndarray): Input image frame in **BGR format** (as captured with OpenCV).
        Expected shape: (height, width, 3).

        ### Returns:
        - `Optional[np.ndarray]`:
        A NumPy array of shape `(33, 4)` if landmarks are detected, where each row corresponds
        to one human body landmark with the following columns:
        - `[i, 0]`: x-coordinate (float, normalized to [0,1], relative to image width).
        - `[i, 1]`: y-coordinate (float, normalized to [0,1], relative to image height).
        - `[i, 2]`: z-coordinate (float, relative depth, negative = closer to camera).
        - `[i, 3]`: visibility score (float in [0,1], probability that the landmark is visible).

        If detection fails, returns `None`.
        """
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        except cv2.error as e:
            ErrorHandler.handle(
                opcode=ErrorCode.FRAME_CONVERSION_FAILED,
                origin=inspect.currentframe(),
                message="cv2.error while converting frame to RGB.",
                extra_info={"Reason": str(e)},
                critical=False
            )
            return None
        except Exception as e:
            ErrorHandler.handle(
                opcode=ErrorCode.FRAME_CONVERSION_FAILED,
                origin=inspect.currentframe(),
                message="Unexpected error while converting frame to RGB.",
                extra_info={"Exception": str(type(e)), "Reason": str(e)},
                critical=False
            )
            return None