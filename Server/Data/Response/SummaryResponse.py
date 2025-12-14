############################################################
######### BODY TRACK // SERVER // DATA // RESPONSE #########
############################################################
################# CLASS: SummaryResponse ###################
############################################################

###############
### IMPORTS ###
###############
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
##############################
### SUMMARY RESPONSE CLASS ###
##############################
class SummaryResponse:
    """
    ### Description:
    The `SummaryResponse` class represents the final summary returned at the end of a training session.

    ### Includes:
    - High-level session metadata
    - Rep-by-rep biomechanical breakdown
    - Aggregated biomechanical errors
    - Overall grade
    - Generated recommendations
    """
    # High-level session metadata.
    session_id:str
    exercise_type:str
    session_duration_seconds:float
    number_of_reps:int
    average_rep_duration_seconds:float

    # Performance grade.
    overall_grade:float

    # Rep-by-rep biomechanical breakdown.
    rep_breakdown:List[Dict[str, Any]] = field(default_factory=list)

    # Aggregated biomechanical errors.
    aggregated_errors:Dict[str, int] = field(default_factory=dict)

    # Generated recommendations.
    recommendations:List[str] = field(default_factory=list)

    ###############
    ### TO DICT ###
    ###############
    def to_dict(self) -> Dict[str, Any]:
        """
        ### Brief:
        The `to_dict` method converts the `SummaryResponse` instance into a dictionary format.

        ### Returns:
        - Dict[str, Any]: A dictionary representation of the `SummaryResponse` instance.
        """
        return {
            "session_id":                     self.session_id,
            "exercise_type":                  self.exercise_type,
            "session_duration_seconds":       self.session_duration_seconds,
            "number_of_reps":                 self.number_of_reps,
            "average_rep_duration_seconds":   self.average_rep_duration_seconds,
            "overall_grade":                  self.overall_grade,
            "rep_breakdown":                  self.rep_breakdown,
            "aggregated_errors":              self.aggregated_errors,
            "recommendations":                self.recommendations
        }