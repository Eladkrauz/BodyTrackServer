############################################################
########### BODY TRACK // SERVER // DATA // POSE ###########
############################################################
################### CLASS: PoseQuality #####################
############################################################

###############
### IMPORTS ###
###############

from enum import Enum as enum
from enum import auto

#########################
### POSE QUALITY ENUM ###
#########################
class PoseQuality(enum):
    """
    ### Description:
    The `PoseQuality` enum epresents the possible quality states of a pose frame. 
    Each value describes a specific condition detected in the landmarks.

    ### Notes:
    Used by `PoseQualityManager` to report a single, clear quality result.
    """
    OK              = auto()
    NO_PERSON       = auto()
    PARTIAL_BODY    = auto()
    TOO_FAR         = auto()
    UNSTABLE        = auto()

    #############################
    ### CONVERT TO ERROR CODE ###
    #############################
    def convert_to_error_code(pose_quality:'PoseQuality'):
        """
        ### Brief:
        The `convert_to_error_code` static method maps a `PoseQuality` value
        to its corresponding `ErrorCode`.

        ### Arguments:
        - `pose_quality` (PoseQuality): The quality of the detected pose.

        ### Returns:
        - `ErrorCode` or `None`: The corresponding error code for the given pose quality,
          or `None` if the quality is `OK`.
        """
        from Server.Utilities.Error.ErrorCode import ErrorCode
        if   pose_quality is PoseQuality.NO_PERSON:      return ErrorCode.NO_PERSON_DETECTED_IN_FRAME
        elif pose_quality is PoseQuality.PARTIAL_BODY:   return ErrorCode.PARTIAL_BODY_IN_FRAME
        elif pose_quality is PoseQuality.TOO_FAR:        return ErrorCode.TOO_FAR_IN_FRAME
        elif pose_quality is PoseQuality.UNSTABLE:       return ErrorCode.UNSTABLE_IN_FRAME
        else:                                            return None