###############################################################
############## BODY TRACK // SERVER // MANAGEMENT #############
###############################################################
################ CLASS: SessionSummaryManager #################
###############################################################

###############
### IMPORTS ###
###############
from copy import deepcopy
from math import ceil
from typing import Dict, Any, List
import inspect
from datetime import datetime

from Data.Response.SummaryResponse     import SummaryResponse
from Data.Session.SessionData          import SessionData
from Data.History.HistoryData          import HistoryData
from Utilities.Config.ConfigLoader     import ConfigLoader
from Utilities.Config.ConfigParameters import ConfigParameters
from Data.Error.DetectedErrorCode      import DetectedErrorCode
from Data.Session.ErrorRecommendations import ErrorRecommendations
from Utilities.Logger                  import Logger
from Utilities.Error.ErrorHandler      import ErrorHandler
from Utilities.Error.ErrorCode         import ErrorCode
from Data.History.HistoryDictKey       import HistoryDictKey

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
            self.retrieve_configurations()
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
            history:HistoryData                 = session_data.get_history()
            session_duration_seconds:float      = history.get_exercise_duration()
            reps:List[Dict[str, Any]]           = history.get_rep_history()
            average_rep_duration_seconds:float  = self._average_rep_duration_seconds(reps)
            raw_reps:List[Dict[str, Any]]       = deepcopy(history.get_rep_history())
            reps_breakdown:List[Dict[str, Any]] = self._prepare_reps(reps)
            aggregated_errors:Dict[str, int]    = self._aggregated_rep_errors(reps_breakdown)

            # Construct the SummaryResponse object.
            session_summary = SummaryResponse(
                session_id=                   session_data.session_id.id,
                exercise_type=                session_data.exercise_type.value,
                session_duration_seconds=     session_duration_seconds,
                number_of_reps=               history.get_rep_count(),
                average_rep_duration_seconds= average_rep_duration_seconds,
                overall_grade=                self._overall_grade(raw_reps),
                rep_breakdown=                reps_breakdown,
                aggregated_errors=            aggregated_errors,
                recommendations=              self._recommendations(aggregated_errors)
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
    
    ####################################
    ### AVERAGE REP DURATION SECONDS ###
    ####################################
    def _average_rep_duration_seconds(self, reps: List[Dict[str, Any]]) -> float:
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
            from Data.History.HistoryDictKey import HistoryDictKey
            total_duration = sum(rep[HistoryDictKey.Repetition.DURATION] for rep in reps)
            return round(total_duration / len(reps) if reps else 0.0, 2)
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
    def _overall_grade(self, reps:List[Dict[str, Any]]) -> float:
        """
        ### Brief:
        The `_overall_grade` method computes the overall performance grade for the session.

        ### The formula:
        - Start with `max_grade`.
        - For each incorrect rep, apply a penalty proportional to the number of errors.
        - Ensure the final grade does not fall below `0`.

        ### Arguments:
        - `reps` (List[Dict[str, Any]]): List of repetitions with correctness info.
        
        ### Returns:
        - `float`: The computed grade, never below 0.
        """
        try:
            # If there are no repetitions, return a grade of 0.0.
            if not reps: return 0.0

            grades:List[float] = []

            for rep in reps:
                # Duration of the repetition in seconds.
                duration: float = rep.get(HistoryDictKey.Repetition.DURATION, 0.0)

                # Estimate total number of frames in this repetition.
                # We ceil the duration, add 1 second margin, and multiply by FPS.
                total_frames:int = (ceil(duration) + 1) * self.approximate_fps

                # Number of error frames (at most one error per frame).
                total_errors:int = len(rep.get(HistoryDictKey.Repetition.ERRORS, []))

                # Avoid division by zero (should not happen, but kept for safety).
                if total_frames <= 0:
                    grades.append(0.0)
                    continue

                # Compute penalty ratio and clamp it.
                penalty_ratio:float = min(
                    total_errors / total_frames,
                    self.penalty
                )

                # Compute grade for this repetition.
                rep_grade:float = self.max_grade * (1.0 - penalty_ratio)

                # Ensure grade is non-negative.
                grades.append(max(0.0, rep_grade))

            # Average grade across all repetitions.
            final_grade:float = sum(grades) / len(grades)

            return round(final_grade, 2)
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.SUMMARY_MANAGER_INTERNAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={"Exception": type(e), "Reason": str(e)}
            )
            return 0.0
        
    ####################
    ### PREPARE REPS ###
    ####################
    def _prepare_reps(self, reps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        ### Brief:
        The `_prepare_reps` method computes a detailed biomechanical breakdown for each repetition.

        ### Arguments:
        - `reps` (List[Dict[str, Any]]): List of repetitions with timestamps and error info.

        ### Returns:
        - `List[Dict[str, Any]]`: The list returned directly by `get_rep_history()`,
          describing for each rep:
            * start_time
            * end_time
            * duration
            * is_correct
            * errors
        """
        try:
            # Format timestamps and clean up errors for each rep.
            for rep_data in reps:
                start_time:datetime = rep_data[HistoryDictKey.Repetition.START_TIME]
                end_time:datetime   = rep_data[HistoryDictKey.Repetition.END_TIME]

                rep_data[HistoryDictKey.Repetition.START_TIME] = start_time.strftime("%H:%M:%S")
                rep_data[HistoryDictKey.Repetition.END_TIME]   = end_time.strftime("%H:%M:%S")

                if rep_data[HistoryDictKey.Repetition.IS_CORRECT] is True:
                    rep_data[HistoryDictKey.Repetition.ERRORS] = []
                else:
                    errors: List[str] = rep_data[HistoryDictKey.Repetition.ERRORS] or []
                    # Remove duplicates while keeping type List[str]
                    rep_data[HistoryDictKey.Repetition.ERRORS] = list(set(errors))

            return reps
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.SUMMARY_MANAGER_INTERNAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={"Exception": type(e), "Reason": str(e)}
            )
            return []
        
    #############################
    ### AGGREGATED REP ERRORS ###
    #############################
    def _aggregated_rep_errors(self, reps:List[Dict[str, Any]]) -> Dict[str, int]:
        """
        ### Brief:
        The `_aggregated_rep_errors` method aggregates the total number of
        each biomechanical error detected during the session.

        ### Arguments:
        - `reps` (List[Dict[str, Any]]): List of repetitions with error info.

        ### Returns:
        - `Dict[str, int]`: Mapping from error name → count.
        """
        try:
            aggregated_errors:Dict[str, int] = {}
            # Aggregate errors across all repetitions.
            for rep_data in reps:
                if rep_data[HistoryDictKey.Repetition.ERRORS] is None: continue

                repetitions_errors:List[str] = rep_data[HistoryDictKey.Repetition.ERRORS]
                for error in repetitions_errors:
                    if error in aggregated_errors:
                        aggregated_errors[error] += 1
                    else:
                        aggregated_errors[error] = 1
            
            # Return the final aggregated errors dictionary.
            return aggregated_errors
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
    def _recommendations(self, aggregated_errors:Dict[str, int]) -> List[str]:
        """
        ### Brief:
        The `_recommendations` method generates recommendations based on
        biomechanical errors detected.

        ### Logic:
        - Sort errors by frequency.
        - Retrieve human-readable recommendations for the top N errors.

        ### Arguments:
        - `aggregated_errors` (Dict[str, int]): Includes error counters collected throughout the session.

        ### Returns:
        - `List[str]`: readable recommendations based on top biomechanical mistakes.
        """
        try:
            # Sort errors by frequency in descending order.
            sorted_errors = sorted(
                aggregated_errors.items(),
                key=lambda item: item[1],
                reverse=True
            )

            recommendations = []
            count = 0
            # Iterate through sorted errors to get recommendations.
            for error_name, _ in sorted_errors:
                # Limit to top N errors.
                if count >= self.number_of_top_errors: break
                count += 1
                try:
                    # Convert error name to enum.
                    enum_error = DetectedErrorCode[error_name]
                    recommendations.append(
                        # Get human-readable recommendation.
                        ErrorRecommendations.get_recommendation(enum_error)
                    )
                except KeyError:
                    continue
            
            return recommendations
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.SUMMARY_MANAGER_INTERNAL_ERROR,
                origin=inspect.currentframe(),
                extra_info={"Exception": type(e), "Reason": str(e)}
            )
            return []
        
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
        self.number_of_top_errors:int = ConfigLoader().get([
            ConfigParameters.Major.SUMMARY,
            ConfigParameters.Minor.NUMBER_OF_TOP_ERRORS
        ])

        self.max_grade:float = ConfigLoader().get([
            ConfigParameters.Major.SUMMARY,
            ConfigParameters.Minor.MAX_GRADE
        ])

        self.penalty:float = ConfigLoader().get([
            ConfigParameters.Major.SUMMARY,
            ConfigParameters.Minor.PENALTY
        ])

        self.approximate_fps:int = ConfigLoader().get([
            ConfigParameters.Major.SUMMARY,
            ConfigParameters.Minor.APPROXIMATE_FPS
        ])