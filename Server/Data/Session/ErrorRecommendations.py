################################################################
########### BODY TRACK // SERVER // DATA // SESSION ############
################################################################
################# CLASS: ErrorRecommendations ##################
################################################################

###############
### IMPORTS ###
###############
from typing import Dict
from Data.Error.DetectedErrorCode import DetectedErrorCode

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
        #######################
        ### SQUAT TOP PHASE ###
        #######################
        DetectedErrorCode.SQUAT_TOP_KNEE_TOO_STRAIGHT:
            "Increase knee flexion.",

        DetectedErrorCode.SQUAT_TOP_KNEE_TOO_BENT:
            "Reduce knee flexion.",

        DetectedErrorCode.SQUAT_TOP_HIP_TOO_STRAIGHT:
            "Increase hip flexion.",

        DetectedErrorCode.SQUAT_TOP_HIP_TOO_BENT:
            "Reduce hip flexion.",

        DetectedErrorCode.SQUAT_TOP_TRUNK_TOO_FORWARD:
            "Straighten your torso.",

        DetectedErrorCode.SQUAT_TOP_TRUNK_TOO_BACKWARD:
            "Bring torso to neutral.",

        DetectedErrorCode.SQUAT_TOP_HIP_LINE_UNBALANCED:
            "Balance weight evenly between hips.",


        ########################
        ### SQUAT DOWN PHASE ###
        ########################
        DetectedErrorCode.SQUAT_DOWN_TRUNK_TOO_FORWARD:
            "Reduce forward trunk lean.",

        DetectedErrorCode.SQUAT_DOWN_TRUNK_TOO_BACKWARD:
            "Reduce backward trunk lean.",

        DetectedErrorCode.SQUAT_DOWN_HIP_LINE_UNBALANCED:
            "Maintain balanced hip alignment.",


        ########################
        ### SQUAT HOLD PHASE ###
        ########################
        DetectedErrorCode.SQUAT_HOLD_KNEE_TOO_STRAIGHT:
            "Increase knee bend.",

        DetectedErrorCode.SQUAT_HOLD_KNEE_TOO_BENT:
            "Reduce knee bend.",

        DetectedErrorCode.SQUAT_HOLD_HIP_TOO_HIGH:
            "Lower hips to proper depth.",

        DetectedErrorCode.SQUAT_HOLD_HIP_TOO_DEEP:
            "Raise hips slightly.",

        DetectedErrorCode.SQUAT_HOLD_TRUNK_TOO_FORWARD:
            "Lift torso to neutral.",

        DetectedErrorCode.SQUAT_HOLD_TRUNK_TOO_BACKWARD:
            "Bring torso forward to neutral.",

        DetectedErrorCode.SQUAT_HOLD_HIP_LINE_UNBALANCED:
            "Stabilize hip alignment.",


        ######################
        ### SQUAT UP PHASE ###
        ######################
        DetectedErrorCode.SQUAT_UP_TRUNK_TOO_FORWARD:
            "Lift chest while rising.",

        DetectedErrorCode.SQUAT_UP_TRUNK_TOO_BACKWARD:
            "Avoid backward trunk lean.",

        DetectedErrorCode.SQUAT_UP_HIP_LINE_UNBALANCED:
            "Maintain even hip drive.",


        ################################
        ### BICEPS CURL – REST PHASE ###
        ################################
        DetectedErrorCode.CURL_REST_ELBOW_TOO_BENT:
            "Fully extend your arms at the bottom of the curl.",

        DetectedErrorCode.CURL_REST_ELBOW_TOO_STRAIGHT:
            "Maintain a slight natural bend in your elbows.",

        DetectedErrorCode.CURL_REST_SHOULDER_TOO_FORWARD:
            "Pull your shoulders back and keep them stable.",

        DetectedErrorCode.CURL_REST_SHOULDER_TOO_BACKWARD:
            "Relax your shoulders - avoid excessive retraction.",


        ###################################
        ### BICEPS CURL – LIFTING PHASE ###
        ###################################
        DetectedErrorCode.CURL_LIFTING_ELBOW_TOO_STRAIGHT:
            "Bend your elbows more as you lift the weight.",

        DetectedErrorCode.CURL_LIFTING_ELBOW_TOO_BENT:
            "Control the lift - avoid over-curling too early.",

        DetectedErrorCode.CURL_LIFTING_SHOULDER_TOO_FORWARD:
            "Keep your shoulders back while lifting.",

        DetectedErrorCode.CURL_LIFTING_SHOULDER_TOO_BACKWARD:
            "Avoid pulling your shoulders backward during the lift.",


        ################################
        ### BICEPS CURL – HOLD PHASE ###
        ################################
        DetectedErrorCode.CURL_HOLD_ELBOW_TOO_OPEN:
            "Squeeze more at the top of the curl.",

        DetectedErrorCode.CURL_HOLD_ELBOW_TOO_CLOSED:
            "Avoid over-contracting - hold a strong but controlled position.",

        DetectedErrorCode.CURL_HOLD_WRIST_TOO_FLEXED:
            "Keep your wrist neutral - avoid bending it inward.",

        DetectedErrorCode.CURL_HOLD_WRIST_TOO_EXTENDED:
            "Relax your wrist slightly - avoid bending it backward.",


        ###################################
        ### BICEPS CURL – LOWERING PHASE ###
        ###################################
        DetectedErrorCode.CURL_LOWERING_ELBOW_TOO_STRAIGHT:
            "Control the lowering - do not lock your elbows.",

        DetectedErrorCode.CURL_LOWERING_ELBOW_TOO_BENT:
            "Extend your arms more as you lower the weight.",

        DetectedErrorCode.CURL_LOWERING_SHOULDER_TOO_FORWARD:
            "Keep your shoulders stable while lowering.",

        DetectedErrorCode.CURL_LOWERING_SHOULDER_TOO_BACKWARD:
            "Avoid pulling your shoulders backward on the way down.",
    
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
