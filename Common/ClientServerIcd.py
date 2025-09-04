#########################################################
################# BODY TRACK // COMMON ##################
#########################################################
################ CLASS: ClientServerIcd #################
#########################################################

###############
### IMPORTS ###
###############
from enum import Enum as enum
from enum import auto

class ClientServerIcd:
    class MessageType(enum):
        REQUEST  = auto()
        RESPONSE = auto()
        ERROR    = auto()

    class ErrorType(enum):
        # Client-server communication.
        CLIENT_IP_IS_INVALID = (100, "The provided IP is invalid.")
        CLIENT_AGENT_IS_INVALID = (101, "The provided client agent is invalid.")
        INVALID_JSON_PAYLOAD_IN_REQUEST = (102, "The JSON payload in the request is invalid.")
        MISSING_EXERCISE_TYPE_IN_REQUEST = (103, "The request does not contain an exercise type.")

        # Session.
        CANT_REGISTER_CLIENT_TO_SESSION = (200, "The system can't register the client to a new session.")
        EXERCISE_TYPE_NOT_SUPPORTED = (201, "The provided exercise type is not supported.")
        MAX_CLIENT_REACHED = (202, "The maximum of concurrent clients has reached.")

        def __new__(cls, code, description):
            obj = object.__new__(cls)
            obj._value_ = code
            obj.description = description
            return obj