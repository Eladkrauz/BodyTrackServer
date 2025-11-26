###############################################################
############ BODY TRACK // SERVER // DATA // SESSION ##########
###############################################################
##################### CLASS: SessionData ######################
###############################################################

###############
### IMPORTS ###
###############
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from Server.Utilities.SessionIdGenerator import SessionId
from Server.Data.Session.ExerciseType import ExerciseType
from Server.Data.Session.SessionStatus import SessionStatus
from Server.Pipeline.HistoryManager import HistoryManager

##########################
### SESSION DATA CLASS ###
##########################
@dataclass
class SessionData:
    """
    ### Brief:
    The `SessionData` represents metadata and runtime details for a single exercise session.

    ### Fields:
    - `session_id` (str): Unique session identifier.
    - `client_info` (dict[str, Any]): Metadata about the client device/IP.
    - `exercise_type` (ExerciseType): The type of exercise (e.g., "squats", "pushups").
    - `time` (dict[str, datetime]): Timestamps about the sessions.
    - `frames_received` (int): Total number of frames received during the session.
    - `extended_evaluation` (bool): Indicates whether evaluate the frame with extended joints or only core.
    - `history_manager` (HistoryManager): Holds pose analysis results and feedback.
    """
    ###########################
    ### SESSION DATA FIELDS ###
    ###########################
    session_id: SessionId
    client_info: Dict[str, Any]
    exercise_type: ExerciseType
    time: Dict[str, Optional[datetime]] = field(default_factory=lambda: {
        "registered": datetime.now(),
        "started": None,
        "paused": None,
        "ended": None,
        "last_activity": datetime.now()
    })
    frames_received: int = 0
    extended_evaluation: bool = False
    history_manager: Optional[HistoryManager] = field(init=False, default=None)

    # Create the HistoryManager instance based on the provided exercise type.
    def __post_init__(self):
        """
        ### Brief:
        The `__post_init__` method initializes the `HistoryManager` instance after all other fields are set.
        """
        try:
            self.history_manager = HistoryManager(self.exercise_type)
        except Exception as e:
            from Server.Utilities.Error.ErrorHandler import ErrorHandler
            from Server.Utilities.Error.ErrorCode import ErrorCode
            import inspect
            ErrorHandler.handle(
                error=ErrorCode.HISTORY_MANAGER_INIT_ERROR,
                origin=inspect.currentframe(),
                extra_info={
                    "Exception": type(e).__name__,
                    "Reason": str(e)
                }
            )
            raise e

    #########################
    ### UPDATE TIME STAMP ###
    #########################
    def update_time_stamp(self, session_status:SessionStatus = None) -> None:
        """
        ### Brief:
        The `update_time_stamp` method updates the times of a `SessionData` object.

        ### Arguments:
        - `session_status` (SessionStatus): The type of time to be updated.

        ### Notes:
        - `session_status` defaults to `None`. If so: updating just the `last_activity` time stamp.
        """
        now = datetime.now()
        if session_status is not None:
            if    session_status is SessionStatus.REGISTERED: self.time['registered'] = now
            elif  session_status is SessionStatus.ACTIVE:     self.time['started']    = now
            elif  session_status is SessionStatus.PAUSED:     self.time['paused']     = now
            elif  session_status is SessionStatus.ENDED:      self.time['ended']      = now
            else:
                from Server.Utilities.Error.ErrorHandler import ErrorHandler
                from Server.Utilities.Error.ErrorCode import ErrorCode
                import inspect
                ErrorHandler.handle(error=ErrorCode.SESSION_STATUS_IS_NOT_RECOGNIZED, origin=inspect.currentframe())

        self.time['last_activity'] = now
        return None