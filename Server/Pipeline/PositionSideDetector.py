###############################################################
############### BODY TRACK // SERVER // PIPELINE ##############
###############################################################
################# CLASS: PositionSideDetector #################
###############################################################

###############
### IMPORTS ###
###############
# Python libraries.
import inspect
import numpy as np
from typing import List

from Utilities.Logger                  import Logger
from Utilities.Error.ErrorHandler      import ErrorHandler
from Utilities.Error.ErrorCode         import ErrorCode
from Utilities.Config.ConfigLoader     import ConfigLoader
from Utilities.Config.ConfigParameters import ConfigParameters

from Data.Pose.PositionSide            import PositionSide
from Data.Pose.PoseLandmarks           import LeftLandmark, RightLandmark
from Data.Session.ExerciseType         import ExerciseType

#####################################
### POSITION SIDE DETECTOR CLASS ####
#####################################
class PositionSideDetector:
    """
    ### Description:
    The `PositionSideDetector` determines from which side the user is filmed
    (`LEFT`, `RIGHT`, `FRONT`, `UNKNOWN`) based on landmark visibility dominance.

    ### Responsibilities:
    - Analyze landmark visibility distribution
    - Determine filming side robustly
    - Validate side against the exercise requirements
    - Return semantic errors if side is invalid
    """
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self):
        """
        ### Brief:
        The `__init__` method initialize the `PositionSideDetector` and
        loads configuration thresholds.
        """
        try:
            self.retrieve_configurations()
            Logger.info("Initialized successfully.")
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.FAILED_TO_INITIALIZE_SIDE_DETECTOR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception": type(e).__name__,
                    "Reason": "Failed during PositionSideDetector initialization."
                }
            )

    ############################################################################
    ############################## PUBLIC METHODS ##############################
    ############################################################################

    ###########################
    ### DETECT AND VALIDATE ###
    ###########################
    def detect_and_validate(self, landmarks:np.ndarray, exercise_type:ExerciseType) -> PositionSide | ErrorCode:
        """
        ### Brief:
        The `detect_and_validate` determines the filming side and validates it against the exercise.

        ### Arguments:
        - `landmarks` (np.ndarray): MediaPipe landmarks (N x 4).
        - `exercise_type` (ExerciseType): Current exercise.

        ### Returns:
        - A `PositionSide` if detection completed successfully.
        - An `ErrorCode` if an error occurred.
        """
        try:
            # Extract visibility scores.
            visibility = landmarks[:, 3]

            # Compute visibility ratios per side.
            left_ratio:float  = self._compute_visibility_ratio(visibility, LeftLandmark.as_list())
            right_ratio:float = self._compute_visibility_ratio(visibility, RightLandmark.as_list())

            ##############
            ### STEP 1 ### - Not enough signal, return PositionSide.UNKNOWN.
            ##############
            # Check if at least one side meets the minimum required landmark ratio.
            if max(left_ratio, right_ratio) < self.min_required_landmark_ratio:
                return PositionSide.UNKNOWN

            ##############
            ### STEP 2 ### - Front detection (symmetry-based).
            ##############
            # Check for symmetry within the front symmetry threshold.
            if abs(left_ratio - right_ratio) <= self.front_symmetry_threshold:
                return self._validate(PositionSide.FRONT, exercise_type)
            
            ##############
            ### STEP 3 ### - Left side dominance.
            ##############
            # Check if left side is dominant.
            if (left_ratio >= self.dominance_ratio_threshold and left_ratio > right_ratio):
                return self._validate(PositionSide.LEFT, exercise_type)

            ##############
            ### STEP 4 ### - Right side dominance.
            ##############
            if (right_ratio >= self.dominance_ratio_threshold and right_ratio > left_ratio):
                return self._validate(PositionSide.RIGHT, exercise_type)

            ##############
            ### STEP 5 ### - Fallback.
            ##############
            return PositionSide.UNKNOWN

        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.POSITION_SIDE_DETECTION_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception": type(e).__name__,
                    "Reason": str(e)
                }
            )
            return PositionSide.UNKNOWN

    #############################################################################    
    ############################## PRIVATE METHODS ##############################
    #############################################################################

    ################################
    ### COMPUTE VISIBILITY RATIO ###
    ################################
    def _compute_visibility_ratio(self, visibility:np.ndarray, indices:List[int]) -> float:
        """
        ### Brief:
        The `_compute_visibility_ratio` computes the ratio of visible landmarks
        for the specified landmark indices.

        ### Arguments:
        - `visibility` (np.ndarray): Array of landmark visibility scores.
        - `indices` (List[int]): List of landmark indices to consider.

        ### Returns:
        - A `float` representing the ratio of visible landmarks.
        """
        # A landmark is considered visible if its visibility score
        # is greater than or equal to the configured threshold.
        # This command creates a boolean array where each element indicates
        # whether the corresponding landmark is visible.
        visible = visibility[indices] >= self.landmark_visibility_threshold

        Logger.debug(' '.join([f"{i}: {visible[i]}" for i in range(len(visible))]))
        
        # Calculate and return the ratio of visible landmarks.
        return float(np.sum(visible)) / float(len(indices))

    ##################
    ### VALIDATION ###
    ##################
    def _validate(self, side:PositionSide, exercise_type:ExerciseType) -> PositionSide | ErrorCode:
        """
        ### Brief:
        The `_validate` method checks if the detected position side is valid
        for the given exercise type.

        ### Arguments:
        - `side` (PositionSide): Detected position side. 
        - `exercise_type` (ExerciseType): Current exercise type.

        ### Returns:
        - A `PositionSide` if valid.
        - An `ErrorCode` if invalid.
        """
        allowed_sides:list[PositionSide] = PositionSide.allowed_sides(exercise_type)

        # Early exit for UNKNOWN side.
        if side.is_unkwown(): return side

        # Validate against allowed sides for the exercise.
        if side not in allowed_sides: return ErrorCode.WRONG_EXERCISE_POSITION

        # Return valid side.
        return side

    ###############################
    ### RETRIEVE CONFIGURATIONS ###
    ###############################
    def retrieve_configurations(self) -> None:
        """
        ### Brief:
        The `retrieve_configurations` method loads the updated configurations from the
        configuration file.
        """
        self.landmark_visibility_threshold = ConfigLoader.get([
            ConfigParameters.Major.POSITION_SIDE,
            ConfigParameters.Minor.LANDMARK_VISIBILITY_THRESHOLD
        ])

        self.dominance_ratio_threshold = ConfigLoader.get([
            ConfigParameters.Major.POSITION_SIDE,
            ConfigParameters.Minor.DOMINANCE_RATIO_THRESHOLD
        ])

        self.front_symmetry_threshold = ConfigLoader.get([
            ConfigParameters.Major.POSITION_SIDE,
            ConfigParameters.Minor.FRONT_SYMMETRY_THRESHOLD
        ])

        self.min_required_landmark_ratio = ConfigLoader.get([
            ConfigParameters.Major.POSITION_SIDE,
            ConfigParameters.Minor.MIN_REQUIRED_LANDMARK_RATIO
        ])

        Logger.info("Retrieved configurations successfully")