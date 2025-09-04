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
                opcode=ErrorCode.ERROR_GENERATING_SESSION_ID,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": type(e).__name__,
                    "Reason": "The system ran out of memory while generating the session ID."
                }
            )
            return None
        except OSError as e:
            ErrorHandler.handle(
                opcode=ErrorCode.ERROR_GENERATING_SESSION_ID,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception type": type(e).__name__,
                    "Reason": "The OS random generator (os.urandom) failed."
                }
            )
            return None
