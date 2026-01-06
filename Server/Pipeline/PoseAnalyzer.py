############################################################
############# BODY TRACK // SERVER // PIPELINE #############
############################################################
################### CLASS: PoseAnalyzer ####################
############################################################

###############
### IMPORTS ###
###############
import cv2, inspect, os
import numpy as np
import mediapipe as mp
from typing import Optional

from Utilities.Config.ConfigLoader     import ConfigLoader
from Utilities.Config.ConfigParameters import ConfigParameters
from Utilities.Error.ErrorHandler      import ErrorHandler
from Utilities.Error.ErrorCode         import ErrorCode
from Utilities.Logger                  import Logger
from Data.Session.FrameData            import FrameData
from Data.Pose.PoseLandmarks           import PoseLandmark, PoseLandmarksArray

Pose = mp.solutions.pose

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
    def __init__(self):
        """
        ### Brief:
        The `__init__` method initializes the `PoseAnalyzer` class.
        """
        try:
            # Load configurations.
            self.retrieve_configurations()

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
                min_tracking_confidence  = 0.5    # Maintain stable tracking across frames if confidence ≥ 50%.
            )

            # Load MediaPipe drawing utilities for optional visualization.
            self.mp_drawing = mp.solutions.drawing_utils

            # Load default landmark drawing styles (color, thickness, etc.).
            # Works together with mp_drawing to render pose annotations consistently.
            self.mp_drawing_styles = mp.solutions.drawing_styles

            Logger.info("Initialized successfully.")
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

    #################
    ### DRAW POSE ###
    #################
    def _draw_pose(self, frame_bgr: np.ndarray, pose_landmarks) -> None:
        """
        Draws pose landmarks and connections on the given BGR frame (in-place).
        """
        if pose_landmarks is None:
            return

        self.mp_drawing.draw_landmarks(
            image=frame_bgr,
            landmark_list=pose_landmarks,
            connections=self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
        )

    ######################
    ### VALIDATE FRAME ###
    ######################
    @staticmethod
    def _validate_frame(frame_content:np.ndarray) -> Optional[ErrorCode]:
        """
        ### Brief:
        The `_validate_frame` static method validates that the input frame is a proper image suitable 
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
    
    ################################
    ### RESIZE WITH ASPECT RATIO ###
    ################################
    @staticmethod
    def _resize_with_aspect_ratio(frame_content:np.ndarray, target_width:int, target_height:int) -> np.ndarray:
        """
        ### Brief:
        The `_resize_with_aspect_ratio` method resizes the input frame to fit within the target dimensions
        while preserving the original aspect ratio.

        ### Arguments:
        - `frame_content` (np.ndarray): Input image frame to resize.
        - `target_width` (int): Desired width after resizing.
        - `target_height` (int): Desired height after resizing.

        ### Returns:
        - `np.ndarray`: The resized frame with preserved aspect ratio .
        """
        original_height, original_width = frame_content.shape[:2]
        original_ratio = original_width / original_height
        target_ratio = target_width / target_height

        # Calculate new dimensions while preserving aspect ratio.
        if original_ratio > target_ratio:
            new_width = target_width
            new_height = int(new_width / original_ratio)
        else:
            new_height = target_height
            new_width = int(new_height * original_ratio)

        # Resize the frame.
        resized_frame = cv2.resize(frame_content, (new_width, new_height))
        return resized_frame

    ########################
    ### PREPROCESS FRAME ###
    ########################
    def _preprocess_frame(self, frame_content:np.ndarray) -> np.ndarray | ErrorCode:
        """
        ### Brief:
        The `_preprocess_frame` static method preprocesses an input frame before sending it to the MediaPipe Pose model.
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
            frame_content = self._resize_with_aspect_ratio(frame_content, self.frame_width, self.frame_height)
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
    def analyze_frame(self, frame_data:FrameData) -> PoseLandmarksArray | ErrorCode:
        """
        ### Brief:
        Processes a single video frame by converting it to RGB and running MediaPipe Pose
        detection on it. Extracts the body landmarks (if detected) and returns the results.

        ### Arguments:
        - `frame_data` (FrameData): Input frame data to be analyzed.

        ### Returns:
        - `PoseLandmarks`:
        A NumPy array of shape `(33, 4)` if landmarks are detected, where each row corresponds
        to one human body landmark with the following columns:
        - `[i, 0]`: x-coordinate (float, normalized to [0,1], relative to image width).
        - `[i, 1]`: y-coordinate (float, normalized to [0,1], relative to image height).
        - `[i, 2]`: z-coordinate (float, relative depth, negative = closer to camera).
        - `[i, 3]`: visibility score (float in [0,1], probability that the landmark is visible).

        If detection fails, returns `ErrorCode`.
        """
        # Validate the frame.
        validation_result = self._validate_frame(frame_data.content)
        if isinstance(validation_result, ErrorCode):
            return ErrorCode.FRAME_VALIDATION_ERROR
        
        # Preprocess the frame.
        preprocessing_result = self._preprocess_frame(frame_data.content)
        if isinstance(preprocessing_result, ErrorCode):
            return preprocessing_result
        
        try:
            # Run MediaPipe Pose.
            result = self.pose.process(preprocessing_result)

            # Convert results to NormalizedLandmarkList.
            pose_landmarks = getattr(result, "pose_landmarks", None)
            if pose_landmarks is None:
                ErrorHandler.handle(
                    error=ErrorCode.FRAME_ANALYSIS_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={ "Reason": "The returned pose landmarks object is None" }
                )
                return ErrorCode.FRAME_ANALYSIS_ERROR
            
            # Convert NormalizedLandmarkList to landmarks list.
            pose_landmarks = getattr(pose_landmarks, "landmark", None)
            if pose_landmarks is None:
                ErrorHandler.handle(
                    error=ErrorCode.FRAME_ANALYSIS_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={ "Reason": "The returned pose landmarks object is None" }
                )
                return ErrorCode.FRAME_ANALYSIS_ERROR
            
            # Creating the output array from the landmarks returned from MediaPipe.
            results_array:list = []
            index:int = 0
            for lm in pose_landmarks:
                landmark_array:list = []
                # Checking for x and y coordinates - invalid coordinate is an error.
                try: 
                    landmark_array.append(lm.x)
                    landmark_array.append(lm.y)
                except:
                    ErrorHandler.handle(
                        error=ErrorCode.FRAME_ANALYSIS_ERROR,
                        origin=inspect.currentframe(),
                        extra_info={ "Reason": f"Failed to extract coordinates for landmark {index}" }
                    )
                    return ErrorCode.FRAME_ANALYSIS_ERROR
                
                # Checking for z coordinate and visibility measure - invalid is tolerated.
                try: landmark_array.append(lm.z)
                except: landmark_array.append(0.0)
                try: landmark_array.append(lm.visibility)
                except: landmark_array.append(0.0)

                results_array.append(landmark_array)
                index += 1

            # Converting the results array (which is a list) to a np.array.
            landmarks_array:PoseLandmarksArray = np.array(results_array, dtype=np.float32)
            # If the size is invalid.
            if len(landmarks_array) != PoseLandmark.NUM_OF_LANDMARKS.value:
                ErrorHandler.handle(
                    error=ErrorCode.FRAME_ANALYSIS_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Reason": "The output landmarks array size is invalid",
                        "Contains": f"{len(landmarks_array)} rows",
                        "Supposed to contain": f"{PoseLandmark.NUM_OF_LANDMARKS.value} rows (landmarks)"
                    }
                )
                return ErrorCode.FRAME_ANALYSIS_ERROR
                        
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
                    "Exception type": type(e),
                    "Reason": "Unexpected error during pose analysis."
                }
            )
            return ErrorCode.FRAME_ANALYSIS_ERROR

    ###############################
    ### RETRIEVE CONFIGURATIONS ###
    ############################### 
    def retrieve_configurations(self) -> None:
        """
        ### Brief:
        The `retrieve_configurations` method gets the updated configurations from the
        configuration file.
        """
        # Load frame dimensions from config (critical values: must exist, otherwise error is raised).
        # These values define the target width and height to which all incoming frames will be resized
        # before being passed to MediaPipe for analysis. Ensures consistent input shape for the model.
        self.frame_width = ConfigLoader.get([
            ConfigParameters.Major.FRAME,
            ConfigParameters.Minor.WIDTH
        ])
        self.frame_height = ConfigLoader.get([
            ConfigParameters.Major.FRAME,
            ConfigParameters.Minor.HEIGHT
        ])
        self.log_level = ConfigLoader.get([
            ConfigParameters.Major.LOG,
            ConfigParameters.Minor.LOG_LEVEL
        ])

        Logger.info("Retrieved configurations successfully")