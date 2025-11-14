############################################################
################ BODY TRACK // COMPONENTS ##################
############################################################
################### CLASS: PoseAnalyzer ####################
############################################################

###############
### IMPORTS ###
###############
import cv2, inspect
import numpy as np
import mediapipe as mp
import mediapipe.python.solutions.pose as Pose
from mediapipe.framework.formats import landmark_pb2
from Utilities.ErrorHandler import ErrorHandler, ErrorCode
from Utilities.Logger import Logger
from Utilities.ConfigLoader import ConfigLoader, ConfigParameters
from typing import Optional
from Components.SessionManager import FrameData as FrameData

##################################
### POSE LANDMARKS ARRAY ALIAS ###
##################################
"""
### Description:
`PoseArray` is a NumPy array containing body landmarks extracted from MediaPipe Pose.
Its shape is (33, 4), one row per landmark.

### Data type:
`np.float32`

### Explanation:
Each row corresponds to a single body landmark as defined in MediaPipe's 33-point skeleton model. The four columns represent:
- [i, 0] → x-coordinate (float, normalized to [0, 1], relative to frame width)
- [i, 1] → y-coordinate (float, normalized to [0, 1], relative to frame height)
- [i, 2] → z-coordinate (float, relative depth; negative = closer to camera)
- [i, 3] → visibility score (float in [0, 1], confidence that landmark is visible)

### Example:
`[0.5123, 0.7341, -0.1045, 0.9987]`
Landmark at ~51% width, 73% height, slightly closer to camera, ~99.9% visible.
"""
PoseLandmarksArray = np.ndarray

###########################
### POSE LANDMARK CLASS ###
###########################
class PoseLandmark:
    """
    ### Description:
    The `PoseLandmark` class defines constants for the 33 body landmarks
    detected by MediaPipe Pose. Each constant corresponds to a row index in the PoseArray (33x4 NumPy array).

    ### Columns in PoseArray:
    - [i, 0] → x (float, normalized to [0,1], relative to frame width)
    - [i, 1] → y (float, normalized to [0,1], relative to frame height)
    - [i, 2] → z (float, relative depth; negative = closer to camera)
    - [i, 3] → visibility (float in [0,1], probability landmark is visible)
    """
    NOSE              = 0
    LEFT_EYE_INNER    = 1
    LEFT_EYE          = 2
    LEFT_EYE_OUTER    = 3
    RIGHT_EYE_INNER   = 4
    RIGHT_EYE         = 5
    RIGHT_EYE_OUTER   = 6
    LEFT_EAR          = 7
    RIGHT_EAR         = 8
    MOUTH_LEFT        = 9
    MOUTH_RIGHT       = 10
    LEFT_SHOULDER     = 11
    RIGHT_SHOULDER    = 12
    LEFT_ELBOW        = 13
    RIGHT_ELBOW       = 14
    LEFT_WRIST        = 15
    RIGHT_WRIST       = 16
    LEFT_PINKY        = 17
    RIGHT_PINKY       = 18
    LEFT_INDEX        = 19
    RIGHT_INDEX       = 20
    LEFT_THUMB        = 21
    RIGHT_THUMB       = 22
    LEFT_HIP          = 23
    RIGHT_HIP         = 24
    LEFT_KNEE         = 25
    RIGHT_KNEE        = 26
    LEFT_ANKLE        = 27
    RIGHT_ANKLE       = 28
    LEFT_HEEL         = 29
    RIGHT_HEEL        = 30
    LEFT_FOOT_INDEX   = 31
    RIGHT_FOOT_INDEX  = 32
    NUM_OF_LANDMARKS  = 33

###########################
### POSE ANALYZER CLASS ###
###########################
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
            # Load frame dimensions from config (critical values: must exist, otherwise error is raised).
            # These values define the target width and height to which all incoming frames will be resized
            # before being passed to MediaPipe for analysis. Ensures consistent input shape for the model.
            self.frame_width = ConfigLoader.get(
                [ConfigParameters.Major.FRAME, ConfigParameters.Minor.WIDTH],
                critical_value=True
            )
            self.frame_height = ConfigLoader.get(
                [ConfigParameters.Major.FRAME, ConfigParameters.Minor.HEIGHT],
                critical_value=True
            )

            # Access the MediaPipe Pose solution class.
            # mp.solutions.pose is a wrapper that provides pretrained pose estimation.
            self.mp_pose = Pose

            # Initialize the MediaPipe Pose model.
            self.pose = self.mp_pose.Pose(
                static_image_mode        = False, # Optimized for video streams, not single images.
                model_complexity         = 1,     # Medium complexity (balance between speed and accuracy).
                smooth_landmarks         = True,  # Apply temporal smoothing to reduce landmark jitter between frames. 
                enable_segmentation      = False, # Disable segmentation mask (not needed for exercise tracking).
                min_detection_confidence = 0.5,   # Discard detections below 50% confidence.
                min_tracking_confidence  = 0.5    # aintain stable tracking across frames if confidence ≥ 50%.
            )

            # Load MediaPipe drawing utilities for optional visualization.
            self.mp_drawing = mp.solutions.drawing_utils

            # Load default landmark drawing styles (color, thickness, etc.).
            # Works together with mp_drawing to render pose annotations consistently.
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

    ######################
    ### VALIDATE FRAME ###
    ######################
    @staticmethod
    def validate_frame(frame_content:np.ndarray) -> Optional[ErrorCode]:
        """
        ### Brief:
        The `validate_frame` static method validates that the input frame is a proper image suitable 
        for further processing in the PoseAnalyzer pipeline.

        ### Arguments:
        - `frame_content` (np.ndarray): Input image frame to validate.

        ### Returns:
        - `None`: if the frame is valid.
        - `ErrorCode`: the specific error encountered.
        """
        # Check if frame is None.
        if frame_content is None:
            ErrorHandler.handle(
                error=ErrorCode.FRAME_VALIDATION_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Reason": "No frame data provided."
                }
            )
            return ErrorCode.FRAME_VALIDATION_ERROR

        # Check if frame is a numpy array.
        if not isinstance(frame_content, np.ndarray):
            ErrorHandler.handle(
                error=ErrorCode.FRAME_VALIDATION_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Reason": "Frame validation failed: not a NumPy array."
                }
            )
            return ErrorCode.FRAME_VALIDATION_ERROR

        # Check shape: must be 3D (H, W, C) with 3 channels (BGR).
        if frame_content.ndim != 3 or frame_content.shape[2] != 3:
            ErrorHandler.handle(
                error=ErrorCode.FRAME_VALIDATION_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Reason": "Frame validation failed: invalid dimensions."
                }
            )
            return ErrorCode.FRAME_VALIDATION_ERROR

        # If all checks passed.
        return None

    ########################
    ### PREPROCESS FRAME ###
    ########################
    @classmethod
    def preprocess_frame(cls, frame_content:np.ndarray) -> np.ndarray | ErrorCode:
        """
        ### Brief:
        The `preprocess_frame` static method preprocesses an input frame before sending it to the MediaPipe Pose model.
        1. Validate the input frame.
        2. Resize to the target resolution.
        3. Convert color space from BGR (OpenCV default) to RGB.
        4. Cast to uint8 for compatibility with MediaPipe.

        ### Arguments:
        - `frame_content` (np.ndarray): Raw frame captured from client video.

        ### Returns:
        - `np.ndarray` (RGB, uint8): The processed frame ready for model input.
        -  Returns ErrorCode if preprocessing fails.
        """
        # Resize the frame.
        try:
            frame_content = cv2.resize(frame_content, (cls.frame_width, cls.frame_height))
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

        # Convert color space BGR to RGB.
        try:
            frame_content = cv2.cvtColor(frame_content, cv2.COLOR_BGR2RGB)
        except cv2.error as e:
            ErrorHandler.handle(
                error=ErrorCode.FRAME_PREPROCESSING_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": type(e).__name__,
                    "Reason": "OpenCV error during color conversion (BGR→RGB)."
                }
            )
            return ErrorCode.FRAME_PREPROCESSING_ERROR

        # Cast to uint8.
        try:
            frame_content = frame_content.astype(np.uint8)
        except (ValueError, TypeError) as e:
            ErrorHandler.handle(
                error=ErrorCode.FRAME_PREPROCESSING_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": type(e).__name__,
                    "Reason": "Failed to cast frame to uint8."
                }
            )
            return ErrorCode.FRAME_PREPROCESSING_ERROR
        
        return frame_content

    #####################
    ### ANALYZE FRAME ###
    #####################       
    def analyze_frame(self, frame_data:FrameData) -> Optional[PoseLandmarksArray]| ErrorCode:
        """
        ### Brief:
        Processes a single video frame by converting it to RGB and running MediaPipe Pose
        detection on it. Extracts the body landmarks (if detected) and returns the results.

        ### Arguments:
        - `frame_data` (FrameData): Input frame data to be analyzed.

        ### Returns:
        - `Optional[PoseLandmarks]`:
        A NumPy array of shape `(33, 4)` if landmarks are detected, where each row corresponds
        to one human body landmark with the following columns:
        - `[i, 0]`: x-coordinate (float, normalized to [0,1], relative to image width).
        - `[i, 1]`: y-coordinate (float, normalized to [0,1], relative to image height).
        - `[i, 2]`: z-coordinate (float, relative depth, negative = closer to camera).
        - `[i, 3]`: visibility score (float in [0,1], probability that the landmark is visible).

        If detection fails, returns `ErrorCode`.
        """
        # Validate the frame.
        validation_result = self.validate_frame(frame_data.content)
        if isinstance(validation_result, ErrorCode):
            return ErrorCode.FRAME_VALIDATION_ERROR
        else:
            Logger.info(f"Frame {frame_data.frame_id} of session {frame_data.session_id} - validated successfully.")
        
        # Preprocess the frame.
        preprocessing_result = self.preprocess_frame(frame_data.content)
        if isinstance(preprocessing_result, ErrorCode):
            return preprocessing_result
        else:
            Logger.info(f"Frame {frame_data.frame_id} of session {frame_data.session_id} - preprocessed successfully.")
        
        try:
            # Run MediaPipe Pose
            result = self.pose.process(preprocessing_result)

            pose_landmarks:Optional[landmark_pb2.NormalizedLandmarkList] = result.pose_landmarks
            if pose_landmarks is None:
                ErrorHandler.handle(
                    error=ErrorCode.FRAME_ANALYSIS_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={ "Reason": "The returned pose landmarks object is None" }
                )
                return ErrorCode.FRAME_ANALYSIS_ERROR
            
            # Creating the output array from the landmarks returned from MediaPipe.
            landmarks_array:PoseLandmarksArray = np.array([
                [lm.x, lm.y, lm.z, lm.visibility] for lm in pose_landmarks.landmark
            ], dtype=np.float32)
            # If the size is invalid.
            if len(landmarks_array) != PoseLandmark.NUM_OF_LANDMARKS:
                ErrorHandler.handle(
                    error=ErrorCode.FRAME_ANALYSIS_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Reason": "The output landmarks array size is invalid",
                        "Contains": f"{len(landmarks_array)} rows",
                        "Supposed to contain": f"{PoseLandmark.NUM_OF_LANDMARKS} rows (landmarks)"
                    }
                )
                return ErrorCode.FRAME_ANALYSIS_ERROR

            Logger.info(f"Extracted {landmarks_array.shape[0]} landmarks "
                        f"from frame {frame_data.frame_id} (Session {frame_data.session_id}).")
            
            # Returning the output landmarks array.
            return landmarks_array
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