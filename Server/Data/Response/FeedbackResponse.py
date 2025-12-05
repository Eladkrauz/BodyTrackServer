############################################################
######### BODY TRACK // SERVER // DATA // RESPONSE #########
############################################################
################## CLASS: FeedbackResponse #################
############################################################

###############
### IMPORTS ###
###############
from enum import Enum as enum
from typing import Dict, Any, Optional
from dataclasses import dataclass

####################################
### FEEDBACK RESPONSE DICT ALIAS ###
####################################
FeedbackResponseDict = Dict[str, Any]

################################
### FEEDBACK CODE ENUM CLASS ###
################################
class FeedbackCode(enum):
    # Add enums here.
    
    def __new__(cls, code, description):
        obj = object.__new__(cls)
        obj._value_ = code
        obj.description = description
        return obj

@dataclass
###############################
### FEEDBACK RESPONSE CLASS ###
###############################
class FeedbackResponse:
    # Class fields.
    feedback_code:FeedbackCode
    extra_info:Optional[Dict[str, Any]] = None

    ###############
    ### TO DICT ###
    ###############
    def to_dict(self) -> FeedbackResponseDict:
        return_dict = {
            "code":        self.feedback_code.value,
            "description": self.feedback_code.description
        }
        if self.extra_info: return_dict["extra_info"] = self.extra_info
        return return_dict