###############################################################
############### BODY TRACK // SERVER // PIPELINE ##############
###############################################################
################### CLASS: PipelineProcessor ##################
###############################################################

###############
### IMPORTS ###
###############
# Python libraries.
import inspect
import numpy as np
from typing import Dict, Any

# Utilities.
from Server.Utilities.SessionIdGenerator      import SessionId
from Server.Utilities.Error.ErrorHandler      import ErrorHandler
from Server.Utilities.Error.ErrorCode         import ErrorCode
from Server.Utilities.Logger                  import Logger

# Pipeline.
from Server.Pipeline.PoseAnalyzer             import PoseAnalyzer
from Server.Pipeline.PoseQualityManager       import PoseQualityManager
from Server.Pipeline.JointAnalyzer            import JointAnalyzer
from Server.Pipeline.PhaseDetector            import PhaseDetector
from Server.Pipeline.HistoryManager           import HistoryManager
from Server.Pipeline.ErrorDetector            import ErrorDetector

# Data.
from Server.Data.Session.SessionData          import SessionData
from Server.Data.Session.FrameData            import FrameData
from Server.Data.Session.AnalyzingState       import AnalyzingState
from Server.Data.Pose.PoseQualityResult       import PoseQualityResult
from Server.Data.Pose.PoseQuality             import PoseQuality
from Server.Data.Pose.PoseLandmarks           import PoseLandmarksArray
from Server.Data.History.HistoryData          import HistoryData
from Server.Data.Response.CalibrationResponse import CalibrationCode
from Server.Data.Response.FeedbackResponse    import FeedbackCode

################################
### PIPELINE PROCESSOR CLASS ###
################################
class PipelineProcessor:
    """
    ### Description:
    The `PipelineProcessor` is the central orchestrator of the `BodyTrack` pipeline.

    ### Responsibilities:
    - Receiving raw frames from the client (`SessionManager` → `PipelineProcessor`).
    - Passing those frames through the analytical stages:
        1. Pose analysis (landmark extraction)
        2. Pose quality evaluation
        3. Joint angle calculation
        4. Phase detection
        5. Error detection

    - Recording results in the `HistoryData` via the `HistoryManager`
    - Returning pipeline results in form of:
        - `CalibrationCode` (during `INIT`/`READY`)
        - `FeedbackCode` (during `ACTIVE`)

    ### Rules:
    - Only `PipelineProcessor` writes to `HistoryData`.
    - All other components (`PhaseDetector`, `ErrorDetector`, etc) may only read from history.
    - The processor does not implement logic itself — it delegates.
    """
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self) -> None:
        """
        ### Brief:
        The `__init__` method initializes the pipeline and instantiates all major pipeline components.

        ### Notes:
        - Configuration values are read from config files during construction.
        - Submodules exposing `retrieve_configurations()` are also initialized.
        """
        # Components.
        self.pose_analyzer        = PoseAnalyzer()
        self.pose_quality_manager = PoseQualityManager()
        self.joint_analyzer       = JointAnalyzer()
        self.history_manager      = HistoryManager()
        self.phase_detector       = PhaseDetector()
        self.error_detector       = ErrorDetector()
        # self.feedback_manager     = FeedbackManager()

        # For easy access to all pipeline modules.
        self.pipeline_modules = {
            self.pose_analyzer,
            self.pose_quality_manager,
            self.joint_analyzer,
            self.history_manager,
            self.phase_detector,
            self.error_detector,
            # self.feedback_manager
        }

        self.retrieve_configurations()
        Logger.info("PipelineProcessor: Initialized successfully")

    ############################################################################
    ############################## PUBLIC METHODS ##############################
    ############################################################################

    #############
    ### START ###
    #############
    def start(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `start` method marks the beginning of an exercise session.

        ### Arguments:
        - `history_data` (HistoryData): The container storing all session-state.
        """
        self.history_manager.mark_exercise_start(history_data)

    ###########
    ### END ###
    ###########
    def end(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `end` method marks the ending of an exercise session.

        ### Arguments:
        - `history_data` (HistoryData): The container storing all session-state.
        """
        self.history_manager.mark_exercise_end(history_data)

    ######################
    ### VALIDATE FRAME ###
    ######################
    def validate_frame(self, session_id:SessionId, frame_id:int, content:np.ndarray) -> FrameData | ErrorCode:
        """
        ### Brief:
        The `validate_frame` method creates an abstract `FrameData` object and validates basic structure.

        ### Arguments:
        - `session_id` (SessionId): The session id as a `SessionId` instance.
        - `frame_id` (int): The frame id.
        - `content` (np.ndarray): The frame content.

        ### Returns:
        - `FrameData` if validation passed.
        - `ErrorCode.FRAME_INITIAL_VALIDATION_FAILED` otherwise.
        """
        frame_data:FrameData = FrameData(session_id=session_id, frame_id=frame_id, content=content)
        try:
            # Performing an initial frame validation before analyzing the pose.
            frame_data.validate()
        except (ValueError, TypeError):
            return ErrorCode.FRAME_INITIAL_VALIDATION_FAILED

        return frame_data

    ###################################
    ### ANALYZE FRAME IN INIT STATE ###
    ###################################
    def analyze_frame_in_init_state(self, session_data:SessionData, frame_data:FrameData) -> CalibrationCode | ErrorCode:
        """
        ### Brief:
        The `analyze_frame_in_init_state` method processes a frame while the session is in `INIT` state.
        Verifies pose landmarks visibility and measures a consecutive streak of `OK`-quality frames before 
        moving to `READY` state.

        ### Arguments:
        - `session_data` (SessionData): The current session instance containing HistoryData.
        - `frame_data` (FrameData): Frame wrapper with timestamp, pixel data and session reference.

        ### Returns:
        - `CalibrationCode.USER_VISIBILITY_IS_UNDER_CHECKING` if the streak has not yet reached the threshold.
        - `CalibrationCode.USER_VISIBILITY_IS_VALID` once minimum `OK` frames are reached and state transitions to `READY`.
        - `ErrorCode` if pose analysis or pose quality evaluation fails.
        """
        ### Analyzing Pose --- using PoseAnalyzer.
        pose_analyzer_result:PoseLandmarksArray | ErrorCode = self.pose_analyzer.analyze_frame(frame_data)
        if self._check_for_error(pose_analyzer_result): return pose_analyzer_result
        
        ### Validating Frame Quality --- using PoseQualityManager.
        pose_quality_result:PoseQualityResult = self.pose_quality_manager.evaluate_landmarks(pose_analyzer_result)
        if self._check_for_error(pose_quality_result): return pose_quality_result

        ### Quality checking.
        quality:PoseQuality = pose_quality_result.quality
        history:HistoryData = session_data.history_data
        # If the frame recieved is not OK - we stay in the INIT state.
        if quality is not PoseQuality.OK:
            # Resetting the counter.
            self.history_manager.reset_consecutive_ok_streak(history)
            error:ErrorCode = PoseQuality.convert_to_error_code(quality)
            ErrorHandler.handle(
                error=error,
                origin=inspect.currentframe(),
                extra_info={ "Frame details", str(frame_data) }
            )
            return error
        # Otherwise, quality is PoseQuality.OK.
        else:
            # Incrementing the counter.
            self.history_manager.increment_consecutive_ok_streak(history)

            # Checking if can move to the next analyzing state.
            if history.get_consecutive_ok_streak() >= self.num_of_min_init_ok_frames:
                session_data.set_analyzing_state(AnalyzingState.READY)
                return CalibrationCode.USER_VISIBILITY_IS_VALID
            else:
                return CalibrationCode.USER_VISIBILITY_IS_UNDER_CHECKING
            
    ####################################
    ### ANALYZE FRAME IN READY STATE ###
    ####################################
    def analyze_frame_in_ready_state(self, session_data:SessionData, frame_data:FrameData) -> CalibrationCode | ErrorCode:
        """
        ### Brief:
        The `analyze_frame_in_ready_state` processes a frame while the session is in `READY` state.
        Ensures that joint angles match the configured initial phase for a consecutive number of
        frames before moving to `ACTIVE`.

        ### Arguments:
        - `session_data` (SessionData): The current session with stored `HistoryData` and state.
        - `frame_data` (FrameData): Validated incoming frame and metadata.

        ### Returns:
        - `CalibrationCode.USER_POSITIONING_IS_UNDER_CHECKING` if the initial phase streak is not yet sufficient.
        - `CalibrationCode.USER_POSITIONING_IS_VALID` once the configured initial phase streak is reached and the state transitions to `ACTIVE`.
        - `ErrorCode` for failures in pose analysis, quality evaluation, or joint calculation.
        """
        ### Analyzing Pose --- using PoseAnalyzer.
        pose_analyzer_result:PoseLandmarksArray | ErrorCode = self.pose_analyzer.analyze_frame(frame_data)
        if self._check_for_error(pose_analyzer_result): return pose_analyzer_result
        
        ### Validating Frame Quality --- using PoseQualityManager.
        pose_quality_result:PoseQualityResult = self.pose_quality_manager.evaluate_landmarks(pose_analyzer_result)
        if self._check_for_error(pose_quality_result): return pose_quality_result

        ### Quality checking.
        quality:PoseQuality = pose_quality_result.quality
        history:HistoryData = session_data.history_data
        # If the frame recieved is not OK.
        if quality is not PoseQuality.OK:
            # Resetting the initial phase counter.
            self.history_manager.reset_consecutive_init_phase_counter(history)
            error:ErrorCode = PoseQuality.convert_to_error_code(quality)
            ErrorHandler.handle(
                error=error,
                origin=inspect.currentframe(),
                extra_info={ "Frame details": str(frame_data) }
            )
            return error
        
        # Else.
        ### Calculating Joints --- using JointAnalyzer.
        joint_analyzer_result:Dict[str, Any] | ErrorCode = self.joint_analyzer.calculate_joints(
            session_data=session_data,
            landmarks=pose_analyzer_result
        )
        if self._check_for_error(joint_analyzer_result): return joint_analyzer_result
        
        ### Checking Inital Phase --- using PhaseDetector.
        phase_detector_result = self.phase_detector.ensure_initial_phase_correct(
            session_data=session_data,
            joints=joint_analyzer_result
        )
        if self._check_for_error(phase_detector_result): return phase_detector_result

        ### Phase is detected - making decision.
        # Checking if the detected phase aligns with the exercise's initial phase.
        elif phase_detector_result is True:
            self.history_manager.increment_consecutive_init_phase_counter(history)
        # If not.
        else:
            self.history_manager.reset_consecutive_init_phase_counter(history)

        # Checking if can move to the next analyzing state.
        if history.get_initial_phase_counter() >= self.num_of_min_correct_phase_frames:
            session_data.set_analyzing_state(AnalyzingState.ACTIVE)
            return CalibrationCode.USER_POSITIONING_IS_VALID
        else:
            return CalibrationCode.USER_POSITIONING_IS_UNDER_CHECKING

    ###################################
    ### ANALYZE FRAME FULL PIPELINE ###
    ###################################
    def analyze_frame_full_pipeline(self, session_data:SessionData, frame_data:FrameData) -> FeedbackCode | ErrorCode:
        """
        ### Brief:
        The `analyze_frame_full_pipeline` method executes the full pipeline in `ACTIVE` state:
        - `PoseAnalyzer`
        - `PoseQualityManager`
        - `JointAnalyzer`
        - `PhaseDetector`
        - `ErrorDetector`
        - `FeedbackFormatter`

        and records all resulting data into `HistoryData`.

        ### Arguments:
        - `session_data` (SessionData): The active session containing exercise metadata and `HistoryData`.
        - `frame_data` (FrameData): The validated frame to process.

        ### Returns:
        - `FeedbackCode` once a feedback formatter is implemented.
        - `ErrorCode` for errors in pose analysis, quality evaluation, joint calculation, phase determination, or error detection.
        """
        ### Analyzing Pose --- using PoseAnalyzer.
        pose_analyzer_result:PoseLandmarksArray | ErrorCode = self.pose_analyzer.analyze_frame(frame_data)
        if self._check_for_error(pose_analyzer_result): return pose_analyzer_result
        
        ### Validating Frame Quality --- using PoseQualityManager.
        pose_quality_result:PoseQualityResult = self.pose_quality_manager.evaluate_landmarks(pose_analyzer_result)
        if self._check_for_error(pose_quality_result): return pose_quality_result

        # The HistoryData of the session.
        history:HistoryData = session_data.history_data

        ##############
        ### CASE 1 ### - The returned results are not OK. This means the frame is invalid (bad frame).
        ##############
        returned_quality:PoseQuality = pose_quality_result.quality
        if returned_quality is not PoseQuality.OK:
            # Logging.
            quality_fail_to_error_code = PoseQuality.convert_to_error_code(returned_quality)
            ErrorHandler.handle(
                error=quality_fail_to_error_code,
                origin=inspect.currentframe(),
                extra_info={ "Frame details": str(frame_data) }
            )
            # Recording invalid frame.
            self.history_manager.record_invalid_frame(
                history_data=history,
                frame_id=frame_data.frame_id,
                invalid_reason=returned_quality
            )
            # Going directly to FeedbackFormatter.
            # feedback:FeedbackCode = self.feedback_formatter.construct_invalid_frame_feedback(...)
            # return feedback

        ##############
        ### CASE 2 ### - The returned results are OK. This means the frame is valid.
        ##############
        ### Calculating Joints --- using JointAnalyzer.
        joint_analyzer_result:Dict[str, Any] | ErrorCode = self.joint_analyzer.calculate_joints(
            session_data=session_data,
            landmarks=pose_analyzer_result
        )
        if self._check_for_error(joint_analyzer_result): return joint_analyzer_result
        
        # Recording valid frame.
        self.history_manager.record_valid_frame(
            history_data=history,
            frame_id=frame_data.frame_id,
            joints=joint_analyzer_result
        )

        # Determining the current phase --- using PhaseDetector.
        phase_detector_result = self.phase_detector.determine_phase(session_data=session_data)
        if self._check_for_error(phase_detector_result): return phase_detector_result
        
        # Recording the phase.
        self.history_manager.record_phase_transition(
            history_data=history,
            new_phase=phase_detector_result,
            frame_id=frame_data.frame_id,
            joints=joint_analyzer_result
        )

        # Detecting errors --- using ErrorDetector.
        error_detector_result = self.error_detector.detect_errors(session_data)
        if self._check_for_error(error_detector_result): return error_detector_result
        
        # If there was a detected error, recording it.
        if error_detector_result is not None:
            
            self.history_manager.add_frame_error(
                history_data=history,
                error_to_add=error_detector_result,
                frame_id=frame_data.frame_id
            )
            self.history_manager.add_error_to_current_rep(
                history_data=history,
                error_to_add=error_detector_result
            )

        # Combining feedback --- using FeedbackFormatter.
        # feedback:FeedbackCode = self.feedback_formatter.construct_invalid_frame_feedback(...)
        # return feedback        

    #############################################################################
    ############################## PRIVATE METHODS ##############################
    #############################################################################

    #######################
    ### CHECK FOR ERROR ###
    #######################
    def _check_for_error(self, result:Any) -> bool:
        """
        ### Brief:
        The `_check_for_error` method determines whether a pipeline result indicates an error.

        ### Arguments:
        - `result` (Any): Output from another pipeline component.

        ### Returns:
        - `True` if the result is `None` or an `ErrorCode`.
        - `False` otherwise.
        """
        if result is None or isinstance(result, ErrorCode): return True
        else:                                               return False

    ###############################
    ### RETRIEVE CONFIGURATIONS ###
    ############################### 
    def retrieve_configurations(self) -> None:
        """
        ### Brief:
        The `retrieve_configurations` method loads the updated configurations from the
        configuration file.
        """
        from Server.Utilities.Config.ConfigLoader import ConfigLoader
        from Server.Utilities.Config.ConfigParameters import ConfigParameters

        # Number of active session initialization OK frames.
        self.num_of_min_init_ok_frames = ConfigLoader.get([
            ConfigParameters.Major.TASKS,
            ConfigParameters.Minor.NUM_OF_MIN_INIT_OK_FRAMES
        ])
        Logger.info(f"SessionManager: Num of min init ok frames: {self.num_of_min_init_ok_frames}")

        # Number of active session initialization correct phase frames.
        self.num_of_min_correct_phase_frames = ConfigLoader.get([
            ConfigParameters.Major.TASKS,
            ConfigParameters.Minor.NUM_OF_MIN_INIT_CORRECT_PHASE
        ])
        Logger.info(f"SessionManager: Num of min init correct phase: {self.num_of_min_correct_phase_frames}")

        # Calling each pipeline module's retrieve_configurations method.
        for pipeline_module in self.pipeline_modules:
            pipeline_module.retrieve_configurations()