###############################################################
############## BODY TRACK // SERVER // PIPELINE ###############
###############################################################
################# CLASS: PoseQualityManager ###################
###############################################################

###############
### IMPORTS ###
###############
from __future__ import annotations
import numpy as np
import inspect
from typing import List, Set, Dict, Any, TYPE_CHECKING

from Utilities.Error.ErrorHandler import ErrorHandler
from Utilities.Error.ErrorCode    import ErrorCode
from Utilities.Logger             import Logger

from Data.Session.SessionData     import SessionData
from Data.Session.ExerciseType    import ExerciseType
from Data.Pose.PoseLandmarks      import PoseLandmarksArray
from Data.Pose.PoseQuality        import PoseQuality
from Data.Pose.PositionSide       import PositionSide
from Data.History.HistoryData     import HistoryData
from Data.History.HistoryDictKey  import HistoryDictKey
from Data.Joints.JointAngle       import JointAngle, Joint

if TYPE_CHECKING:
    from Data.Debug.FrameTrace    import FrameTrace

####################################
### POSE QUALITY MANAGER CLASS #####
####################################
class PoseQualityManager:
    """
    ### Description:
    The `PoseQualityManager` class evaluates pose quality for a single frame in
    a stateless manner.

    ### Responsibilities:
    Detects hard failures: `NO_PERSON`, `TOO_FAR`, `PARTIAL_BODY`, `UNSTABLE`.

    ### Mathematical and Logical Overview:
    This class implements the third stage in the BodyTrack pose-analysis pipeline:
        1) PoseAnalyzer: Raw landmark extraction (MediaPipe)
        2) PositionSideDetector: Body orientation (LEFT / RIGHT / FRONT)
        3) PoseQualityManager: Frame-level technical validation (this class)

    The `PoseQualityManager` is intentionally designed to be stateless and
    exercise-aware. It evaluates whether a given frame is technically suitable
    for further biomechanical analysis, without making semantic or instructional
    decisions.

    ### Design Principles:
    - Stateless evaluation: The manager does not store temporal state internally.
    All temporal comparisons rely exclusively on data stored in HistoryData.

    - Exercise-aware filtering: Only landmarks that are actually required for
    the current exercise are validated. This prevents false negatives when non-relevant
    body parts (e.g., legs during biceps curls) are outside the frame.

    - Side-aware analysis: Landmark relevance is filtered according to the detected
    body orientation (LEFT, RIGHT, FRONT), ensuring robustness to side views and
    partial occlusion.

    - Hard-failure detection only: This class reports technical validity, not coaching
    or feedback decisions. All detected issues are objective, frame-level failures.

    ### Step-by-Step Logic:
    #### STEP 1 — Landmark Existence Validation:
    The first validation ensures that the landmark array exists and has a valid
    shape. If landmarks are missing or malformed, no person is considered detected.

    ##### Mathematically:
    If landmarks is None OR empty OR not a 2D array → NO_PERSON

    This prevents undefined behavior in downstream numerical calculations.

    #### STEP 2 — Bounding Box Area Analysis:
    The bounding box area is computed using normalized MediaPipe coordinates:
    `area = (max(x) - min(x)) X (max(y) - min(y))`

    This represents the 2D screen-space footprint of the detected pose.

    ##### Interpretation:
    - Very small area: person is too far or detection is unreliable
    - Stable, resolution-independent metric
    - Independent of camera resolution

    ##### Two checks are performed:
    - `area ≤ minimum_bbox_area` leads to `NO_PERSON`
    - `area < bbox_too_far` - candidate for `TOO_FAR` (validated later)

    #### STEP 3 — Exercise-Specific Visibility Validation:
    Instead of checking global visibility across all landmarks, the system evaluates
    only landmarks that are biomechanically required for the current exercise.

    ##### Process:
    1. Extract landmark indices
    2. Filter landmarks based on detected body side
    3. Compute visibility ratio

    ##### Decision rule:
    - If `visibility_ratio < required_visibility_ratio`, it is `PARTIAL_BODY`

    ##### This approach allows:
    - Feet to be outside frame during upper-body exercises
    - Side views without penalizing occluded limbs
    - Robust operation across multiple exercise types

    #### STEP 4 — Temporal Stability Check:
    Frame-to-frame stability is evaluated using mean Euclidean landmark displacement:
    `mean_delta = mean(||current_xy - previous_xy||)`

    ##### Where:
    - current_xy  = (x, y) landmark positions of current frame
    - previous_xy = last accepted frame from HistoryData

    This measures average motion magnitude across all landmarks.

    ##### Interpretation:
    - Low values lead to natural exercise motion
    - High values lead camera shake, frame jump, detection glitch

    ##### Decision rule:
    - `mean_delta > stability_threshold` leads to `UNSTABLE`

    Temporal state is fully externalized to `HistoryData`, preserving stateless design.
    """
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self):
        """
        ### Brief:
        The `__init__` method initializes the `PoseQualityManager` instance
        by retrieving configuration parameters and preparing the manager for
        pose quality evaluations.
        """
        try:
            self.retrieve_configurations()
            Logger.info("Initialized successfully.")
        except Exception:
            ErrorHandler.handle(
                error=ErrorCode.FAILED_TO_INITIALIZE_QUALITY_MANAGER,
                origin=inspect.currentframe()
            )

    ############################################################################
    ############################## PUBLIC METHODS ##############################
    ############################################################################

    ##########################
    ### EVALUATE LANDMARKS ###
    ##########################
    def evaluate_landmarks(
            self,
            session_data:SessionData,
            landmarks:PoseLandmarksArray
        ) -> PoseQuality | ErrorCode:
        """
        ### Brief:
        The `evaluate_landmarks` method assesses the quality of the provided
        pose landmarks based on various criteria such as visibility, bounding
        box area, and temporal stability.

        ### Arguments:
        - `session_data` (SessionData): The session data containing history
                                        and exercise type information.
        - `landmarks` (PoseLandmarksArray): The array of pose landmarks to evaluated.

        ### Returns:
        - `PoseQuality` if the evaluation is successful.
        - `ErrorCode` if an error occurs during evaluation.
        """
        history:HistoryData = session_data.get_history()
        exercise_type:ExerciseType = session_data.get_exercise_type()
        position_side:PositionSide = history.get_position_side()
        frame_trace:FrameTrace = session_data.get_last_frame_trace()

        ##################################
        ### CHECKING ELEMENTS VALIDITY ###
        ##################################
        if exercise_type is None:
            ErrorHandler.handle(
                error=ErrorCode.EXERCISE_TYPE_DOES_NOT_EXIST,
                origin=inspect.currentframe()
            )
            return ErrorCode.EXERCISE_TYPE_DOES_NOT_EXIST
        
        if position_side is None:
            ErrorHandler.handle(
                error=ErrorCode.POSITION_SIDE_DOES_NOT_EXIST,
                origin=inspect.currentframe()
            )
            return ErrorCode.POSITION_SIDE_DOES_NOT_EXIST

        ##############
        ### STEP 1 ### - Validate landmark existence.
        ##############
        if landmarks is None or landmarks.size == 0 or landmarks.ndim != 2:
            if frame_trace is not None:
                session_data.get_last_frame_trace().add_event(
                    stage="PoseQualityManager",
                    success=True,
                    result_type="No Person",
                    result={"Landmarks":  "Missing"} if landmarks is None else {"Landmarks": "Invalid shape"}
                )
            return PoseQuality.NO_PERSON

        ##############
        ### STEP 2 ### - Extract arrays safely.
        ##############
        x:np.ndarray = np.nan_to_num(landmarks[:, 0], nan=0.0)
        y:np.ndarray = np.nan_to_num(landmarks[:, 1], nan=0.0)

        visibility:np.ndarray = (landmarks[:, 3] if landmarks.shape[1] >= 4 else landmarks[:, 2])
        visibility:np.ndarray = np.nan_to_num(visibility, nan=0.0)
        current_xy:np.ndarray = np.stack([x, y], axis=1)

        ##############
        ### STEP 3 ### - Bounding box, checking if no person is in frame.
        ##############
        area:float = self._bbox_area(x, y)

        # If the area is too small, likely no person detected.
        if area <= self.minimum_bbox_area:
            if frame_trace is not None:
                session_data.get_last_frame_trace().add_event(
                    stage="PoseQualityManager",
                    success=True,
                    result_type="No Person",
                    result={ "Bounding Box Area": "Too small" }
                )
            return PoseQuality.NO_PERSON

        ##############
        ### STEP 4 ### - Required landmarks visibility.
        ##############
        # Get required landmark indices for the exercise type and position side.
        required_indices:Set[int] = self._required_landmark_indices(
            exercise_type=exercise_type,
            position_side=position_side,
            extended_evaluation=session_data.get_extended_evaluation()
        )
        # Count how many required landmarks are sufficiently visible.
        visible_count:int = sum(
            1 for idx in required_indices
            if visibility[idx] >= self.visibility_good_threshold
        )
        # Calculate visibility ratio.
        visibility_ratio:float = visible_count / len(required_indices)

        # If the area is below the "too far" threshold, mark as TOO FAR.
        if area < self.bbox_too_far and visibility_ratio < self.required_visibility_ratio:
            if frame_trace is not None:
                session_data.get_last_frame_trace().add_event(
                    stage="PoseQualityManager",
                    success=True,
                    result_type="Too Far",
                    result={ "Bounding Box Area": "Below too far threshold and insufficient visibility" }
                )
            return PoseQuality.TOO_FAR
        
        # If visibility ratio is below required threshold, mark as PARTIAL BODY.
        elif area >= self.bbox_too_far and visibility_ratio < self.required_visibility_ratio:
            if frame_trace is not None:
                session_data.get_last_frame_trace().add_event(
                    stage="PoseQualityManager",
                    success=True,
                    result_type="Partial Body",
                    result={ "Visibility": "Insufficient for required landmarks" }
                )
            return PoseQuality.PARTIAL_BODY

        ##############
        ### STEP 5 ### - Stability check.
        ##############
        # Retrieve last stable landmarks from history.
        last_valid_frame:Dict[str, Any] | None = history.get_last_valid_frame()
        if last_valid_frame is None:
            if history.is_state_ok() and history.get_current_number_of_frames() > 1:
                ErrorHandler.handle(
                    error=ErrorCode.LAST_VALID_FRAME_MISSING,
                    origin=inspect.currentframe()
                )
                return ErrorCode.LAST_VALID_FRAME_MISSING
            else:
                if frame_trace is not None:
                    session_data.get_last_frame_trace().add_event(
                        stage="PoseQualityManager",
                        success=True,
                        result_type="OK",
                        result={ "No Previous Valid Frame": "Skipping stability check" }
                    )
                return PoseQuality.OK
        
        prev_xy:np.ndarray | None = last_valid_frame.get(HistoryDictKey.Frame.LANDMARKS, None)
        # If previous landmarks exist, compute mean delta and check stability.
        if prev_xy is not None:
            mean_delta:float | None = self._mean_landmark_delta(prev_xy, current_xy)
            if mean_delta is not None and mean_delta > self.stability_threshold:
                
                if frame_trace is not None:
                    frame_trace.add_event(
                        stage="PoseQualityManager",
                        success=True,
                        result_type="Unstable",
                        result={ "Mean landmark delta exceeds stability threshold": mean_delta }
                    )
                return PoseQuality.UNSTABLE
            
        ##############
        ### STEP 6 ### - Frame accepted.
        ##############
        if frame_trace is not None:
            session_data.get_last_frame_trace().add_event(
                stage="PoseQualityManager",
                success=True,
                result_type="OK",
                result={ "Frame passed": "All quality checks" }
            )
        return PoseQuality.OK

    #####################################################################
    ############################## HELPERS ##############################
    #####################################################################

    #################
    ### BBOX AREA ###
    #################
    def _bbox_area(self, x:np.ndarray, y:np.ndarray) -> float:
        """
        ### Brief:
        The `_bbox_area` method calculates the area of the bounding box
        that encompasses the provided x and y coordinates.

        ### Arguments:
        - `x` (np.ndarray): The x-coordinates of the landmarks.
        - `y` (np.ndarray): The y-coordinates of the landmarks.

        ### Returns:
        - The area of the bounding box as a float.
        """
        try:              return float((x.max() - x.min()) * (y.max() - y.min()))
        except Exception: return 0.0

    ###########################
    ### MEAN LANDMARK DELTA ###
    ###########################
    def _mean_landmark_delta(self, prev:np.ndarray, curr:np.ndarray) -> float | None:
        """
        ### Brief:
        The `_mean_landmark_delta` method calculates the mean Euclidean
        distance between corresponding landmarks in two frames.

        ### Arguments:
        - `prev` (np.ndarray): The landmark positions from the previous frame.
        - `curr` (np.ndarray): The landmark positions from the current frame.

        ### Returns:
        - The mean Euclidean distance as a float if the shapes match.
        - `None` if the shapes of the input arrays do not match.
        """
        # Ensure both arrays have the same shape.
        if prev.shape != curr.shape: return None

        # Calculate mean Euclidean distance.
        deltas = curr - prev
        # Calculate the Euclidean norm for each landmark and then compute the mean.
        return float(np.mean(np.linalg.norm(deltas, axis=1)))

    ##################################
    ### REQUIRED LANDMARKS INDICES ###
    ##################################
    def _required_landmark_indices(
            self,
            exercise_type:ExerciseType,
            position_side:PositionSide,
            extended_evaluation:bool
        ) -> Set[int]:
        """
        ### Brief:
        The `_required_landmark_indices` method identifies the set of landmark
        indices that must be visible for a given exercise type and body side.

        ### Arguments:
        - `exercise_type` (ExerciseType): The type of exercise being performed.
        - `position_side` (PositionSide): The side of the body being evaluated.
        - `extended_evaluation` (bool): Flag indicating whether to include
                                        additional landmarks for extended evaluation.

        ### Returns:
        - A `set` of integers representing the required landmark indices.
        """
        joints:List[Joint] = JointAngle.get_all_joints(
            cls_name=JointAngle.exercise_type_to_joint_type(exercise_type),
            position_side=position_side,
            extended_evaluation=extended_evaluation
        )

        indices:Set[int] = set()

        # Collect required landmark indices based on joints and body side.
        for joint in joints:
            for landmark in joint.landmarks:
                indices.add(landmark)

        return indices

    ###############################
    ### RETRIEVE CONFIGURATIONS ###
    ###############################
    def retrieve_configurations(self) -> None:
        """
        ### Brief:
        The `retrieve_configurations` method fetches configuration parameters
        related to pose quality evaluation from the configuration loader.
        """
        from Utilities.Config.ConfigLoader import ConfigLoader
        from Utilities.Config.ConfigParameters import ConfigParameters

        self.stability_threshold:float = ConfigLoader.get([
            ConfigParameters.Major.POSE,
            ConfigParameters.Minor.STABILITY_THRESHOLD
        ])

        self.bbox_too_far:float = ConfigLoader.get([
            ConfigParameters.Major.POSE,
            ConfigParameters.Minor.BBOX_TOO_FAR
        ])

        self.minimum_bbox_area:float = ConfigLoader.get([
            ConfigParameters.Major.POSE,
            ConfigParameters.Minor.MINIMUM_BBOX_AREA
        ])

        # New, explicit thresholds
        self.visibility_good_threshold:float = ConfigLoader.get([
            ConfigParameters.Major.POSE,
            ConfigParameters.Minor.VISIBILITY_GOOD_THRESHOLD
        ])

        self.required_visibility_ratio:float = ConfigLoader.get([
            ConfigParameters.Major.POSE,
            ConfigParameters.Minor.REQUIRED_VISIBILITY_RATIO
        ])