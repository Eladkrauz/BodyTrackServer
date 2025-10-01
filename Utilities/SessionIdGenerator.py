############################################################
################# BODY TRACK // UTILITIES ##################
############################################################
################ CLASS: SessionIdGenerator #################
############################################################

###############
### IMPORTS ###
###############
import uuid, inspect
from Utilities.ErrorHandler import ErrorHandler, ErrorCode
from Utilities.Logger import Logger
from dataclasses import dataclass

@dataclass
class SessionId:
    id:str

class SessionIdGenerator:
    """
    ### Description:
    The `SessionIdGenerator` class is responsible for generating unique session IDs for each exercise session in the BodyTrack system.
    
    ### Notes:
    - Uses Python's `uuid4` for randomness-based unique IDs.
    - Provides a simple and safe interface for ID creation.
    - In case of unexpected errors, logs the issue and falls back gracefully.
    """

    ###########################
    ### GENERATE SESSION ID ###
    ###########################
    def generate_session_id(self) -> SessionId:
        """
        ### Brief:
        The `generate_session_id` method generates a unique session ID for a new exercise session.
        
        ### Returns:
        - A `SessionId` dataclass object representing the unique session ID.
        
        ### Notes:
        - Uses UUID v4 which is random-based and extremely unlikely to collide.
        - Errors (if any) are logged, and `None` is returned.
        """
        try:
            session_id = SessionId(str(uuid.uuid4()))
            Logger.debug(f"Generated session ID: {session_id}")
            return session_id
        except MemoryError as e:
            ErrorHandler.handle(
                error=ErrorCode.ERROR_GENERATING_SESSION_ID,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": type(e).__name__,
                    "Reason": "The system ran out of memory while generating the session ID."
                }
            )
            return None
        except OSError as e:
            ErrorHandler.handle(
                error=ErrorCode.ERROR_GENERATING_SESSION_ID,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": type(e).__name__,
                    "Reason": "The OS random generator (os.urandom) failed."
                }
            )
            return None
    
    #################################
    ### PACK STRING TO SESSION ID ###
    #################################
    def pack_string_to_session_id(self, session_id:str) -> SessionId | None:
        """
        ### Brief:
        The `pack_string_to_session_id` method gets a `session_id` as a string and packs it to a `SessionId` object.
        
        ### Arguments:
        - `session_id` (str): A session id represented as a string (sent via HTTP communication).
        
        ### Returns:
        - `SessionId` object with the given session id string value, if valid, or `None` if not.
        """
        if self._is_session_id_valid(session_id):
            return SessionId(id=session_id)
        else:
            ErrorHandler.handle(
                error=ErrorCode.INVALID_SESSION_ID,
                origin=inspect.currentframe(),
                extra_info={ "The provided session id": session_id if isinstance(session_id, str) else "N/A" }
            )
            return None
    
    ###########################
    ### IS SESSION ID VALID ###
    ###########################
    def _is_session_id_valid(self, session_id:str) -> bool:
        """
        ### Brief:
        The `_is_session_id_valid` method checks if a provided session id is a valid one.
        
        ### Arguments:
        - `session_id` (str): A string containing a session id to be checked for validity.
        
        ### Returns:
        - `True` if the session id is valid, `False` if not.
        """
        if session_id is None:
            return False
        elif not isinstance(session_id, str):
            return False
        elif session_id == "":
            return False
        else:
            try:
                val = uuid.UUID(session_id, version=4)
            except ValueError:
                return False
            return val.version == 4 and str(val) == session_id