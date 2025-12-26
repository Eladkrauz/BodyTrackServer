#########################################################
######## BODY TRACK // SERVER // COMMUNICATION ##########
#########################################################
################# CLASS: Communication ##################
#########################################################

###############
### IMPORTS ###
###############
from typing import Dict, Any

from Utilities.Error.ErrorCode import ErrorCode, ErrorResponse, ErrorResponseDict
from Data.Response.FeedbackResponse import FeedbackResponse, FeedbackResponseDict
from Data.Response.CalibrationResponse import CalibrationResponse, CalibrationResponseDict
from Data.Response.ManagementResponse import ManagementResponse, ManagementResponseDict

################################
### PING RESPONSE DICT ALIAS ###
################################
PingResponseDict = Dict[str, Any]

##########################
### MESSAGE TYPE CLASS ###
##########################
class MessageType:
    REQUEST  = 1
    RESPONSE = 2
    ERROR    = 3

######################
### RESPONSE CLASS ###
######################
class Response:
    PING        = 1
    MANAGEMENT  = 2
    CALIBRATION = 3
    FEEDBACK    = 4
    UNKNOWN     = 5

class Communication:  
    ######################
    ### ERROR RESPONSE ###
    ######################
    @classmethod
    def error_response(cls, error:ErrorResponse = None, error_code:ErrorCode = None) -> ErrorResponseDict:
        """
        ### Brief:
        The `error_response` method gets an `ErrorResponse` and constructs a `HTTP`
        response `dict` message.

        ### Arguments:
        - `error` (ErrorResponse): The error response to be returned.
        - `error_code` (ErrorCode): The error code to be returned as response.

        ### Returns:
        - `ErrorResponseDict` which is a `Dict[str, Any]` with relevant information about the error.

        ### Raises:
        - `ValueError` if not only one parameter was provided, or both were not provided.
        """
        if error is not None and error_code is not None:
            raise ValueError("Communication.error_response(): Expecting exactly one parameter, not two.")
        if error is None and error_code is None:
            raise ValueError("Communication.error_response(): Expecting exactly one parameter, not zero.")
        
        to_return = {
            "message_type": MessageType.ERROR,
        }
        if error is not None:
            to_return.update(error.to_dict())
            
        if error_code is not None:
            to_return.update({
                "code":        error_code.value,
                "description": error_code.description
            })

        return to_return

    ##########################
    ### CONSTRUCT RESPONSE ###
    ##########################
    @classmethod
    def construct_response(
        cls, response:ManagementResponse | CalibrationResponse | FeedbackResponse
    ) -> ManagementResponseDict | CalibrationResponseDict | FeedbackResponseDict:
        """
        ### Brief:
        The `construct_response` method gets a response message and constructs a `HTTP`
        response `dict` message.

        ### Arguments:
        Can be one of these three:
        - `response` as a `ManagementResponse`
        - `response` as a `CalibrationResponse`
        - `response` as a `FeedbackResponse`

        ### Returns:
        Can be one of these three (corresponding to the argument):
        - `ManagementResponseDict` 
        - `CalibrationResponseDict` 
        - `FeedbackResponseDict` 
        
        Which are a `Dict[str, Any]` with relevant information about the message.
        """
        if   isinstance(response, ManagementResponse):  response_type = Response.MANAGEMENT
        elif isinstance(response, CalibrationResponse): response_type = Response.CALIBRATION
        elif isinstance(response, FeedbackResponse):    response_type = Response.FEEDBACK
        else:                                           response_type = Response.UNKNOWN
    
        to_return = {
            "message_type":  MessageType.RESPONSE,
            "response_type": response_type,
        }
        to_return.update(response.to_dict())
        return to_return
    
    #####################
    ### PING RESPONSE ###
    #####################
    @classmethod
    def ping_response(cls) -> PingResponseDict:
        """
        ### Brief:
        The `ping_response` method constructs a `HTTP` ping response `dict` message.

        ### Returns:
        - `PingResponseDict` which is a `Dict[str, Any]` for a ping response.
        """
        return {
            "message_type":  MessageType.RESPONSE,
            "response_type": Response.PING
        }
