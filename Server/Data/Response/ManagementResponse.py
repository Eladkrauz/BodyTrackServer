############################################################
######### BODY TRACK // SERVER // DATA // RESPONSE #########
############################################################
################ CLASS: ManagementResponse #################
############################################################

###############
### IMPORTS ###
###############
from enum import IntEnum
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
class ManagementCode(IntEnum):
    CLIENT_REGISTERED_SUCCESSFULLY     = auto()
    CLIENT_SESSION_IS_REGISTERED       = auto()
    CLIENT_SESSION_IS_ACTIVE           = auto()
    CLIENT_SESSION_IS_PAUSED           = auto()
    CLIENT_SESSION_IS_RESUMED          = auto()
    CLIENT_SESSION_IS_ENDED            = auto()
    CLIENT_SESSION_IS_UNREGISTERED     = auto()
    CLIENT_SESSION_IS_NOT_IN_SYSTEM    = auto()
    SERVER_IS_BEING_SHUTDOWN           = auto()
    CONFIGURATION_UPDATED_SUCCESSFULLY = auto()
    SESSION_IS_STARTING                = auto()

    @property
    def description(self) -> str:
        return {
            ManagementCode.CLIENT_REGISTERED_SUCCESSFULLY:      "The client was registered successfully.",
            ManagementCode.CLIENT_SESSION_IS_REGISTERED:        "The client's session is registered.",
            ManagementCode.CLIENT_SESSION_IS_ACTIVE:            "The client's session is active.",
            ManagementCode.CLIENT_SESSION_IS_PAUSED:            "The client's session is paused.",
            ManagementCode.CLIENT_SESSION_IS_RESUMED:           "The client's session is resumed.",
            ManagementCode.CLIENT_SESSION_IS_ENDED:             "The client's session is ended.",
            ManagementCode.CLIENT_SESSION_IS_UNREGISTERED:      "The client's session is unregistered.",
            ManagementCode.CLIENT_SESSION_IS_NOT_IN_SYSTEM:     "The client's session is not in the system.",
            ManagementCode.SERVER_IS_BEING_SHUTDOWN:            "The server is being shutdown.",
            ManagementCode.CONFIGURATION_UPDATED_SUCCESSFULLY:  "The configuration was updated successfully.",
            ManagementCode.SESSION_IS_STARTING:                 "The session is starting."
        }[self]

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