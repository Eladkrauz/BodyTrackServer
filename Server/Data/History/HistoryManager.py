############################################################
######### BODY TRACK // SERVER // DATA // HISTORY ##########
############################################################
################## CLASS: HistoryManager ###################
############################################################

###############
### IMPORTS ###
###############
import time, inspect
from typing import Dict, Any, List

from Server.Utilities.Logger import Logger
from Server.Utilities.Error.ErrorHandler import ErrorHandler
from Server.Utilities.Error.ErrorCode import ErrorCode
from Server.Data.Session.ExerciseType import ExerciseType
from Server.Data.Joints.JointAngle import JointAngle
from Server.Data.Phase.PhaseType import PhaseType

#############################
### HISTORY MANAGER CLASS ###
#############################
class HistoryManager:
    """
    ### Description:
    The `HistoryManager` class maintains and updates the analysis history
    for each active session inside the `SessionManager`.

    It acts as a central data structure that holds all temporal, statistical,
    and contextual information necessary for advanced analysis across frames —
    including phase detection, repetition counting, feedback evaluation, and 
    long-term session metrics.

    ### Core Responsibilities:
    1. Initialize analysis data when a session begins.
    2. Store & update the latest frame-level analysis results.
    3. Maintain rolling history windows (for smoothing, velocity, visibility).
    4. Provide consistent state to the `PhaseDetector` and later `FeedbackManager`.
    5. Ensure thread safety and data consistency when accessed concurrently
       by multiple frames of the same session.

    ### Pipeline Context:
    The `HistoryManager` is used within `SessionManager.analyze_frame()`:
    1. PoseAnalyzer → returns landmarks  
    2. JointAnalyzer → returns joint angles  
    3. HistoryManager.update() → stores new data & rolling windows  
    4. PhaseDetector → reads from updated history to detect phase  
    5. FeedbackManager → uses phase + angles + history for feedback

    ### Life Cycle:
    - Created once per session when analysis starts.
    - Persisted in memory via `SessionData.analysis_data`.
    - Updated per frame through `HistoryManager.update()` calls.
    - Reset or saved to DB upon session termination.
    """
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self, exercise_type:ExerciseType):
        """
        ### Brief:
        The `__init__` method initializes a new `HistoryManager` for a given exercise type.

        ### Arguments:
        - `exercise_type` (ExerciseType): The exercise assigned to this session.

        ### Notes:
        - Each session keeps one instance of `HistoryManager` inside its `analysis_data`.
        - Exercise-specific angle keys are derived directly from `JointAnalyzer.JointAngle`.
        """
        try:
            self.exercise_type = exercise_type
            self.analysis_data: Dict[str, Any] = {}
            self._init_structure()
            Logger.info(f"HistoryManager initialized for {exercise_type.name}.")
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_INIT_ERROR,
                origin=inspect.currentframe(),
                extra_info={ "Exception": str(e) }
            )

    #######################
    ### INIT STRUCTURE ####
    #######################
    def _init_structure(self) -> None:
        """
        ### Brief:
        The `_init_structure` method initializes the `analysis_data` dictionary — a structured container
        that holds all contextual, temporal, and biomechanical data used for:
        - Phase detection
        - Error detection
        - Feedback generation and stability assessment

        ### Notes:
        - This data represents the short-term analytical memory of a live session.
        - It is updated once per frame by `HistoryManager.update()`.
        - It is continuously read by `PhaseDetector` and `FeedbackManager`.
        """
        self.analysis_data = {

            # ================================================================
            # ====================== SESSION CONTEXT =========================
            # ================================================================

            # The type of exercise being analyzed (e.g., SQUAT, BICEPS_CURL, LATERAL_RAISE).
            # -------------------------------------------------------------------------
            # What it stores:
            #   - An enum value from `ExerciseType` representing the current exercise.
            # Why we need it:
            #   - Determines which joint angles to compute and which phase model to use.
            # Who updates it:
            #   - Set once by `SessionManager` when the session starts.
            # Who reads it:
            #   - `PhaseDetector` → to select the correct state machine (`PhaseType`).
            #   - `FeedbackManager` → to customize biomechanical messages per exercise.
            "exercise_type": self.exercise_type,

            # Sequential frame counter that increments each time a new frame is processed.
            # -------------------------------------------------------------------------
            # What it stores:
            #   - Integer index of the current frame since session start.
            # Why we need it:
            #   - Used to calculate motion timing and identify dropped or skipped frames.
            # Who updates it:
            #   - Incremented in `HistoryManager.update()` each frame.
            # Who reads it:
            #   - `PhaseDetector` for temporal logic.
            #   - Logging/analytics for performance metrics.
            "frame_index": 0,

            # ================================================================
            # ====================== PHASE STATE MACHINE =====================
            # ================================================================

            # Current detected movement phase (e.g., DOWN, UP, HOLD, NONE).
            # -------------------------------------------------------------------------
            # What it stores:
            #   - Enum from `PhaseType.<Exercise>` corresponding to the active motion phase.
            # Why we need it:
            #   - Defines the user’s current biomechanical state.
            # Who updates it:
            #   - Set initially to `PhaseType.<Exercise>.NONE`.
            #   - Updated by `PhaseDetector` via `HistoryManager.set_phase()`.
            # Who reads it:
            #   - `FeedbackManager` for context-based cues.
            #   - `SessionManager` for session summaries and logging.
            "last_phase": PhaseType.get_phase_enum(self.exercise_type),

            # Previous motion phase detected in the last iteration.
            # -------------------------------------------------------------------------
            # What it stores:
            #   - The prior phase value (Enum) before the current one.
            # Why we need it:
            #   - Used for detecting transitions like DOWN→UP or LIFTING→LOWERING.
            # Who updates it:
            #   - `PhaseDetector` when setting a new phase.
            # Who reads it:
            #   - `PhaseDetector` → to detect repetition boundaries.
            #   - `FeedbackManager` → to contextualize feedback based on phase transitions.
            "prev_phase": PhaseType.get_phase_enum(self.exercise_type),

            # Timestamp marking when the current phase began.
            # -------------------------------------------------------------------------
            # What it stores:
            #   - float (seconds since epoch) recorded using `time.time()`.
            # Why we need it:
            #   - Enables measuring how long a phase has lasted (for HOLD checks or timing).
            # Who updates it:
            #   - Updated in `HistoryManager.set_phase()` whenever a new phase starts.
            # Who reads it:
            #   - `PhaseDetector` for stability/time-based thresholds.
            #   - `FeedbackManager` for duration-based feedback (“Hold position for 1s”).
            "phase_enter_time": 0.0,

            # Total count of completed repetitions within the session.
            # -------------------------------------------------------------------------
            # What it stores:
            #   - Integer count of full motion cycles (e.g., DOWN→UP = 1 rep).
            # Why we need it:
            #   - Tracks exercise progress and performance.
            # Who updates it:
            #   - `PhaseDetector` after detecting a full phase sequence.
            # Who reads it:
            #   - `FeedbackManager` → motivational output.
            #   - `SessionManager` → sends progress updates to the client.
            "repetition_count": 0,

            # ================================================================
            # ====================== MOTION TRACKING =========================
            # ================================================================

            # Rolling buffer of the most recent N frames' calculated joint angles.
            # -------------------------------------------------------------------------
            # What it stores:
            #   - List of dictionaries: [{joint_name: angle_in_degrees}, ...]
            # Why we need it:
            #   - Enables trend detection, velocity calculation, and phase estimation.
            # Who updates it:
            #   - `HistoryManager.update()` after each frame.
            # Who reads it:
            #   - `PhaseDetector` → motion trend and phase detection.
            #   - `ErrorDetector` (future) → to analyze motion smoothness.
            "angles_window": [],

            # Current angular velocities per joint.
            # -------------------------------------------------------------------------
            # ✅ What it stores:
            #   - Dict: {joint_name: angular_velocity_in_deg_per_sec}.
            # ✅ Why we need it:
            #   - Used to detect direction (ascending vs descending).
            # ✅ Who updates it:
            #   - Computed in `HistoryManager.update()` based on Δangle/Δtime.
            # ✅ Who reads it:
            #   - `PhaseDetector` for determining movement direction.
            "angle_velocities": {},

            # Min and max angles observed during the current repetition.
            # -------------------------------------------------------------------------
            # ✅ What it stores:
            #   - Dict: {joint_name: {"min": value, "max": value}}.
            # ✅ Why we need it:
            #   - Detects full range of motion (used for rep validation).
            # ✅ Who updates it:
            #   - `PhaseDetector` or `JointAnalyzer` during ongoing movement.
            # ✅ Who reads it:
            #   - `PhaseDetector` to confirm rep completion.
            #   - `FeedbackManager` to warn about shallow motion.
            "current_rep_extrema": {},

            # Rolling buffer of recent visibility averages from MediaPipe Pose.
            # -------------------------------------------------------------------------
            # ✅ What it stores:
            #   - List of float values [0.0–1.0] for recent frames’ visibility.
            # ✅ Why we need it:
            #   - Ensures we rely only on frames with sufficient pose confidence.
            # ✅ Who updates it:
            #   - `HistoryManager.update()` each frame.
            # ✅ Who reads it:
            #   - `PhaseDetector` → may pause updates if visibility too low.
            #   - `FeedbackManager` → “Move closer to camera” cues.
            "visibility_window": [],

            # ================================================================
            # ===================== POSE QUALITY TRACKING ====================
            # ================================================================

            # List of quality issues detected in the latest frame.
            # -------------------------------------------------------------------------
            # ✅ What it stores:
            #   - Example: ["LOW_VISIBILITY", "PARTIAL_BODY"]
            # ✅ Why we need it:
            #   - To identify invalid frames or unreliable data.
            # ✅ Who updates it:
            #   - `PoseAnalyzer` after evaluating pose with `PoseQualityManager`.
            # ✅ Who reads it:
            #   - `PhaseDetector` → to skip invalid frames.
            #   - `FeedbackManager` → to generate visual/audio cues for user correction.
            "last_quality_flags": [],

            # Counter for how many consecutive frames each issue has appeared.
            # -------------------------------------------------------------------------
            # ✅ What it stores:
            #   - Dict like {"LEAN_FORWARD": 4, "KNEE_VALGUS": 2}.
            # ✅ Why we need it:
            #   - Avoids false positives from single-frame noise.
            # ✅ Who updates it:
            #   - `ErrorDetector` (future component).
            # ✅ Who reads it:
            #   - `FeedbackManager` for persistent error feedback logic.
            "issue_counters": {},

            # Tracks consecutive pose-quality issues like low visibility or missing landmarks.
            # -------------------------------------------------------------------------
            # ✅ What it stores:
            #   - Dict of quality issue counters.
            # ✅ Why we need it:
            #   - Prevents repeated identical warnings every frame.
            # ✅ Who updates it:
            #   - `PoseQualityManager`.
            # ✅ Who reads it:
            #   - `FeedbackManager`.
            "consecutive_quality_issues": {},

            # ================================================================
            # ====================== FEEDBACK CONTROL ========================
            # ================================================================

            # Indicates whether current phase detection is stable enough for feedback.
            # -------------------------------------------------------------------------
            # ✅ What it stores:
            #   - Boolean flag.
            # ✅ Why we need it:
            #   - Avoids sending feedback mid-transition or under noisy conditions.
            # ✅ Who updates it:
            #   - `PhaseDetector` after evaluating stability.
            # ✅ Who reads it:
            #   - `FeedbackManager` to decide whether to issue new cues.
            "phase_valid": True,

            # Stores feedback codes already sent in the previous frame.
            # -------------------------------------------------------------------------
            # ✅ What it stores:
            #   - List of identifiers for feedback messages.
            # ✅ Why we need it:
            #   - Prevents duplicate text or voice prompts.
            # ✅ Who updates it:
            #   - `FeedbackManager` after feedback is dispatched.
            # ✅ Who reads it:
            #   - `FeedbackManager` before sending new feedback.
            "last_feedback_codes": [],

            # ================================================================
            # =================== EXERCISE CONFIGURATION ======================
            # ================================================================

            # List of relevant joint angle names for this exercise.
            # -------------------------------------------------------------------------
            # ✅ What it stores:
            #   - List of strings, e.g., ["left_knee_angle", "right_knee_angle", ...]
            # ✅ Why we need it:
            #   - Defines which angles are tracked and logged.
            # ✅ Who updates it:
            #   - Determined by `_resolve_angle_keys()` at initialization.
            # ✅ Who reads it:
            #   - `PhaseDetector` and `FeedbackManager` to know which angles to analyze.
            "keys_used": self._resolve_angle_keys(),

            # Maximum number of frames to retain in rolling windows.
            # -------------------------------------------------------------------------
            # ✅ What it stores:
            #   - Integer defining buffer size for angles and visibility.
            # ✅ Why we need it:
            #   - Prevents memory overflow and controls smoothing window size.
            # ✅ Who updates it:
            #   - Set once during initialization.
            # ✅ Who reads it:
            #   - `HistoryManager.update()` to trim lists.
            "angles_window_size": 20
        }


    ##########################
    ### RESOLVE ANGLE KEYS ###
    ##########################
    def _resolve_angle_keys(self) -> List[str]:
        """
        ### Brief:
        The `_resolve_angle_keys` method determines which joint angle names
        belong to the current exercise type.

        ### Explanation:
        These keys are derived directly from the `JointAnalyzer.JointAngle`
        definitions, ensuring a one-to-one mapping between computed angles
        and the fields tracked in the history structure.

        ### Returns:
        - `list[str]`: Names of the angles relevant for this exercise.
        """
        if self.exercise_type == ExerciseType.SQUAT:
            return [j.name for j in JointAngle.Squat.CORE + JointAngle.Squat.EXTENDED]
        elif self.exercise_type == ExerciseType.BICEPS_CURL:
            return [j.name for j in JointAngle.BicepsCurl.CORE + JointAngle.BicepsCurl.EXTENDED]
        elif self.exercise_type == ExerciseType.LATERAL_RAISE:
            return [j.name for j in JointAngle.LateralRaise.CORE + JointAngle.LateralRaise.EXTENDED]
        else:
            ErrorHandler.handle(
                error=ErrorCode.EXERCISE_TYPE_DOES_NOT_EXIST,
                origin=inspect.currentframe()
            )
            return []

    ######################
    ### UPDATE HISTORY ###
    ######################
    def update(self, joint_angles:Dict[str, float], mean_visibility:float, bbox_area:float) -> None:
        """
        ### Brief:
        Updates the `analysis_data` dictionary after processing a new frame.

        ### Arguments:
        - `joint_angles` (Dict[str, float]): Latest calculated angles from `JointAnalyzer`.
        - `mean_visibility` (float): Mean landmark visibility returned by `PoseQualityManager`.
        - `bbox_area` (float): Bounding box area ratio (helps identify scale and proximity).

        ### Explanation:
        Called by `SessionManager.analyze_frame()` immediately after `JointAnalyzer` finishes
        and before `PhaseDetector` runs. It stores the newly calculated frame-level data and
        maintains rolling windows for short-term analysis.

        ### Processing Steps:
        1. Increment frame index.
        2. Append latest `joint_angles` and auxiliary metrics to rolling windows.
        3. Compute velocities (difference vs previous frame).
        4. Trim buffers to maintain constant memory footprint.
        5. Prepare the dataset for `PhaseDetector`.
        """

        try:
            self.analysis_data["frame_index"] += 1
            now = time.time()

            # Rolling windows: append and truncate
            self.analysis_data["angles_window"].append(joint_angles)
            self.analysis_data["visibility_window"].append(mean_visibility)
            self.analysis_data["bbox_area_window"].append(bbox_area)

            max_size = self.analysis_data["angles_window_size"]
            if len(self.analysis_data["angles_window"]) > max_size:
                self.analysis_data["angles_window"].pop(0)
                self.analysis_data["visibility_window"].pop(0)
                self.analysis_data["bbox_area_window"].pop(0)

            # Compute angle velocities
            if len(self.analysis_data["angles_window"]) >= 2:
                prev_angles = self.analysis_data["angles_window"][-2]
                dt = max(now - self.analysis_data.get("phase_enter_time", now), 1e-3)
                vels = {}
                for key in joint_angles.keys():
                    prev_val = prev_angles.get(key)
                    curr_val = joint_angles.get(key)
                    if prev_val is not None and curr_val is not None:
                        vels[key] = (curr_val - prev_val) / dt
                self.analysis_data["angle_velocities"] = vels

            # Mean visibility tracking (basic confidence indicator)
            self.analysis_data["mean_visibility"] = mean_visibility
            self.analysis_data["bbox_area_latest"] = bbox_area

        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_UPDATE_ERROR,
                origin=inspect.currentframe(),
                extra_info={"Exception": str(e)}
            )

    ########################
    ### ACCESSOR METHODS ###
    ########################
    def get_data(self) -> Dict[str, Any]:
        """Returns the current analysis_data dictionary."""
        return self.analysis_data

    def get_latest_angles(self) -> Dict[str, float]:
        """Returns the most recent set of joint angles (or empty dict)."""
        if not self.analysis_data["angles_window"]:
            return {}
        return self.analysis_data["angles_window"][-1]

    def get_last_phase(self) -> str:
        """Returns the last detected phase string."""
        return self.analysis_data.get("last_phase", "NONE")

    def set_phase(self, new_phase: str, transition: str):
        """
        ### Brief:
        Updates the last detected motion phase and logs the transition.

        ### Arguments:
        - `new_phase`: The phase determined by PhaseDetector.
        - `transition`: Human-readable transition (e.g., "DOWN->UP").

        ### Notes:
        Called by `PhaseDetector` when a new stable phase is identified.
        """
        prev_phase = self.analysis_data.get("last_phase", "NONE")
        self.analysis_data["prev_phase"] = prev_phase
        self.analysis_data["last_phase"] = new_phase
        self.analysis_data["phase_enter_time"] = time.time()
        self.analysis_data["last_transition"] = transition
        Logger.info(f"Phase transition: {transition}")
