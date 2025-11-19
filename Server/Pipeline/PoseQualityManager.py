############################################################
############# BODY TRACK // SERVER // PIPELINE #############
############################################################
############### CLASS: PoseQualityManager ##################
############################################################

###############
### IMPORTS ###
###############
import numpy as np, inspect
from typing import Optional

from Server.Utilities.Error.ErrorHandler import ErrorHandler
from Server.Utilities.Error.ErrorHandler import ErrorCode
from Server.Utilities.Logger import Logger
from Server.Data.Pose.PoseLandmarks import PoseLandmarksArray
from Server.Data.Pose.PoseQuality import PoseQuality
from Server.Data.Pose.PoseQualityResult import PoseQualityResult

####################################
### POSE QUALITY MANAGER CLASS #####
####################################
class PoseQualityManager:
    """
    ### Description:
    The `PoseQualityManager` class evaluates the quality of pose detection
    results returned by the MediaPipe Pose model.

    ### Responsibilities:
    - Analyzes the MediaPipe `results` object (pose_landmarks).
    - Detects problems such as:
        - No person in frame
        - Low visibility / partial body
        - Subject too far / too close
        - Unstable movement between frames
    - Return a single `PoseQualityResult` per frame.


    ### Notes:
    This class only detects and reports pose quality issues.
    It does **not** decide how to handle them (alert, skip, reuse, etc.).
    That responsibility is left to higher-level components.
    """
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self):
        """
        ### Brief:
        Initializes the PoseQualityManager and loads all pose-quality thresholds
        from the configuration system.

        ### Notes:
        Thresholds control detection of “too far”, “too close”, low visibility,
        partial body, and frame instability.
        All values are loaded from config so they can be tuned without modifying code.
        last_landmarks stores the previous frame's (x,y) points for stability checks.
        """
        try:
            from Server.Utilities.Config.ConfigLoader import ConfigLoader
            from Server.Utilities.Config.ConfigParameters import ConfigParameters
            # Load quality thresholds from configuration.
            self.stability_threshold = ConfigLoader.get(
                key=[
                    ConfigParameters.Major.POSE,
                    ConfigParameters.Minor.STABILITY_THRESHOLD
                ],
                critical_value=True
            )
            self.bbox_too_far = ConfigLoader.get(
                key=[
                    ConfigParameters.Major.POSE,
                    ConfigParameters.Minor.BBOX_TOO_FAR
                ],
                critical_value=True
            )
            self.bbox_too_close = ConfigLoader.get(
                key=[
                    ConfigParameters.Major.POSE,
                    ConfigParameters.Minor.BBOX_TOO_CLOSE
                ],
                critical_value=True
            )
            self.mean_vis_threshold = ConfigLoader.get(
                key=[
                    ConfigParameters.Major.POSE,
                    ConfigParameters.Minor.MEAN_VIS_THRESHOLD
                ],
                critical_value=True
            )
            self.partial_count_threshold = ConfigLoader.get(
                key=[
                    ConfigParameters.Major.POSE,
                    ConfigParameters.Minor.PARTIAL_COUNT_THRESHOLD
                ],
                critical_value=True
            )
            self.minimum_bbox_area = ConfigLoader.get(
                key=[
                    ConfigParameters.Major.POSE,
                    ConfigParameters.Minor.MINIMUM_BBOX_AREA
                ],
                critical_value=True
            )

            # Track last landmarks as an array of (x,y) for stability checks.
            self.last_landmarks = None
            self.last_quality = PoseQuality.OK

            Logger.info("PoseQualityManager initialized successfully.")
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.FAILED_TO_INITIALIZE_QUALITY_MANAGER,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": type(e).__name__,
                    "Reason": "Unexpected error while initializing PoseQualityManager."
                }
            )

    ###################################
    ### COMPUTE MEAN LANDMARK DELTA ###
    ###################################
    def _compute_mean_landmark_delta(self, current_xy: np.ndarray) -> Optional[float]:
        """
        ### Brief:
        The `_compute_mean_landmark_delta` method computes the average movement of all
        landmarks between the previous frame and the current frame. Movement is measured
        as the Euclidean distance between corresponding (x,y) points.

        ### Returns:
        - `float`: Mean movement across all landmarks.
        - `None`: If no previous frame exists or shapes do not match.
        """
        try:
            # If we have no previous frame → cannot compute movement.
            if self.last_landmarks is None:
                return None
        
            # Convert to NumPy arrays (ensures proper dtype).
            previous = np.asarray(self.last_landmarks, dtype=np.float32)
            current = np.asarray(current_xy, dtype=np.float32)

            # Shape mismatch → cannot compute movement.
            if previous.shape != current.shape:
               Logger.debug(
                f"PoseQualityManager: Landmark shape mismatch. "
                f"Prev={previous.shape}, Curr={current.shape}"
                )
               return None

            # Compute the difference between frames: (dx, dy) for every landmark.
            # This subtracts two (N,2) arrays element-wise.
            deltas = current - previous    # shape (N,2)

            # Compute Euclidean distances for each landmark.
            # sqrt(dx² + dy²) using vectorized NumPy operations.
            distances = np.sqrt(np.sum(deltas ** 2, axis=1))  # Euclidean distances per landmark

            # Return the average distance across all landmarks.
            return float(np.mean(distances))
        except Exception as e:
            # Critical but not fatal → log and disable stability this frame.
            ErrorHandler.handle(
                error=ErrorCode.FRAME_STABILITY_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": type(e).__name__,
                    "Reason": "Error computing frame-to-frame stability",
                },
            )
            return None

    #################
    ### BBOX AREA ###
    #################
    def _bbox_area(self, x_array: np.ndarray, y_array: np.ndarray) -> float:
        """
        ### Brief:
        The `_bbox_area` method computes the bounding-box area based on min/max x and y coordinates.

        ### Arguments:
        - `x_array` (np.ndarray): All x-coordinates of detected landmarks.
        - `y_array` (np.ndarray): All y-coordinates of detected landmarks.

        ### Returns:
        - `float`: The computed bounding-box area. Returns 0.0 on failure.
        """
        try:
            return float((np.max(x_array) - np.min(x_array)) * (np.max(y_array) - np.min(y_array)))
        except Exception:
            return 0.0

    #############################
    ### IS NO PERSON BY SHAPE ###
    #############################
    def _is_no_person_by_shape(self, landmark_array: PoseLandmarksArray) -> bool:
        """
        ### Brief:
        The `_is_no_person_by_shape` method checks whether the landmark array is invalid due to missing data
        or incorrect shape.

        ### Arguments:
        - `landmark_array` (PoseLandmarksArray): Raw landmarks (N×4 or N×3).

        ### Returns:
        - `bool`: True if shape indicates that no person is present.
        """
        return (landmark_array is None) or (landmark_array.size == 0) or (landmark_array.ndim != 2) or (landmark_array.shape[1] < 3)

    ############################
    ### IS NO PERSON BY BBOX ###
    ############################
    def _is_no_person_by_bbox(self, area: float) -> bool:
        """
        ### Brief:
        The `_is_no_person_by_bbox` method determines whether the bounding-box area is below the minimum threshold.

        ### Arguments:
        - `area` (float): The computed bounding-box area.

        ### Returns:
        - `bool`: True if the area is too small to represent a real person.
        """
        return area <= self.minimum_bbox_area

    ##################
    ### IS TOO FAR ###
    ##################
    def _is_too_far(self, area: float) -> bool:
        """
        ### Brief:
        The `_is_too_far` method returns True if the detected person is too far from the camera.

        ### Arguments:
        - `area` (float): Bounding-box area of the detected pose.

        ### Returns:
        - `bool`: True if the area is smaller than the configured "far" threshold.
        """
        return area < self.bbox_too_far

    ####################
    ### IS TOO CLOSE ###
    ####################
    def _is_too_close(self, area: float) -> bool:
        """
        ### Brief:
        The `_is_too_close` method returns True if the person is too close to the camera.

        ### Arguments:
        - `area` (float): Bounding-box area of the detected pose.

        ### Returns:
        - `bool`: True if the area exceeds the "too close" threshold.
        """
        return area > self.bbox_too_close

    #########################
    ### IS LOW VISIBILITY ###
    #########################
    def _is_low_visibility(self, visibility_array: np.ndarray) -> bool:
        """
        ### Brief:
        The `_is_low_visibility` method checks whether overall landmark visibility is too low.

        ### Arguments:
        - `visibility_array` (np.ndarray): Visibility values for each landmark.

        ### Returns:
        - `bool`: True if mean visibility is below the configured threshold.

        ### Notes:
        - If the array is empty, visibility is considered too low.
        """
        if visibility_array.size == 0:
            return True
        return float(np.mean(visibility_array)) < self.mean_vis_threshold

    #######################
    ### IS PARTIAL BODY ###
    #######################
    def _is_partial_body(self, visibility_array: np.ndarray) -> bool:
        """
        ### Brief:
        The `_is_partial_body` method detects whether too many landmarks have low visibility.

        ### Arguments:
        - `visibility_array` (np.ndarray): Visibility values for each landmark.

        ### Returns:
        - `bool`: True if the number of poorly visible landmarks exceeds the limit.
        """
        return int(np.sum(visibility_array < self.mean_vis_threshold)) > self.partial_count_threshold

    ###################
    ### IS UNSTABLE ###
    ###################
    def _is_unstable(self, current_xy: np.ndarray) -> bool:
        """
        ### Brief:
        The `_is_unstable` method checks if movement between the current and previous frame is too large.

        ### Arguments:
        - `current_xy` (np.ndarray): Current frame's (x, y) coordinates (N×2).

        ### Returns:
        - `bool`: True if average movement exceeds the stability threshold.

        ### Notes:
        - Uses `_compute_mean_landmark_delta` internally.
        """
        mean_delta = self._compute_mean_landmark_delta(current_xy)
        return (mean_delta is not None) and (mean_delta > self.stability_threshold)

    ##########################
    ### EVALUATE LANDMARKS ###
    ##########################
    def evaluate_landmarks(self, landmarks: PoseLandmarksArray) -> PoseQualityResult | ErrorCode:
        """
        ### Brief:
        The `evaluate_landmarks` method evaluates the quality of a pose frame based on landmark
        positions and visibility values. Detects conditions such as no person, low visibility,
        partial body, incorrect distance from camera, or unstable motion.

        ### Arguments:
        - `landmarks` (PoseLandmarksArray): A NumPy array of shape (N,4) containing
        (x, y, z, visibility) for each detected landmark.

        ### Returns:
        - `PoseQualityResult`: Contains:
            - `PoseQuality`: A single enum describing the detected issue:
                - `OK`           → All checks passed.
                - `NO_PERSON`    → No valid person detected.
                - `LOW_VISIBILITY` → Mean visibility too low.
                - `PARTIAL_BODY` → Too many landmarks with low visibility.
                - `TOO_FAR`      → Person is too small in frame.
                - `TOO_CLOSE`    → Person is too large in frame.
                - `UNSTABLE`     → Sudden movement between frames.
            - `mean_visibility` (float): Average visibility of all landmarks.
            - `bbox_area` (float): Computed bounding-box area of the pose.
        - `ErrorCode`: If an internal error occurs during evaluation.

        ### Notes:
        - Returns immediately on first detected issue (logical prioritization).
        - Updates `last_landmarks` only when meaningful for temporal analysis.
        """
        try:
            # Shape validation
            if self._is_no_person_by_shape(landmarks):
                self.last_landmarks = None
                return PoseQualityResult(
                    quality=PoseQuality.NO_PERSON,
                    mean_visibility=0.0,
                    bbox_area=0.0
                )

            # Cast and sanitize
            x_array = np.nan_to_num(landmarks[:, 0], nan=0.0)
            y_array = np.nan_to_num(landmarks[:, 1], nan=0.0)
            visibility_array = np.nan_to_num(
                landmarks[:, 3] if landmarks.shape[1] >= 4 else landmarks[:, 2],
                nan=0.0
            )

            # Precomputed values
            area = self._bbox_area(x_array, y_array)
            current_xy = np.stack([x_array, y_array], axis=1)
            mean_vis = float(np.mean(visibility_array)) if visibility_array.size > 0 else 0.0

            # --- PRIORITY: NO PERSON ---
            if self._is_no_person_by_bbox(area):
                self.last_landmarks = None
                return PoseQualityResult(
                    quality=PoseQuality.NO_PERSON,
                    mean_visibility=mean_vis,
                    bbox_area=area
                )

            # --- TOO FAR ---
            if self._is_too_far(area):
                self.last_landmarks = current_xy.copy()
                return PoseQualityResult(
                    quality=PoseQuality.TOO_FAR,
                    mean_visibility=mean_vis,
                    bbox_area=area
                )

            # --- TOO CLOSE ---
            if self._is_too_close(area):
                self.last_landmarks = current_xy.copy()
                return PoseQualityResult(
                    quality=PoseQuality.TOO_CLOSE,
                    mean_visibility=mean_vis,
                    bbox_area=area
                )

            # --- LOW VISIBILITY ---
            if self._is_low_visibility(visibility_array):
                self.last_landmarks = current_xy.copy()
                return PoseQualityResult(
                    quality=PoseQuality.LOW_VISIBILITY,
                    mean_visibility=mean_vis,
                    bbox_area=area
                )

            # --- PARTIAL BODY ---
            if self._is_partial_body(visibility_array):
                self.last_landmarks = current_xy.copy()
                return PoseQualityResult(
                    quality=PoseQuality.PARTIAL_BODY,
                    mean_visibility=mean_vis,
                    bbox_area=area
                )

            # --- UNSTABLE ---
            if self._is_unstable(current_xy):
                self.last_landmarks = current_xy.copy()
                return PoseQualityResult(
                    quality=PoseQuality.UNSTABLE,
                    mean_visibility=mean_vis,
                    bbox_area=area
                )

            # --- OK ---
            self.last_landmarks = current_xy.copy()
            return PoseQualityResult(
                quality=PoseQuality.OK,
                mean_visibility=mean_vis,
                bbox_area=area
            )

        except MemoryError:
            self.last_landmarks = None
            ErrorHandler.handle(
                error=ErrorCode.QUALITY_CHECKING_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": "MemoryError",
                    "Reason": "Insufficient memory during pose quality evaluation."
                }
            )
            return ErrorCode.QUALITY_CHECKING_ERROR

        except ValueError:
            self.last_landmarks = None
            ErrorHandler.handle(
                error=ErrorCode.QUALITY_CHECKING_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": "ValueError",
                    "Reason": "Invalid numeric data while analyzing pose landmarks."
                }
            )
            return ErrorCode.QUALITY_CHECKING_ERROR

        except Exception as e:
            self.last_landmarks = None
            ErrorHandler.handle(
                error=ErrorCode.QUALITY_CHECKING_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": type(e).__name__,
                    "Reason": "Unexpected error in PoseQualityManager.evaluate_landmarks."
                }
            )
            return ErrorCode.QUALITY_CHECKING_ERROR