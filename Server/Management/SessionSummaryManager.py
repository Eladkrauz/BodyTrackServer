###############################################################
############## BODY TRACK // SERVER // MANAGEMENT #############
###############################################################
################ CLASS: SessionSummaryManager #################
###############################################################

###############
### IMPORTS ###
###############
from typing import Dict, Any, List
import inspect
from datetime import datetime

from Server.Data.Response.SummaryResponse     import SummaryResponse
from Server.Data.Session.SessionData          import SessionData
from Server.Data.History.HistoryData          import HistoryData
from Server.Utilities.Config.ConfigLoader     import ConfigLoader
from Server.Utilities.Config.ConfigParameters import ConfigParameters
from Server.Data.Error.DetectedErrorCode      import DetectedErrorCode
from Server.Data.Session.ErrorRecommendations import ErrorRecommendations
from Server.Utilities.Logger                  import Logger
from Server.Utilities.Error.ErrorHandler      import ErrorHandler
from Server.Utilities.Error.ErrorCode         import ErrorCode

#####################################
### SUMMARY SESSION MANAGER CLASS ###
#####################################
class SessionSummaryManager():
    """
    ### Description:
    The `SessionSummaryManager` class is responsible for constructing a complete
    session summary at the end of a training exercise.

    It aggregates:
    - Session metadata (ID, type, total duration)
    - Performance metrics (rep count, average rep duration, overall grade)
    - Biomechanical details (rep breakdown, aggregated errors)
    - High-level personalized recommendations

    The result is returned as a `SummaryResponse` object.
    """
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self):
        """
        ### Brief:
        The `__init__` method initializes configuration parameters related
        to session scoring and reporting.

        ### Notes:
        - `number_of_top_errors`: how many top biomechanical errors to include in recommendations.
        - `penalty`: the penalty applied per biomechanical error.
        - `max_grade`: the maximum possible session grade.
        """
        try:
            self.number_of_top_errors:int = ConfigLoader().get([
                ConfigParameters.Major.SUMMARY,
                ConfigParameters.Minor.NUMBER_OF_TOP_ERRORS
            ])

            self.penalty:float = ConfigLoader().get([
                ConfigParameters.Major.SUMMARY,
                ConfigParameters.Minor.PENALTY_PER_ERROR
            ])

            self.max_grade:float = ConfigLoader().get([
                ConfigParameters.Major.SUMMARY,
                ConfigParameters.Minor.MAX_GRADE
            ])

            Logger.info("Initialized successfully.")

        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.SUMMARY_MANAGER_INIT_ERROR,
                origin=inspect.currentframe(),
                extra_info={"Exception": type(e).__name__, "Reason": str(e)}
            )

    ##############################
    ### CREATE SESSION SUMMARY ###
    ##############################
    def create_session_summary(self, session_data:SessionData) -> SummaryResponse:
        """
        ### Brief:
        The `create_session_summary` method creates a full `SummaryResponse`
        object summarizing the entire session.

        ### Arguments:
        - `session_data` (SessionData): The full session data, including:
            * history (reps, errors, timestamps)
            * exercise type
            * timing metadata

        ### Returns:
        - `SummaryResponse`: An aggregated representation of the session including:
            * Session metadata
            * Rep metrics
            * Grades
            * Biomechanical breakdown
            * Aggregated errors
            * Recommendations
        """
        try:
            history = session_data.get_history()

            session_summary = SummaryResponse(
                session_id=                     session_data.session_id,
                exercise_type=                  session_data.exercise_type,
                session_duration_seconds=       self._session_duration_seconds(history),
                number_of_reps=                 history.get_rep_count(),
                average_rep_duration_seconds=   self._average_rep_duration_seconds(history),
                overall_grade                   =self._overall_grade(history),
                rep_breakdown                   =self._rep_breakdown(history),
                aggregated_errors               =self._aggregated_errors(history),
                recommendations                 =self._recommendations(history)
            )

            Logger.info(f"Session summary created for session: {session_data.session_id}")
            return session_summary

        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.SUMMARY_MANAGER_CREATE_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception": type(e).__name__,
                    "Reason": str(e),
                    "SessionID": session_data.session_id
                }
            )
            return SummaryResponse.empty()  # fallback safe object if exists

    ################################
    ### SESSION DURATION SECONDS ###
    ################################
    def _session_duration_seconds(self, history: HistoryData) -> float | None:
        """
        ### Brief:
        The `_session_duration_seconds` method computes the total duration of the session in seconds.

        ### Arguments:
        - `history` (HistoryData): Provides timestamps for session start and end.

        ### Returns:
        - `float`: Duration in seconds, or `None` if timestamps are incomplete.
        """
        try:
            return history.get_exercise_duration()
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.SUMMARY_MANAGER_INTERNAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={"Exception": type(e), "Reason": str(e)}
            )
            return None
    
    ####################################
    ### AVERAGE REP DURATION SECONDS ###
    ####################################
    def _average_rep_duration_seconds(self, history: HistoryData) -> float:
        """
        ### Brief:
        The `_average_rep_duration_seconds` method computes the average duration of repetitions.

        ### Arguments:
        - `history` (HistoryData): Contains a list of completed reps.

        ### Returns:
        - `float`: The average rep duration. Returns `0.0` if no reps exist.
        """
        # Calculate average rep duration
        try:
            from Server.Data.History.HistoryDictKey import HistoryDictKey
            rep_list = history.get_rep_history()
            total_duration = sum(rep[HistoryDictKey.Repetition.DURATION] for rep in rep_list)
            return total_duration / len(rep_list) if rep_list else 0.0

        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.SUMMARY_MANAGER_INTERNAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={"Exception": type(e), "Reason": str(e)}
            )
            return 0.0

    #####################
    ### OVERALL GRADE ###
    #####################
    def _overall_grade(self, history: HistoryData) -> float:
        """
        ### Brief:
        The `_overall_grade` method computes the overall performance grade for the session.

        ### The formula:
        - `grade = max_grade - (total_errors * penalty)`

        ### Arguments:
        - `history` (HistoryData): Provides error counters.

        ### Returns:
        - `float`: The computed grade, never below 0.
        """
        from Server.Data.Error.DetectedErrorCode import DetectedErrorCode
        try:
            error_counters:Dict[str, int] = history.get_error_counters()
            
            if DetectedErrorCode.NO_BIOMECHANICAL_ERROR.name in error_counters:
                error_counters.pop(DetectedErrorCode.NO_BIOMECHANICAL_ERROR.name)
            if DetectedErrorCode.NOT_READY_FOR_ANALYSIS.name in error_counters:
                error_counters.pop(DetectedErrorCode.NOT_READY_FOR_ANALYSIS.name)

            total_errors = sum(error_counters.values())
            grade = max(0.0, self.max_grade - (total_errors * self.penalty))
            return grade

        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.SUMMARY_MANAGER_INTERNAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={"Exception": type(e), "Reason": str(e)}
            )
            return 0.0
        
    #####################
    ### REP BREAKDOWN ###
    #####################
    def _rep_breakdown(self, history: HistoryData) -> List[Dict[str, Any]]:
        """
        ### Brief:
        The `_rep_breakdown` method computes a detailed biomechanical breakdown for each repetition.

        ### Arguments:
        - `history` (HistoryData): Contains repetition-level information.

        ### Returns:
        - `List[Dict[str, Any]]`: The list returned directly by `get_rep_history()`,
          describing for each rep:
            * start_time
            * end_time
            * duration
            * is_correct
            * errors
        """
        from Server.Data.History.HistoryDictKey import HistoryDictKey
        try:
            rep_history:List[Dict[str, Any]] = history.get_rep_history()
            for rep_data in rep_history:
                start_time:datetime = rep_data[HistoryDictKey.Repetition.START_TIME]
                end_time:datetime = rep_data[HistoryDictKey.Repetition.END_TIME]

                rep_history[HistoryDictKey.Repetition.START_TIME] = start_time.strftime("%H:%M:%S")
                rep_history[HistoryDictKey.Repetition.END_TIME] = end_time.strftime("%H:%M:%S")

                if rep_history[HistoryDictKey.Repetition.IS_CORRECT] is True:
                    rep_history[HistoryDictKey.Repetition.ERRORS] = []
                
                return rep_history
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.SUMMARY_MANAGER_INTERNAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={"Exception": type(e), "Reason": str(e)}
            )
            return []
        
    #########################
    ### AGGREGATED ERRORS ###
    #########################
    def _aggregated_errors(self, history: HistoryData) -> Dict[str, int]:
        """
        ### Brief:
        The `_aggregated_errors` method aggregates the total number of
        each biomechanical error detected during the session.

        ### Arguments:
        - `history` (HistoryData): Maintains error counters.

        ### Returns:
        - `Dict[str, int]`: Mapping from error name → count.
        """
        try:
            return history.get_error_counters()
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.SUMMARY_MANAGER_INTERNAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={"Exception": type(e), "Reason": str(e)}
            )
            return {}
    
    #######################
    ### RECOMMENDATIONS ###
    #######################
    def _recommendations(self, history: HistoryData) -> List[str]:
        """
        ### Brief:
        The `_recommendations` method generates recommendations based on
        biomechanical errors detected.

        ### Logic:
        1. Converts error keys (strings) → `DetectedErrorCode` enums.
        2. Filters out irrelevant errors (such as NO_BIOMECHANICAL_ERROR).
        3. Sorts errors by frequency (highest first).
        4. Retrieves human-readable recommendation text from `ErrorRecommendations`.
        5. Returns only the top N errors (configured value).

        ### Arguments:
        - `history` (HistoryData): Includes error counters collected throughout the session.

        ### Returns:
        - `List[str]`: readable recommendations based on top biomechanical mistakes.
        """
        try:
            error_counters:Dict[str, int] = history.get_error_counters()
            typing_errors = {}
            for error, count in error_counters.items():
                enum_key:DetectedErrorCode = DetectedErrorCode[error] 
                typing_errors[enum_key] = count
            
            filtered_errors = {}
            irrelevant_errors = (DetectedErrorCode.NO_BIOMECHANICAL_ERROR, DetectedErrorCode.NOT_READY_FOR_ANALYSIS)
            for error, count in typing_errors.items():
                if count > 0 and error not in irrelevant_errors:
                    filtered_errors[error] = count

            sorted_errors = sorted(filtered_errors.items(), key=lambda item: item[1], reverse=True)
            recommendations = []
            for error, _ in sorted_errors[:self.number_of_top_errors]:
                recommendation = ErrorRecommendations.get_recommendation(error)
                recommendations.append(recommendation)
            return recommendations
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.SUMMARY_MANAGER_INTERNAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={"Exception": type(e), "Reason": str(e)}
            )
            return []