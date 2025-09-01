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
    @classmethod   
    def generate_session_id(cls) -> str:
        """
        ### Brief:
        The `generate_session_id` method generates a unique session ID for a new exercise session.
        ### Returns:
        - A string representing the unique session ID.
        ### Notes:
        - Uses UUID v4 which is random-based and extremely unlikely to collide.
        - Errors (if any) are logged, and `None` is returned.
        """
        try:
            session_id = str(uuid.uuid4())
            Logger.debug(f"Generated session ID: {session_id}")
            return session_id
        except MemoryError as e:
            ErrorHandler.handle(
                opcode=ErrorCode.ERROR_GENERATING_SESSION_ID,
                origin=inspect.currentframe(),
                message="MemoryError while generating session ID.",
                extra_info={
                    "Reason": "The system ran out of memory while generating the session ID."
                },
                critical=False
            )
            return None
        except OSError as e:
            ErrorHandler.handle(
                opcode=ErrorCode.ERROR_GENERATING_SESSION_ID,
                origin=inspect.currentframe(),
                message="OSError while generating session ID.",
                extra_info={
                    "Reason": "The OS random generator (os.urandom) failed."
                },
                critical=False
            )
            return None
