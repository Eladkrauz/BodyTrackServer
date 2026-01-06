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
from typing import Dict, Any, cast

# Utilities.
from Utilities.SessionIdGenerator      import SessionId
from Utilities.Error.ErrorHandler      import ErrorHandler
from Utilities.Error.ErrorCode         import ErrorCode
from Utilities.Logger                  import Logger

# Pipeline.
from Pipeline.PoseAnalyzer             import PoseAnalyzer
from Pipeline.PositionSideDetector     import PositionSideDetector
from Pipeline.PoseQualityManager       import PoseQualityManager
from Pipeline.JointAnalyzer            import JointAnalyzer, CalculatedJoints
from Pipeline.PhaseDetector            import PhaseDetector
from Pipeline.HistoryManager           import HistoryManager
from Pipeline.ErrorDetector            import ErrorDetector
from Pipeline.FeedbackFormatter        import FeedbackFormatter

# Data.
from Data.Session.SessionData          import SessionData
from Data.Session.FrameData            import FrameData
from Data.Session.AnalyzingState       import AnalyzingState
from Data.Pose.PoseQuality             import PoseQuality
from Data.Pose.PoseLandmarks           import PoseLandmarksArray
from Data.History.HistoryData          import HistoryData
from Data.Response.CalibrationResponse import CalibrationCode
from Data.Response.FeedbackResponse    import FeedbackCode
from Data.Error.DetectedErrorCode      import DetectedErrorCode
from Data.Phase.PhaseType              import PhaseType
from Data.Pose.PositionSide            import PositionSide

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
        self.pose_analyzer          = PoseAnalyzer()
        self.position_side_detector = PositionSideDetector()
        self.pose_quality_manager   = PoseQualityManager()
        self.joint_analyzer         = JointAnalyzer()
        self.history_manager        = HistoryManager()
        self.phase_detector         = PhaseDetector()
        self.error_detector         = ErrorDetector()
        self.feedback_formatter     = FeedbackFormatter()

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
        Logger.info("Initialized successfully")

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

    #############
    ### PAUSE ###
    #############
    def pause(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `pause` method marks the pausing of an exercise session.

        ### Arguments:
        - `history_data` (HistoryData): The container storing all session-state.
        """
        self.history_manager.pause_session(history_data)

    ##############
    ### RESUME ###
    ##############
    def resume(self, history_data:HistoryData) -> None:
        """
        ### Brief:
        The `resume` method marks the resuming of an exercise session.

        ### Arguments:
        - `history_data` (HistoryData): The container storing all session-state.
        """
        self.history_manager.resume_session(history_data)

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
        
        ### Detecting Position Side --- using PositionSideDetector.
        position_side_result:PositionSide | ErrorCode = self.position_side_detector.detect_and_validate(
            landmarks=pose_analyzer_result,
            exercise_type=session_data.get_exercise_type()
        )
        position_side_error:bool = self._check_for_error(position_side_result)
        if not position_side_error:
            self.history_manager.set_position_side(
                history_data=session_data.get_history(),
                position_side=position_side_result
            )
        
        ### Validating Frame Quality --- using PoseQualityManager.
        pose_quality_result:PoseQuality = self.pose_quality_manager.evaluate_landmarks(
            session_data=session_data,
            landmarks=pose_analyzer_result
        )
        if self._check_for_error(pose_quality_result): return pose_quality_result

        ### Quality checking.
        history:HistoryData = session_data.get_history()
        # If the frame recieved is not OK - we stay in the INIT state.
        if position_side_error or pose_quality_result is not PoseQuality.OK:
            # Resetting the counter.
            self.history_manager.reset_consecutive_ok_streak(history)
            if position_side_error: error:ErrorCode = position_side_result
            else:                   error:ErrorCode = PoseQuality.convert_to_error_code(pose_quality_result)
            ErrorHandler.handle(
                error=error,
                origin=inspect.currentframe(),
                extra_info={ "Frame details": str(frame_data) }
            )
            return error
        # Otherwise, quality is PoseQuality.OK.
        else:
            # Incrementing the counter.
            self.history_manager.increment_consecutive_ok_streak(history)

            # Checking if can move to the next analyzing state.
            if history.get_consecutive_ok_streak() >= self.num_of_min_init_ok_frames:
                session_data.set_analyzing_state(AnalyzingState.READY)
                self.history_manager.set_camera_is_stable(history)
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

        ### Detecting Position Side --- using PositionSideDetector.
        position_side_result:PositionSide | ErrorCode = self.position_side_detector.detect_and_validate(
            landmarks=pose_analyzer_result,
            exercise_type=session_data.get_exercise_type()
        )
        position_side_error:bool = self._check_for_error(position_side_result)
        
        ### Validating Frame Quality --- using PoseQualityManager.
        pose_quality_result:PoseQuality = self.pose_quality_manager.evaluate_landmarks(
            landmarks=pose_analyzer_result,
            session_data=session_data
        )
        if self._check_for_error(pose_quality_result): return pose_quality_result

        ### Quality checking.
        history:HistoryData = session_data.get_history()
        # If the frame recieved is not OK.
        if position_side_error or pose_quality_result is not PoseQuality.OK:
            # Resetting the initial phase counter.
            self.history_manager.reset_consecutive_init_phase_counter(history)
            error:ErrorCode = PoseQuality.convert_to_error_code(pose_quality_result)
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
        phase_detector_result:bool = self.phase_detector.ensure_initial_phase_correct(
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
            self.history_manager.set_initial_phase(history, session_data.get_exercise_type())
            self.history_manager.set_position_side(history, position_side_result)
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
        frame_id:int = frame_data.frame_id
        session_data.init_new_frame_trace(frame_id)

        ### PIPELINE STEP >>> Analyzing Pose --- using PoseAnalyzer.
        pose_analyzer_result:PoseLandmarksArray | ErrorCode = self.pose_analyzer.analyze_frame(frame_data)
        if self._check_for_error(pose_analyzer_result):
            session_data.get_last_frame_trace().add_event(
                stage="PoseAnalyzer",
                success=False,
                result_type="Error Code",
                result={ "Error Code": cast(ErrorCode, pose_analyzer_result).description }
            )
            return pose_analyzer_result
        else:
            session_data.get_last_frame_trace().add_event(
                stage="PoseAnalyzer",
                success=True,
                result_type="PoseLandmarks Array",
                result=None
            )
        
        ### PIPELINE STEP >>> Validating Frame Quality --- using PoseQualityManager.
        pose_quality_result:PoseQuality = self.pose_quality_manager.evaluate_landmarks(
            session_data=session_data,
            landmarks=pose_analyzer_result
        )
        if self._check_for_error(pose_quality_result):
            session_data.get_last_frame_trace().add_event(
                stage="PoseQualityManager",
                success=False,
                result_type="Error Code",
                result={ "Error Code": cast(ErrorCode, pose_quality_result).description }
            )
            return pose_quality_result

        # The HistoryData of the session.
        history:HistoryData = session_data.get_history()

        ##############
        ### CASE 1 ### - The returned results are not OK. This means the frame is invalid (bad frame).
        ##############
        if pose_quality_result is not PoseQuality.OK:
            # Recording invalid frame.
            self.history_manager.record_invalid_frame(
                history_data=history,
                frame_id=frame_data.frame_id,
                invalid_reason=pose_quality_result
            )
            session_data.get_last_frame_trace().add_event(
                stage="HistoryManager",
                success=True,
                result_type="Record Invalid Frame",
                result={ "Invalid Reason": pose_quality_result.name }
            )

            # Check if frame needs to get aborted.
            if self.history_manager.should_abort_session(history):
                session_data.get_last_frame_trace().add_event(
                    stage="HistoryManager",
                    success=True,
                    result_type="Session Should Abort",
                    result=None
                )
                return ErrorCode.SESSION_SHOULD_ABORT
            else:
                return self.feedback_formatter.construct_feedback(session_data)

        ##############
        ### CASE 2 ### - The returned results are OK. This means the frame is valid.
        ##############
        ### PIPELINE STEP >>> Calculating Joints --- using JointAnalyzer.
        joint_analyzer_result:CalculatedJoints | ErrorCode = self.joint_analyzer.calculate_joints(
            session_data=session_data,
            landmarks=pose_analyzer_result
        )
        if self._check_for_error(joint_analyzer_result):
            session_data.get_last_frame_trace().add_event(
                stage="JointAnalyzer",
                success=False,
                result_type="Error Code",
                result={ "Error Code": cast(ErrorCode, joint_analyzer_result).description }
            )
            return joint_analyzer_result
        
        # Recording valid frame.
        self.history_manager.record_valid_frame(
            history_data=history,
            frame_id=frame_data.frame_id,
            landmarks=pose_analyzer_result,
            joints=joint_analyzer_result
        )
        session_data.get_last_frame_trace().add_event(
            stage="HistoryManager",
            success=True,
            result_type="Record Valid Frame",
            result=None
        )

        ### PIPELINE STEP >>> Determining the current phase --- using PhaseDetector.
        phase_detector_result:PhaseType = self.phase_detector.determine_phase(session_data=session_data)
        if self._check_for_error(phase_detector_result):
            session_data.get_last_frame_trace().add_event(
                stage="PhaseDetector",
                success=False,
                result_type="Error Code",
                result={ "Error Code": cast(ErrorCode, phase_detector_result).description }
            )
            return phase_detector_result
        
        # Recording the phase.
        self.history_manager.record_phase_transition(
            history_data=history,
            exercise_type=session_data.get_exercise_type(),
            new_phase=phase_detector_result,
            frame_id=frame_data.frame_id,
            joints=joint_analyzer_result
        )
        session_data.get_last_frame_trace().add_event(
            stage="HistoryManager",
            success=True,
            result_type="Record Phase Transition",
            result={ "New Phase": phase_detector_result.name }
        )

        ### PIPELINE STEP >>> Detecting errors --- using ErrorDetector.
        error_detector_result:DetectedErrorCode = self.error_detector.detect_errors(session_data)
        if self._check_for_error(error_detector_result):
            session_data.get_last_frame_trace().add_event(
                stage="ErrorDetector",
                success=False,
                result_type="Error Code",
                result={ "Error Code": cast(ErrorCode, error_detector_result).description }
            )
            return error_detector_result
        
        # Recording the error (also NO_BIOMECHANICAL_ERROR and NOT_READY_FOR_ANALYSIS are recorded).   
        self.history_manager.add_frame_error(
            history_data=history,
            error_to_add=error_detector_result,
            frame_id=frame_data.frame_id
        )
        
        session_data.get_last_frame_trace().add_event(
            stage="HistoryManager",
            success=True,
            result_type="Add Frame Error",
            result={ "Detected Error": error_detector_result.name }
        )
        session_data.get_last_frame_trace().add_event(
            stage="ErrorStreaks",
            success=True,
            result_type="Update Error Streaks",
            result=history.get_error_streaks()
        )

        if not error_detector_result in (
            DetectedErrorCode.NO_BIOMECHANICAL_ERROR,
            DetectedErrorCode.NOT_READY_FOR_ANALYSIS
        ):
            self.history_manager.add_error_to_current_rep(
                history_data=history,
                error_to_add=error_detector_result
            )
            session_data.get_last_frame_trace().add_event(
                stage="HistoryManager",
                success=True,
                result_type="Add Error To Current Rep",
                result={ "Detected Error": error_detector_result.name }
            )

        ### PIPELINE STEP >>> Combining feedback --- using FeedbackFormatter.
        feedback_result = self.feedback_formatter.construct_feedback(session_data)
        if self._check_for_error(feedback_result):
            session_data.get_last_frame_trace().add_event(
                stage="FeedbackFormatter",
                success=False,
                result_type="Error Code",
                result={ "Error Code": cast(ErrorCode, feedback_result).description }
            )
            return feedback_result

        # If the feedback is SILENT or VALID - increment frames since last feedback.
        if feedback_result in (FeedbackCode.SILENT, FeedbackCode.VALID):
            self.history_manager.increment_frames_since_last_feedback(history)
            session_data.get_last_frame_trace().add_event(
                stage="HistoryManager",
                success=True,
                result_type="Increment Frames Since Last Feedback",
                result=None
            )
        # Else - reset the counter and record the feedback to the current rep.
        else:
            self.history_manager.reset_frames_since_last_feedback(history)
            self.history_manager.record_feedback_notified(history, feedback_result)
            session_data.get_last_frame_trace().add_event(
                stage="HistoryManager",
                success=True,
                result_type="Record Feedback Notified",
                result={ "Feedback Code": feedback_result.name }
            )

        return feedback_result

    #####################################################################
    ############################## HELPERS ##############################
    #####################################################################

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
        from Utilities.Config.ConfigLoader import ConfigLoader
        from Utilities.Config.ConfigParameters import ConfigParameters

        # Number of active session initialization OK frames.
        self.num_of_min_init_ok_frames = ConfigLoader.get([
            ConfigParameters.Major.SESSION,
            ConfigParameters.Minor.NUM_OF_MIN_INIT_OK_FRAMES
        ])
        Logger.info(f"Num of min init ok frames: {self.num_of_min_init_ok_frames}")

        # Number of active session initialization correct phase frames.
        self.num_of_min_correct_phase_frames = ConfigLoader.get([
            ConfigParameters.Major.SESSION,
            ConfigParameters.Minor.NUM_OF_MIN_INIT_CORRECT_PHASE
        ])
        Logger.info(f"Num of min init correct phase: {self.num_of_min_correct_phase_frames}")

        # Calling each pipeline module's retrieve_configurations method.
        for pipeline_module in self.pipeline_modules:
            pipeline_module.retrieve_configurations()