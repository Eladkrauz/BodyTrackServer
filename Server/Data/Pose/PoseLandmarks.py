###############################################################
############## BODY TRACK // SERVER // DATA // POSE ###########
###############################################################
#################### CLASS: PoseLandmarks #####################
###############################################################

###############
### IMPORTS ###
###############
import numpy as np

##################################
### POSE LANDMARKS ARRAY ALIAS ###
##################################
"""
### Description:
`PoseArray` is a NumPy array containing body landmarks extracted from MediaPipe Pose.
Its shape is (33, 4), one row per landmark.

### Data type:
`np.float32`

### Explanation:
Each row corresponds to a single body landmark as defined in MediaPipe's 33-point skeleton model. The four columns represent:
- [i, 0] → x-coordinate (float, normalized to [0, 1], relative to frame width)
- [i, 1] → y-coordinate (float, normalized to [0, 1], relative to frame height)
- [i, 2] → z-coordinate (float, relative depth; negative = closer to camera)
- [i, 3] → visibility score (float in [0, 1], confidence that landmark is visible)

### Example:
`[0.5123, 0.7341, -0.1045, 0.9987]`
Landmark at ~51% width, 73% height, slightly closer to camera, ~99.9% visible.
"""
PoseLandmarksArray = np.ndarray

###########################
### POSE LANDMARK CLASS ###
###########################
class PoseLandmark:
    """
    ### Description:
    The `PoseLandmark` class defines constants for the 33 body landmarks
    detected by MediaPipe Pose. Each constant corresponds to a row index in the PoseArray (33x4 NumPy array).

    ### Columns in PoseArray:
    - [i, 0] → x (float, normalized to [0,1], relative to frame width)
    - [i, 1] → y (float, normalized to [0,1], relative to frame height)
    - [i, 2] → z (float, relative depth; negative = closer to camera)
    - [i, 3] → visibility (float in [0,1], probability landmark is visible)
    """
    NOSE              = 0
    LEFT_EYE_INNER    = 1
    LEFT_EYE          = 2
    LEFT_EYE_OUTER    = 3
    RIGHT_EYE_INNER   = 4
    RIGHT_EYE         = 5
    RIGHT_EYE_OUTER   = 6
    LEFT_EAR          = 7
    RIGHT_EAR         = 8
    MOUTH_LEFT        = 9
    MOUTH_RIGHT       = 10
    LEFT_SHOULDER     = 11
    RIGHT_SHOULDER    = 12
    LEFT_ELBOW        = 13
    RIGHT_ELBOW       = 14
    LEFT_WRIST        = 15
    RIGHT_WRIST       = 16
    LEFT_PINKY        = 17
    RIGHT_PINKY       = 18
    LEFT_INDEX        = 19
    RIGHT_INDEX       = 20
    LEFT_THUMB        = 21
    RIGHT_THUMB       = 22
    LEFT_HIP          = 23
    RIGHT_HIP         = 24
    LEFT_KNEE         = 25
    RIGHT_KNEE        = 26
    LEFT_ANKLE        = 27
    RIGHT_ANKLE       = 28
    LEFT_HEEL         = 29
    RIGHT_HEEL        = 30
    LEFT_FOOT_INDEX   = 31
    RIGHT_FOOT_INDEX  = 32
    NUM_OF_LANDMARKS  = 33