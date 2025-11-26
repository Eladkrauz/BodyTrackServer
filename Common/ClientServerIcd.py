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
        # Client-server communication, including database operations failures.
        CLIENT_IP_IS_INVALID                = (100, "The provided IP is invalid.")
        CLIENT_AGENT_IS_INVALID             = (101, "The provided client agent is invalid.")
        INVALID_JSON_PAYLOAD_IN_REQUEST     = (102, "The JSON payload in the request is invalid.")
        MISSING_EXERCISE_TYPE_IN_REQUEST    = (103, "The request does not contain an exercise type.")
        MISSING_SESSION_ID_IN_REQUEST       = (104, "The request does not contain a session id.")
        MISSING_FRAME_DATA_IN_REQUEST       = (105, "The request does not contain frame data, which should include session id, frame id and frame content.")
        FRAME_DECODING_FAILED               = (106, "The request contains frame content that could not be decoded.")
        INTERNAL_SERVER_ERROR               = (107, "There was an internal server error.")
        USER_ALREADY_EXISTS                 = (108, "The user already exists in the system.")
        DATABASE_INSERT_FAILED              = (109, "Failed to insert to database.")
        DATABASE_QUERY_FAILED               = (110, "Failed to query the database.")
        DATABASE_UPDATE_FAILED              = (111, "Failed to update the database.")
        DATABASE_DELETE_FAILED              = (112, "Failed to delete from the database")
        USER_INVALID_CREDENTIALS            = (113, "The provided user credentials are invalid.")
        USER_IS_ALREADY_LOGGED_IN           = (114, "The user with the given credentials is already logged in.")
        USER_IS_NOT_LOGGED_IN               = (115, "The user with the given credentials is not logged in.")
        USER_NOT_FOUND                      = (116, "The user with the given user id is not found in the system.")


        # Session.
        CANT_REGISTER_CLIENT_TO_SESSION     = (200, "The system can't register the client to a new session.")
        EXERCISE_TYPE_DOES_NOT_EXIST        = (201, "The provided exercise type is not supported.")
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
        INVALID_EXTENDED_EVALUATION_PARAM   = (213, "The parameter of extended evaluation is not valid.")

        # PoseAnalyzer, PoseQualityManager, JointAnalyzer and frame processing.
        FRAME_INITIAL_VALIDATION_FAILED     = (300, "The initial validation process of the frame failed.")
        FRAME_ANALYZING_FAILED              = (301, "Failed to analyze frame.")
        JOINT_ANALYZING_FAILED              = (302, "Failed to calculate frame joint angles.")
        TOO_MANY_INVALID_ANGLES             = (303, "Too many invalid angles in the provided frame")
        QUALITY_CHECKING_ERROR              = (304, "Error during the run of quality checking.")
        NO_PERSON_DETECTED_IN_FRAME         = (305, "No person detected in received frame")
        LOW_VISIBILITY_IN_FRAME             = (306, "The received visibility is too low")
        PARTIAL_BODY_IN_FRAME               = (307, "Only partial body is in frame")
        TOO_FAR_IN_FRAME                    = (308, "The person in frame is too far")
        TOO_CLOSE_IN_FRAME                  = (309, "The person in frame is too close")
        UNSTABLE_IN_FRAME                   = (310, "The frame is unstable")

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
        CLIENT_SESSION_IS_REGISTERED        = (101, "The client's session is registered.")
        CLIENT_SESSION_IS_ACTIVE            = (102, "The client's session is active.")
        CLIENT_SESSION_IS_PAUSED            = (103, "The client's session is paused.")
        CLIENT_SESSION_IS_RESUMED           = (104, "The client's session is resumed.")
        CLIENT_SESSION_IS_ENDED             = (105, "The client's session is ended.")
        CLIENT_SESSION_IS_UNREGISTERED      = (106, "The client's session is unregistered.")
        CLIENT_SESSION_IS_NOT_IN_SYSTEM     = (107, "The client's session is not in the system.")
        FRAME_ANALYZED_SUCCESSFULLY         = (108, "The frame analyzed successfully.")

        def __new__(cls, code, description):
            obj = object.__new__(cls)
            obj._value_ = code
            obj.description = description
            return obj