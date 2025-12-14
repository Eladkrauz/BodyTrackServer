################################################################
########### BODY TRACK // SERVER // DATA // SESSION ############
################################################################
################# CLASS: ErrorRecommendations ##################
################################################################

###############
### IMPORTS ###
###############
from typing import Dict
from Server.Data.Error.DetectedErrorCode import DetectedErrorCode

#############################
### ERROR RECOMMENDATIONS ###
#############################
class ErrorRecommendations:
    """
    ### Description:
    The `ErrorRecommendations` class provides predefined, human-readable recommendation
    messages for each biomechanical error defined in `DetectedErrorCode`.

    This class functions as a **static mapping only**:
        - No logic, no computation, and no stored state.
        - Centralized repository of feedback strings.
        - Allows the pipeline to remain modular by separating:
              (a) detection  → ErrorDetector
              (b) mapping    → ErrorRecommendations
              (c) summarizing→ SessionSummaryManager
              (d) formatting → FeedbackFormatter (if needed)

    ### Use Cases:
    - Used by `SessionSummaryManager` to produce final recommendations.
    - Can be used by future real-time feedback modules for instant corrective suggestions.
    """
    _default_message = "Maintain controlled, stable movement and proper form."
    _recommenations_map:Dict[DetectedErrorCode, str] = {
        ####################
        ### SQUAT ERRORS ###
        ####################
        DetectedErrorCode.SQUAT_NOT_DEEP_ENOUGH: 
            "Try lowering your hips slightly more to increase squat depth.",
        DetectedErrorCode.SQUAT_TOO_DEEP: 
            "You are squatting too deep — stop a bit higher to reduce knee load.",
        DetectedErrorCode.SQUAT_KNEES_INWARD: 
            "Keep your knees outward while squatting to maintain proper alignment.",
        DetectedErrorCode.SQUAT_KNEES_OUTWARD: 
            "Avoid pushing your knees too far out — aim to keep them aligned with your feet.",
        DetectedErrorCode.SQUAT_HEELS_OFF_GROUND: 
            "Try keeping your heels firmly on the ground throughout the movement.",
        DetectedErrorCode.SQUAT_WEIGHT_FORWARD: 
            "Your weight is shifting forward — try sitting back with your hips.",
        DetectedErrorCode.SQUAT_CHEST_LEAN_FORWARD: 
            "Keep your chest more upright during the squat.",
        DetectedErrorCode.SQUAT_BACK_ROUNDED: 
            "Straighten your back and engage your core to avoid rounding.",
        DetectedErrorCode.SQUAT_HIP_SHIFT_LEFT:
            "Your hips are shifting left — aim to distribute your weight evenly.",
        DetectedErrorCode.SQUAT_HIP_SHIFT_RIGHT:
            "Your hips are shifting right — try to keep the movement centered.",

        ##########################
        ### BICEPS CURL ERRORS ###
        ##########################
        DetectedErrorCode.CURL_TOO_SHORT_TOP:
            "Try squeezing more at the top for a full contraction.",
        DetectedErrorCode.CURL_NOT_FULL_FLEXION:
            "Lift your arm higher to achieve full flexion.",
        DetectedErrorCode.CURL_ELBOWS_MOVING_FORWARD:
            "Keep your elbows close to your body — avoid pushing them forward.",
        DetectedErrorCode.CURL_ELBOWS_MOVING_BACKWARD:
            "Avoid pulling your elbows backward — keep them stable.",
        DetectedErrorCode.CURL_LEANING_FORWARD:
            "Stand more upright — avoid leaning forward.",
        DetectedErrorCode.CURL_LEANING_BACKWARD:
            "Avoid leaning backward — stabilize your torso.",
        DetectedErrorCode.CURL_WRIST_NOT_NEUTRAL:
            "Keep your wrist straight to avoid unnecessary stress.",

        ############################
        ### LATERAL RAISE ERRORS ###
        ############################
        DetectedErrorCode.LATERAL_ARMS_TOO_LOW:
            "Lift your arms slightly higher for proper lateral raise form.",
        DetectedErrorCode.LATERAL_ARMS_TOO_HIGH:
            "Avoid raising your arms above shoulder level.",
        DetectedErrorCode.LATERAL_ELBOWS_BENT_TOO_MUCH:
            "Straighten your elbows slightly — avoid excessive bending.",
        DetectedErrorCode.LATERAL_TORSO_SWAYING:
            "Avoid swaying your torso — use lighter weights if needed.",
        DetectedErrorCode.LATERAL_PARTIAL_REP:
            "Try completing the full range of motion for better results.",

        #####################
        ### SPECIAL CASES ###
        #####################
        DetectedErrorCode.NO_BIOMECHANICAL_ERROR:
            "No biomechanical issues detected.",
        DetectedErrorCode.NOT_READY_FOR_ANALYSIS:
            "Not enough stable data to analyze this repetition."
    }

    ##########################
    ### GET RECOMMENDATION ###
    ##########################
    @classmethod
    def get_recommendation(cls, error_code:DetectedErrorCode) -> str:
        """
        ### Brief:
        The `get` method retrieves a human-readable recommendation
        message associated with a specific `DetectedErrorCode`.

        ### Arguments:
        - `error_code` (DetectedErrorCode): The biomechanical error for which a
          recommendation is required.

        ### Returns:
        - `str`: The predefined recommendation message.
                If the error code is not present in the mapping,
                returns a generic fallback message.

        ### Notes:
        - This method ensures the system remains robust even if new enum values
          are added before recommendations are written for them.
        """
        return cls._recommenations_map.get(error_code, cls._default_message)
