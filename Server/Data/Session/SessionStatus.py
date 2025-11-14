###############################################################
############ BODY TRACK // SERVER // DATA // SESSION ##########
###############################################################
##################### CLASS: SessionStatus ####################
###############################################################

###############
### IMPORTS ###
###############
from enum import Enum as enum

#################################
### SESSION STATUS ENUM CLASS ###
#################################
class SessionStatus(enum):
    """
    ### Description:
    The `SessionStatus` enum class represents the statuses a session can be in.
    """
    REGISTERED    = 0
    ACTIVE        = 1
    ENDED         = 2
    PAUSED        = 3
    NOT_IN_SYSTEM = 4