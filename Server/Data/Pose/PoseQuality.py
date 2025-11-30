############################################################
############# BODY TRACK // SERVER // PIPELINE #############
############################################################
################### CLASS: PoseQuality #####################
############################################################

###############
### IMPORTS ###
###############
from enum import Enum as enum

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
    OK              = 0
    NO_PERSON       = 1
    LOW_VISIBILITY  = 2
    PARTIAL_BODY    = 3
    TOO_FAR         = 4
    TOO_CLOSE       = 5
    UNSTABLE        = 6

    #############################
    ### CONVERT TO ERROR CODE ###
    #############################
    def convert_to_error_code(self, pose_quality:'PoseQuality'):
        from Server.Utilities.Error.ErrorCode import ErrorCode
        if   pose_quality is PoseQuality.NO_PERSON:      return ErrorCode.NO_PERSON_DETECTED_IN_FRAME
        elif pose_quality is PoseQuality.LOW_VISIBILITY: return ErrorCode.LOW_VISIBILITY_IN_FRAME
        elif pose_quality is PoseQuality.PARTIAL_BODY:   return ErrorCode.PARTIAL_BODY_IN_FRAME
        elif pose_quality is PoseQuality.TOO_FAR:        return ErrorCode.TOO_FAR_IN_FRAME
        elif pose_quality is PoseQuality.TOO_CLOSE:      return ErrorCode.TOO_CLOSE_IN_FRAME
        elif pose_quality is PoseQuality.UNSTABLE:       return ErrorCode.UNSTABLE_IN_FRAME
        else:                                            return None