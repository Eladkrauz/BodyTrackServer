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
        REQUEST                             = 1
        RESPONSE                            = 2
        ERROR                               = 3

    class ErrorType(enum):
        # Client-server communication.
        CLIENT_IP_IS_INVALID                = (100, "The provided IP is invalid.")
        CLIENT_AGENT_IS_INVALID             = (101, "The provided client agent is invalid.")
        INVALID_JSON_PAYLOAD_IN_REQUEST     = (102, "The JSON payload in the request is invalid.")
        MISSING_EXERCISE_TYPE_IN_REQUEST    = (103, "The request does not contain an exercise type.")
        MISSING_SESSION_ID_IN_REQUEST       = (104, "The request does not contain a session id.")

        # Session.
        CANT_REGISTER_CLIENT_TO_SESSION     = (200, "The system can't register the client to a new session.")
        EXERCISE_TYPE_NOT_SUPPORTED         = (201, "The provided exercise type is not supported.")
        MAX_CLIENT_REACHED                  = (202, "The maximum of concurrent clients has reached.")
        INVALID_SESSION_ID                  = (203, "The provided session ID is not valid.")
        CLIENT_IS_NOT_REGISTERED            = (204, "The client is not registered to the system.")
        CLIENT_IS_ALREADY_REGISTERED        = (205, "The client is already registered to the system.")
        CLIENT_IS_NOT_ACTIVE                = (206, "The client is not in an active session.")
        CLIENT_IS_ALREADY_ACTIVE            = (207, "The client is already in an active session.")
        CLIENT_IS_NOT_PAUSED                = (208, "The client is not in a paused session.")
        CLIENT_IS_ALREADY_PAUSED            = (209, "The client is already in a paused session.")
        CLIENT_IS_NOT_ENDED                 = (210, "The client is not in an ended session.")
        CLIENT_IS_ALREADY_ENDED             = (211, "The client is already in an ended session.")
        CLIENT_IS_ONLY_REGISTERED           = (212, "The client is only registered, did not start yet.")

        def __new__(cls, code, description):
            obj = object.__new__(cls)
            obj._value_ = code
            obj.description = description
            return obj
        
    class ResponseType(enum):
        # Server Communication.
        ALIVE                               = (1, "")

        # Session.
        CLIENT_REGISTERED_SUCCESSFULLY      = (100, "The client was registered successfully.")
        CLIENT_SESSION_IS_ACTIVE            = (101, "The client's session is active.")
        CLIENT_SESSION_IS_PAUSED            = (102, "The client's session is paused.")
        CLIENT_SESSION_IS_RESUMED           = (103, "The client's session is resumed.")
        CLIENT_SESSION_IS_ENDED             = (104, "The client's session is ended.")
        CLIENT_SESSION_IS_UNREGISTERED      = (105, "The client's session is unregistered.")

        def __new__(cls, code, description):
            obj = object.__new__(cls)
            obj._value_ = code
            obj.description = description
            return obj