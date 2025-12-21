############################################################
######### BODY TRACK // SERVER // DATA // RESPONSE #########
############################################################
################ CLASS: CalibrationResponse ################
############################################################

###############
### IMPORTS ###
###############
from enum import Enum as enum
from enum import auto
from typing import Dict, Any, Optional
from dataclasses import dataclass

#######################################
### CALIBRATION RESPONSE DICT ALIAS ###
#######################################
CalibrationResponseDict = Dict[str, Any]

###################################
### CALIBRATION CODE ENUM CLASS ###
###################################
class CalibrationCode(enum):
    USER_VISIBILITY_IS_VALID           = auto(), "Initial frame visibility checking is valid."
    USER_VISIBILITY_IS_UNDER_CHECKING  = auto(), "Initial frame visibility checking is in process."
    USER_POSITIONING_IS_VALID          = auto(), "Initial frame positioning checking is valid."
    USER_POSITIONING_IS_UNDER_CHECKING = auto(), "Initial frame positioning checking is in process."

    def __new__(cls, code, description):
        obj = object.__new__(cls)
        obj._value_ = code
        obj.description = description
        return obj

@dataclass
##################################
### CALIBRATION RESPONSE CLASS ###
##################################
class CalibrationResponse:
    # Class fields.
    calibration_code:CalibrationCode
    extra_info:Optional[Dict[str, Any]] = None

    ###############
    ### TO DICT ###
    ###############
    def to_dict(self) -> CalibrationResponseDict:
        return_dict = {
            "code":        self.calibration_code.value,
            "description": self.calibration_code.description
        }
        if self.extra_info: return_dict["extra_info"] = self.extra_info
        return return_dict