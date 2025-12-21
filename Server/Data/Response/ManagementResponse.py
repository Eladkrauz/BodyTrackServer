############################################################
######### BODY TRACK // SERVER // DATA // RESPONSE #########
############################################################
################ CLASS: ManagementResponse #################
############################################################

###############
### IMPORTS ###
###############
from enum import Enum as enum
from enum import auto
from typing import Dict, Any, Optional
from dataclasses import dataclass

######################################
### MANAGEMENT RESPONSE DICT ALIAS ###
######################################
ManagementResponseDict = Dict[str, Any]

##################################
### MANAGEMENT CODE ENUM CLASS ###
##################################
class ManagementCode(enum):
    CLIENT_REGISTERED_SUCCESSFULLY      = auto(), "The client was registered successfully."
    CLIENT_SESSION_IS_REGISTERED        = auto(), "The client's session is registered."
    CLIENT_SESSION_IS_ACTIVE            = auto(), "The client's session is active."
    CLIENT_SESSION_IS_PAUSED            = auto(), "The client's session is paused."
    CLIENT_SESSION_IS_RESUMED           = auto(), "The client's session is resumed."
    CLIENT_SESSION_IS_ENDED             = auto(), "The client's session is ended."
    CLIENT_SESSION_IS_UNREGISTERED      = auto(), "The client's session is unregistered."
    CLIENT_SESSION_IS_NOT_IN_SYSTEM     = auto(), "The client's session is not in the system."
    SERVER_IS_BEING_SHUTDOWN            = auto(), "The server is being shutdown."
    CONFIGURATION_UPDATED_SUCCESSFULLY  = auto(), "The configuration was updated successfully."

    def __new__(cls, code, description):
        obj = object.__new__(cls)
        obj._value_ = code
        obj.description = description
        return obj

@dataclass
#################################
### MANAGEMENT RESPONSE CLASS ###
#################################
class ManagementResponse:
    # Class fields.
    management_code:ManagementCode
    extra_info:Optional[Dict[str, Any]] = None

    ###############
    ### TO DICT ###
    ###############
    def to_dict(self) -> ManagementResponseDict:
        return_dict = {
            "code":        self.management_code.value,
            "description": self.management_code.description
        }
        if self.extra_info: return_dict["extra_info"] = self.extra_info
        return return_dict