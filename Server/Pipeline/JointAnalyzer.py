############################################################
############# BODY TRACK // SERVER // PIPELINE #############
############################################################
################## CLASS: JointAnalyzer ####################
############################################################

###############
### IMPORTS ###
###############
# Python libraries.
import math, inspect
import numpy as np
from typing import Dict, Any

from Server.Utilities.Logger             import Logger
from Server.Utilities.Error.ErrorHandler import ErrorHandler
from Server.Utilities.Error.ErrorCode    import ErrorCode
from Server.Data.Pose.PoseLandmarks      import PoseLandmarksArray
from Server.Data.Session.SessionData     import SessionData
from Server.Data.Joints.JointAngle       import JointAngle, Joint
from Server.Data.Pose.PositionSide       import PositionSide
from Server.Data.History.HistoryData     import HistoryData
from Server.Data.Session.AnalyzingState  import AnalyzingState

###############################
### CALCULATED JOINTS ALIAS ###
###############################
CalculatedJoints = Dict[str, float]

############################
### JOINT ANALYZER CLASS ###
############################
class JointAnalyzer:
    """
    ### Description:
    The `JointAnalyzer` class calculates joint angles based on MediaPipe Pose landmarks.
    
    ### Notes:
    - Only calculates the angles needed for the selected exercise (not all possible joints).
    - Uses vector math (dot product, arccos) to compute angles in degrees.
    - Can be extended with new exercises and their required joints.
    """
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self):
        """
        ### Brief:
        The `__init__` method initializes the `JointAnalyzer` instance.
        """
        # Get configurations.
        self.retrieve_configurations()

        # Initialized.
        Logger.info("Initialized successfully.")

    ############################################################################
    ############################## PUBLIC METHODS ##############################
    ############################################################################

    ########################
    ### CALCULATE JOINTS ###
    ########################
    def calculate_joints(self, session_data:SessionData, landmarks:PoseLandmarksArray) -> CalculatedJoints | ErrorCode:
        """
        ### Brief:
        The `calculate_joints` method calculates the relevant joint angles for the given exercise.

        ### Arguments:
        - `session_data` (SessionData): The session data of the checked session.
        - `landmarks` (PoseLandmarksArray): Array of pose landmarks from PoseAnalyzer.

        ### Returns:
        - `CalculatedJoints`, which is a `dict[str, float]` of calculated joint angles.
        - An empty `dict` if the last frame is not actually valid.
        - `ErrorCode`: If calculation fails due to missing/invalid landmarks.
        """
        history:HistoryData = session_data.get_history()
        # Ensure session state is stable.
        if not history.is_state_ok():
            ErrorHandler.handle(
                error=ErrorCode.CANT_CALCULATE_JOINTS_OF_UNSTALBE_FRAME,
                origin=inspect.currentframe()
            )
            return {}
        
        # Ensure there is valid frame data to analyze.
        if session_data.analyzing_state is AnalyzingState.ACTIVE and \
            not history.is_last_frame_actually_valid():
            return {}
        
        exercise_type       = session_data.get_exercise_type()
        extended_evaluation = session_data.get_extended_evaluation()
        # Validate landmarks.
        if landmarks is None or not isinstance(landmarks, np.ndarray):
            ErrorHandler.handle(
                error=ErrorCode.JOINT_CALCULATION_ERROR,
                origin=inspect.currentframe(),
                extra_info={"Reason": "Invalid landmarks array."}
            )
            return ErrorCode.JOINT_CALCULATION_ERROR

        # Handle each exercise.
        try:        
            # Based on position side and extended_evaluation parameter, decide which joints to calculate.
            position_side:PositionSide = session_data.get_history().get_position_side()
            exercise_joints:list[Joint] = JointAngle.get_all_joints(
                cls_name=JointAngle.exercise_type_to_joint_type(exercise_type),
                position_side=position_side,
                extended_evaluation=extended_evaluation
            )
            # If no joints are defined for the given exercise type, in this position side.
            if exercise_joints is None or len(exercise_joints) == 0:
                ErrorHandler.handle(
                    error=ErrorCode.JOINT_CALCULATION_ERROR,
                    origin=inspect.currentframe(),
                    extra_info={"Reason": "No joints defined for the given exercise type."}
                )
                return ErrorCode.JOINT_CALCULATION_ERROR

            results:CalculatedJoints = {}

            count_valid_core_joints = 0
            # Iterate over required joints to be calculated.
            for joint in exercise_joints:
                if len(joint.landmarks) == JointAngle.TWO_POINT_JOINT:
                    left_point, right_point = joint.landmarks
                    calculated_angle = self._line_against_horizontal_angle(
                        left_point=landmarks[left_point],
                        right_point=landmarks[right_point]
                    )
                    Logger.debug(f"Calculated angle for joint {joint.name}: {calculated_angle}, with landmarks {left_point} ({landmarks[left_point]}), {right_point} ({landmarks[right_point]})")
                elif len(joint.landmarks) == JointAngle.THREE_POINT_JOINT:
                    landmark_1, landmark_2, landmark_3 = joint.landmarks
                    calculated_angle = self._calculate_angle(
                        dimension=joint.dimension,
                        landmark_1=landmarks[landmark_1],
                        landmark_2=landmarks[landmark_2],
                        landmark_3=landmarks[landmark_3]
                    )
                    Logger.debug(f"Calculated angle for joint {joint.name}: {calculated_angle}, with landmarks {landmark_1} ({landmarks[landmark_1]}), {landmark_2} ({landmarks[landmark_2]}), {landmark_3} ({landmarks[landmark_3]})")
                else:
                    ErrorHandler.handle(
                        error=ErrorCode.DIMENSION_OF_ANGLE_IS_INVALID,
                        origin=inspect.currentframe(),
                        extra_info={
                            "The dimension is": len(joint.landmarks),
                            "The required dimension is": "2 or 3"
                        }
                    )
                    calculated_angle = None

                # Counting valid core joints.
                if calculated_angle is not None:
                    count_valid_core_joints += 1
                
                # Adding the angle to the results dictionary.
                results[joint.name] = calculated_angle

            # Checking the percentage of valid core joints versus the predefined parameter.
            if (count_valid_core_joints / len(exercise_joints)) < self.min_valid_joint_ratio:
                ErrorHandler.handle(
                    error=ErrorCode.TOO_MANY_INVALID_ANGLES,
                    origin=inspect.currentframe(),
                    extra_info={
                        "Valid angles percentage": (count_valid_core_joints / len(exercise_joints)),
                        "Minimum required to proceed with pipeline": self.min_valid_joint_ratio
                    }
                )
                return ErrorCode.TOO_MANY_INVALID_ANGLES
            else:
                return results
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.JOINT_CALCULATION_ERROR,
                origin=inspect.currentframe(),
                extra_info={ "Exception": str(e) }
            )
            return ErrorCode.JOINT_CALCULATION_ERROR
        
    #############################################################################
    ############################## PRIVATE METHODS ##############################
    #############################################################################

    ########################
    ### VALIDATE NDARRAY ###
    ########################
    @staticmethod
    def _validate_ndarray(array:np.ndarray) -> tuple[bool, str]:
        """
        ### Brief:
        The `_validate_ndarray` static method gets an array and validates it.
        - Checks if the array is `None`.
        - Checks if the array is not an instance of `numpy.ndarray`.
        - Checks if the array is not in the correct shape (which is `3`).

        ### Arguments:
        `array` (np.ndarray): The array to be validated.

        ### Returns:
        `True` if the array is valid, `False` and the reason - if not.
        """
        # If the array is None.
        if array is None: return False, "The provided array is None"
        
        # If the array is not an numpy.ndarray.
        if not isinstance(array, np.ndarray): return False, "The provided array is not an instance of np.ndarray"
        
        # If the array is not in the correct shape.
        if array.size < 3: return False, "The size of the provided array is smaller then 3"
        
        # If all passes.
        return True, ""

    ##############
    ### VECTOR ###
    ##############
    @classmethod
    def _vector(cls, point_1:np.ndarray, point_2:np.ndarray) -> np.ndarray | None:
        """
        ### Brief:
        The `_vector` class method returns a vector from point point1 to point 2.
        
        ### Arguments:
        - `point_1` (np.ndarray): The first point.
        - `point_2` (np.ndarray): The second point.

        ### Returns:
        - An `np.ndarray` calculated vector based on the two given points.
        - `None` if failed to calculate the vector.
        """
        # Checking if the first point is valid.
        is_valid, reason_if_not = cls._validate_ndarray(point_1)
        if not is_valid:
            ErrorHandler.handle(
                error=ErrorCode.VECTOR_VALIDATION_FAILED,
                origin=inspect.currentframe(),
                extra_info={
                    "Reason": reason_if_not,
                    "The problem is with": "point_1"
                }
            )
            return None
        # Checking if the second point is valid.
        is_valid, reason_if_not = cls._validate_ndarray(point_2)
        if not is_valid:
            ErrorHandler.handle(
                error=ErrorCode.VECTOR_VALIDATION_FAILED,
                origin=inspect.currentframe(),
                extra_info={
                    "Reason": reason_if_not,
                    "The problem is with": "point_2"
                }
            )
            return None

        # Trying to calculate the vector between the two points.
        try:
            return np.array([point_2[0] - point_1[0], point_2[1] - point_1[1], point_2[2] - point_1[2]])
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.VECTOR_VALIDATION_FAILED,
                origin=inspect.currentframe(),
                extra_info={
                    "An exception occured": type(e),
                    "Reason": str(e)
                }
            )
            return None

    #############
    ### ANGLE ###
    #############
    @classmethod
    def _angle(cls, vector_1:np.ndarray, vector_2:np.ndarray) -> float | None:
        """
        ### Brief:
        The `_angle` class method calculates an angle between two provided vectors.
        The calculation of the angle is in degrees using dot product.

        ### Arguments:
        - `vector_1` (np.ndarray): The first vector.
        - `vector_2` (np.ndarray): The second vector.

        ### Returns:
        - The angle between the vectors, as a `float`.
        - If the inputs are invalid or the calculation is not possible, returns `None`.
        """
        # Checking if the first vector is valid.
        is_valid, reason_if_not = cls._validate_ndarray(vector_1)
        if not is_valid:
            ErrorHandler.handle(
                error=ErrorCode.ANGLE_VALIDATION_FAILED,
                origin=inspect.currentframe(),
                extra_info={
                    "Reason": reason_if_not,
                    "The problem is with": "vector_1"
                }
            )
            return None
        # Checking if the second vector is valid.
        is_valid, reason_if_not = cls._validate_ndarray(vector_2)
        if not is_valid:
            ErrorHandler.handle(
                error=ErrorCode.ANGLE_VALIDATION_FAILED,
                origin=inspect.currentframe(),
                extra_info={
                    "Reason": reason_if_not,
                    "The problem is with": "vector_2"
                }
            )
            return None

        # Trying to calculate the angle.
        try:
            # Compute dot product and magnitudes
            dot = float(np.dot(vector_1, vector_2))
            normalized_vector_1 = float(np.linalg.norm(vector_1))
            normalized_vector_2 = float(np.linalg.norm(vector_2))

            # Invalid vector/s (zero length).
            if normalized_vector_1 == 0.0 or normalized_vector_2 == 0.0:
                ErrorHandler.handle(
                    error=ErrorCode.ANGLE_VALIDATION_FAILED,
                    origin=inspect.currentframe(),
                    extra_info={ "Reason": "One or more of the provided vectors are zero length." }
                )
                return None

            # Clamp the cosine value to [-1, 1] to avoid floating point errors.
            cos_theta = np.clip(dot / (normalized_vector_1 * normalized_vector_2), -1.0, 1.0)

            return float(np.degrees(np.arccos(cos_theta)))
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.ANGLE_VALIDATION_FAILED,
                origin=inspect.currentframe(),
                extra_info={
                    "An exception occured": type(e),
                    "Reason": str(e)
                }
            )
            return None

    #######################
    ### CLACULATE ANGLE ###
    #######################
    def _calculate_angle(
            self,
            dimension:bool,
            landmark_1:np.ndarray,
            landmark_2:np.ndarray,
            landmark_3:np.ndarray
        ) -> float | ErrorCode:
        """
        ### Brief:
        The `_calculate_angle` method calculates the angle at landmark_2 given three landmarks.

        ### Arguments:
        - `dimension` (bool): The dimension to calculate the angle in (2D - `False` or 3D - `True`).
        - `landmark_1` (np.ndarray): The first landmark.
        - `landmark_2` (np.ndarray): The second landmark.
        - `landmark_3` (np.ndarray): The third landmark.

        ### Returns:
        A `float` as the angle calculated, or `ErrorCode` if the calculation failed.

        ### Reasons for failure:
        - Landmark's visibility is not within the predefined threshold.
        - Vector creation failed cause one/more of the points validation failed.
        - Angle calculation failed cause one/more of the vectors validation failed.
        """
        if dimension is True:
            Logger.debug("Calculating angle in 3D space.")
            # Calculating the first vector.
            vector_1 = self._vector(landmark_2, landmark_1)
            if vector_1 is None:
                ErrorHandler.handle(
                    error=ErrorCode.ANGLE_CALCULATION_FAILED,
                    origin=inspect.currentframe(),
                    extra_info={ "Reason": "Failed to calculate a vector between landmark 1 and 2." }
                )
                return ErrorCode.ANGLE_CALCULATION_FAILED
            
            # Calculating the second vector.
            vector_2 = self._vector(landmark_2, landmark_3)
            if vector_2 is None:
                ErrorHandler.handle(
                    error=ErrorCode.ANGLE_CALCULATION_FAILED,
                    origin=inspect.currentframe(),
                    extra_info={ "Reason": "Failed to calculate a vector between landmark 2 and 3." }
                )
                return ErrorCode.ANGLE_CALCULATION_FAILED
            
            # Calculating the angle between the two vectors.
            angle = self._angle(vector_1, vector_2)
            if angle is None:
                ErrorHandler.handle(
                    error=ErrorCode.ANGLE_CALCULATION_FAILED,
                    origin=inspect.currentframe(),
                    extra_info={ "Reason": "Failed to calculate an angle between the two (correctly) calculated vectors." }
                )
                return ErrorCode.ANGLE_CALCULATION_FAILED
            
        else:
            Logger.debug("Calculating angle in 2D space.")
            try:
                # Extracting XY coordinates of the landmarks.
                p1 = landmark_1[:2]
                p2 = landmark_2[:2]
                p3 = landmark_3[:2]

                # Building vectors in 2D.
                v1 = p1 - p2
                v2 = p3 - p2

                # Calculating the angle using the dot product formula.
                dot = float(np.dot(v1, v2))
                norm = float(np.linalg.norm(v1) * np.linalg.norm(v2))

                if norm == 0.0:
                    return ErrorCode.ANGLE_CALCULATION_FAILED

                cos_theta = np.clip(dot / norm, -1.0, 1.0)
                angle = float(np.degrees(np.arccos(cos_theta)))
            except Exception:
                return ErrorCode.ANGLE_CALCULATION_FAILED
            
        # All calculations went correctly - returning the calculated angle.
        return angle
    
    #####################################
    ### LINE AGAINST HORIZONTAL ANGLE ###
    #####################################
    def _line_against_horizontal_angle(self, left_point:np.ndarray, right_point:np.ndarray) -> float | ErrorCode:
        """
        ### Brief:
        The `_line_against_horizontal_angle` mathod calculates the angle (in degrees) between a line segment
        defined by two landmarks (left_point - right_point) and the horizontal axis of the image.

        ### Arguments:
        - `left_point` (np.ndarray): First landmark.
        - `right_point` (np.ndarray): Second landmark.

        ### Returns:
        - `float`: Angle in degrees. 0° = perfectly horizontal, increases as the line tilts towards vertical.
        - `ErrorCode`: If validation fails or calculation is impossible.

        ### Notes:
        - Works in 2D (x, y) ignoring depth (z).
        - Useful for biomechanical checks like pelvic tilt (hip line) or shoulder tilt.
        """
        # Validate inputs.
        is_valid, reason_if_not = self._validate_ndarray(left_point)
        if not is_valid:
            ErrorHandler.handle(
                error=ErrorCode.ANGLE_CALCULATION_FAILED,
                origin=inspect.currentframe(),
                extra_info={"Reason": reason_if_not, "At": "left_point"}
            )
            return ErrorCode.ANGLE_CALCULATION_FAILED

        is_valid, reason_if_not = self._validate_ndarray(right_point)
        if not is_valid:
            ErrorHandler.handle(
                error=ErrorCode.ANGLE_CALCULATION_FAILED,
                origin=inspect.currentframe(),
                extra_info={"Reason": reason_if_not, "At": "right_point"}
            )
            return ErrorCode.ANGLE_CALCULATION_FAILED

        try:
            dx = float(right_point[0] - left_point[0])
            dy = float(right_point[1] - left_point[1])

            # Check for degenerate line.
            if dx == 0.0 and dy == 0.0:
                ErrorHandler.handle(
                    error=ErrorCode.ANGLE_CALCULATION_FAILED,
                    origin=inspect.currentframe(),
                    extra_info={"Reason": "Both points are identical → no line"}
                )
                return ErrorCode.ANGLE_CALCULATION_FAILED

            # atan2 gives the angle to the x-axis; we normalize to [0, 90].
            angle = math.degrees(math.atan2(abs(dy), abs(dx)))
            return float(angle)

        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.ANGLE_CALCULATION_FAILED,
                origin=inspect.currentframe(),
                extra_info={"Exception": type(e).__name__, "Reason": str(e)}
            )
            return ErrorCode.ANGLE_CALCULATION_FAILED
        
    ############################################################################
    ############################## CONFIGURATIONS ##############################
    ############################################################################
        
    ###############################
    ### RETRIEVE CONFIGURATIONS ###
    ############################### 
    def retrieve_configurations(self) -> None:
        """
        ### Brief:
        The `retrieve_configurations` method gets the updated configurations from the
        configuration file.
        """
        from Server.Utilities.Config.ConfigLoader import ConfigLoader
        from Server.Utilities.Config.ConfigParameters import ConfigParameters

        self.visibility_threshold = ConfigLoader.get([
            ConfigParameters.Major.JOINTS,
            ConfigParameters.Minor.VISIBILITY_THRESHOLD
        ])
        self.min_valid_joint_ratio = ConfigLoader.get([
            ConfigParameters.Major.JOINTS,
            ConfigParameters.Minor.MIN_VALID_JOINT_RATIO
        ])