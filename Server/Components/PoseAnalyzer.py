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
import inspect
from Utilities.ErrorHandler import ErrorHandler, ErrorCode
from Utilities.Logger import Logger
from Utilities.ConfigLoader import ConfigLoader, ConfigParameters
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
            # Load frame dimensions from config
            self.frame_width = ConfigLoader.get(
                [ConfigParameters.Major.FRAME, ConfigParameters.Minor.WIDTH],
                critical_value=True
            )
            self.frame_height = ConfigLoader.get(
                [ConfigParameters.Major.FRAME, ConfigParameters.Minor.HEIGHT],
                critical_value=True
            )
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
            static_image_mode=False, 
            model_complexity=1, 
            smooth_landmarks=True, 
            enable_segmentation=False, 
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
            )
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_drawing_styles = mp.solutions.drawing_styles
            Logger.info("PoseAnalyzer initialized successfully.")
        except ValueError as e:
            ErrorHandler.handle(
                error=ErrorCode.ERROR_INITIALIZING_POSE,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": type(e).__name__,
                    "Reason": "Invalid parameter passed to Mediapipe Pose."
                }
            )
        except RuntimeError as e:
            ErrorHandler.handle(
                error=ErrorCode.ERROR_INITIALIZING_POSE,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": type(e).__name__,
                    "Reason": "Failed to initialize PoseAnalyzer."
                }
            )
        except OSError as e:
            ErrorHandler.handle(
                error=ErrorCode.ERROR_INITIALIZING_POSE,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": type(e).__name__,
                    "Reason": "OSError while accessing Mediapipe model files."
                }
            )
        except MemoryError as e:
            ErrorHandler.handle(
                error=ErrorCode.ERROR_INITIALIZING_POSE,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": type(e).__name__,
                    "Reason": "MemoryError while initializing Mediapipe Pose."
                }
            )
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.ERROR_INITIALIZING_POSE,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": type(e).__name__,
                    "Reason": "Unexpected error while initializing Mediapipe Pose."
                }
            )


    ########################
    ### VALIDATE FRAME   ###
    ########################
    @staticmethod
    def validate_frame(frame: np.ndarray) -> Optional[ErrorCode]:
        """
        ### Brief:
        Validates that the input frame is a proper image suitable 
        for further processing in the PoseAnalyzer pipeline.

        ### Arguments:
        - `frame` (np.ndarray): Input image frame to validate.

        ### Returns:
        - `None`: if the frame is valid.
        - `ErrorCode`: the specific error encountered.
        """
        # 1. Check if frame is None
        if frame is None:
            ErrorHandler.handle(
                error=ErrorCode.FRAME_VALIDATION_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Reason": "No frame data provided."
                }
            )
            return ErrorCode.FRAME_VALIDATION_ERROR

        # 2. Check if frame is a numpy array
        if not isinstance(frame, np.ndarray):
            ErrorHandler.handle(
                error=ErrorCode.FRAME_VALIDATION_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Reason": "Frame validation failed: not a NumPy array."
                }
            )
            return ErrorCode.FRAME_VALIDATION_ERROR


        # 3. Check shape: must be 3D (H, W, C) with 3 channels (BGR)
        if frame.ndim != 3 or frame.shape[2] != 3:
            ErrorHandler.handle(
                error=ErrorCode.FRAME_VALIDATION_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Reason": "Frame validation failed: invalid dimensions."
                }
            )
            return ErrorCode.FRAME_VALIDATION_ERROR


        # If all checks passed
        Logger.info("Frame validation passed successfully.")
        return None


    ########################
    ####PreProcess Frame####
    ########################
    @classmethod
    def preprocess_frame(cls, frame: np.ndarray) -> np.ndarray | ErrorCode:
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

        ### Returns:
        - `np.ndarray` (RGB, uint8): The processed frame ready for model input.
        -  Returns ErrorCode if preprocessing fails.
        """
        validation_error = cls.validate_frame(frame)
        if validation_error is not None:
            return validation_error
        try:
            resized = cv2.resize(frame, (cls.frame_width, cls.frame_height))
        except cv2.error as e:
            ErrorHandler.handle(
                error=ErrorCode.FRAME_PREPROCESSING_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": type(e).__name__,
                    "Reason": "OpenCV error during frame resizing."
                }
            )
            return ErrorCode.FRAME_PREPROCESSING_ERROR

            # 3. Convert color space BGR → RGB
        try:
            converted = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        except cv2.error as e:
            ErrorHandler.handle(
                error=ErrorCode.FRAME_PROCESSING_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": type(e).__name__,
                    "Reason": "OpenCV error during color conversion (BGR→RGB)."
                }
            )
            return ErrorCode.FRAME_PREPROCESSING_ERROR

        # 4. Cast to uint8
        try:
            processedFrame = converted.astype(np.uint8)
        except (ValueError, TypeError) as e:
            ErrorHandler.handle(
                error=ErrorCode.FRAME_PROCESSING_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": type(e).__name__,
                    "Reason": "Failed to cast frame to uint8."
                }
            )
            return ErrorCode.FRAME_PREPROCESSING_ERROR
        Logger.info("Frame preprocessing completed successfully.")
        return processedFrame

        


    #####################
    ### analyze_frame ###
    #####################       
    def analyze_frame(self, frame: np.ndarray) -> Optional[np.ndarray]| ErrorCode | None:
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
        preprocessed_result = self.preprocess_frame(frame)
        if isinstance(preprocessed_result, ErrorCode):
            return preprocessed_result
        
        try:
            media_pose_result = self.pose.process(preprocessed_result)
        except TypeError as e:
            ErrorHandler.handle(
                error=ErrorCode.FRAME_ANALYSIS_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": "TypeError",
                    "Reason": "Invalid input type passed to MediaPipe Pose."
                }
            )
            return ErrorCode.FRAME_ANALYSIS_ERROR
        except ValueError as e:
            ErrorHandler.handle(
                error=ErrorCode.FRAME_ANALYSIS_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": "ValueError",
                    "Reason": "Frame shape or dimensions not supported (expected H, W, 3)."
                }
            )
            return ErrorCode.FRAME_ANALYSIS_ERROR
        except IndexError as e:
            ErrorHandler.handle(
                error=ErrorCode.FRAME_ANALYSIS_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": "IndexError",
                    "Reason": "Channel index out of range while accessing frame."
                }
            )
            return ErrorCode.FRAME_ANALYSIS_ERROR
        except MemoryError as e:
            ErrorHandler.handle(
                error=ErrorCode.FRAME_ANALYSIS_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": "MemoryError",
                    "Reason": "Insufficient memory while running MediaPipe Pose."
                }
            )
            return ErrorCode.FRAME_ANALYSIS_ERROR        
        except RuntimeError as e:
            ErrorHandler.handle(
                error=ErrorCode.FRAME_ANALYSIS_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": "RuntimeError",
                    "Reason": "Internal MediaPipe runtime error."
                }
            )
            return ErrorCode.FRAME_ANALYSIS_ERROR        
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.FRAME_ANALYSIS_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": type(e).__name__,
                    "Reason": "Unexpected error during pose analysis."
                }
            )
            return ErrorCode.FRAME_ANALYSIS_ERROR