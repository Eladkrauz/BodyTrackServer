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
from enum import IntEnum, auto

###################################
### CALIBRATION CODE ENUM CLASS ###
###################################
class CalibrationCode(IntEnum):
    """
    ### Description:
    The `CalibrationCode` enum class defines various calibration status codes
    related to user visibility and positioning checks.
    """
    USER_VISIBILITY_IS_VALID           = auto()
    USER_VISIBILITY_IS_UNDER_CHECKING  = auto()
    USER_POSITIONING_IS_VALID          = auto()
    USER_POSITIONING_IS_UNDER_CHECKING = auto()

    @property
    def description(self) -> str:
        return {
            CalibrationCode.USER_VISIBILITY_IS_VALID:           "Initial frame visibility checking is valid.",
            CalibrationCode.USER_VISIBILITY_IS_UNDER_CHECKING:  "Initial frame visibility checking is in process.",
            CalibrationCode.USER_POSITIONING_IS_VALID:          "Initial frame positioning checking is valid.",
            CalibrationCode.USER_POSITIONING_IS_UNDER_CHECKING: "Initial frame positioning checking is in process.",
        }[self]


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