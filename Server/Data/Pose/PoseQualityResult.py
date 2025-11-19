############################################################
############# BODY TRACK // SERVER // PIPELINE #############
############################################################
################ CLASS: PoseQualityResult ##################
############################################################

###############
### IMPORTS ###
###############
from dataclasses import dataclass
from Server.Data.Pose.PoseQuality import PoseQuality

#################################
### POSE QUALITY RESULT CLASS ###
#################################
@dataclass
class PoseQualityResult:
    """
    Holds the final pose-quality decision for the frame and 
    the metrics needed by the HistoryManager.
    """
    quality: PoseQuality
    mean_visibility: float
    bbox_area: float