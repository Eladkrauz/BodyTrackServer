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
from threading import RLock

from Server.Utilities.SessionIdGenerator import SessionId
from Server.Data.Session.ExerciseType    import ExerciseType
from Server.Data.Session.SessionStatus   import SessionStatus
from Server.Data.Session.AnalyzingState  import AnalyzingState
from Server.Data.History.HistoryData     import HistoryData

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
    - `extended_evaluation` (bool): Indicates whether evaluate the frame with extended joints or only core.
    - `history_data` (HistoryData): Holds pose analysis results and feedback.
    """
    ###########################
    ### SESSION DATA FIELDS ###
    ###########################
    history:HistoryData                 = field(init=False)
    session_id:SessionId                = field()
    client_info:Dict[str, Any]          = field()
    exercise_type:ExerciseType          = field()
    time:Dict[str, Optional[datetime]]  = field(default_factory=lambda: {
        "registered": datetime.now(),
        "started": None,
        "paused": None,
        "ended": None,
        "last_activity": datetime.now(),
    })
    extended_evaluation:bool            = field(default=False)
    # TODO: CHANGE BACK TO INIT!!!
    analyzing_state:AnalyzingState      = field(default=AnalyzingState.INIT)
    lock:RLock                          = field(default_factory=RLock, init=False, repr=False)
    session_status:SessionStatus        = field(default=SessionStatus.REGISTERED)

    #################
    ### POST INIT ###
    #################
    def __post_init__(self):
        """
        ### Brief:
        The `__post_init__` method initializes the `HistoryData` instance after all other fields are set.
        """
        try:
            self.history = HistoryData()
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
    
    #####################################################################
    ############################## GETTERS ##############################
    #####################################################################

    ######################
    ### GET SESSION ID ###
    ######################
    def get_session_id(self) -> SessionId:
        """
        ### Brief:
        The `get_session_id` method retrieves the unique session identifier.

        ### Returns:
        - `SessionId`: The unique session identifier.
        """
        return self.session_id

    #######################
    ### GET CLIENT INFO ###
    #######################
    def get_client_info(self) -> Dict[str, Any]:
        """
        ### Brief:
        The `get_client_info` method retrieves the client information associated with the session.

        ### Returns:
        - `Dict[str, Any]`: The client information dictionary.
        """
        return self.client_info

    #########################
    ### GET EXERCISE TYPE ###
    #########################
    def get_exercise_type(self) -> ExerciseType:
        """
        ### Brief:
        The `get_exercise_type` method retrieves the `ExerciseType` of the session.

        ### Returns:
        - `ExerciseType`: The type of exercise for the session.
        """
        return self.exercise_type
    
    ###############################
    ### GET EXTENDED EVALUATION ###
    ###############################
    def get_extended_evaluation(self) -> bool:
        """
        ### Brief:
        The `get_extended_evaluation` method retrieves whether extended evaluation
        is enabled for the session.

        ### Returns:
        - `bool`: True if extended evaluation is enabled, False otherwise.
        """
        return self.extended_evaluation

    ###########################
    ### GET ANALYZING STATE ###
    ###########################
    def get_analyzing_state(self) -> AnalyzingState:
        """
        ### Brief:
        The `get_analyzing_state` method retrieves the current `AnalyzingState` of the session.
        
        ### Returns:
        - `AnalyzingState`: The current analyzing state of the session.
        """
        return self.analyzing_state
    
    ##########################
    ### GET SESSION STATUS ###
    ##########################
    def get_session_status(self) -> SessionStatus:
        """
        ### Brief:
        The `get_session_status` method retrieves the current `SessionStatus` of the session.

        ### Returns:
        - `SessionStatus`: The current status of the session.
        """
        return self.session_status
    
    ###################
    ### GET HISTORY ###
    ###################
    def get_history(self) -> HistoryData:
        """
        ### Brief:
        The `get_history` method retrieves the `HistoryData` associated with the session.

        ### Returns:
        - `HistoryData`: The history data of the session.
        """
        return self.history

    #####################################################################
    ############################## SETTERS ##############################
    #####################################################################

    ###############################
    ### SET EXTENDED EVALUATION ###
    ###############################
    def set_extended_evaluation(self, extended_evaluation:bool) -> None:
        """
        ### Brief:
        The `set_extended_evaluation` method sets whether extended evaluation
        is enabled for the session.

        ### Arguments:
        - `extended_evaluation` (bool): `True` to enable extended evaluation, `False` to disable.
        """
        self.extended_evaluation = extended_evaluation

    ###########################
    ### SET ANALYZING STATE ###
    ###########################
    def set_analyzing_state(self, analyzing_state:AnalyzingState) -> None:
        """
        ### Brief:
        The `set_analyzing_state` method sets the current `AnalyzingState` of the session.

        ### Arguments:
        - `analyzing_state` (AnalyzingState): The new analyzing state to set.
        """
        self.analyzing_state = analyzing_state

    ##########################
    ### SET SESSION STATUS ###
    ##########################
    def set_session_status(self, session_status:SessionStatus) -> None:
        """
        ### Brief:
        The `set_session_status` method sets the current `SessionStatus` of the session.

        ### Arguments:
        - `session_status` (SessionStatus): The new session status to set.
        """
        self.session_status = session_status
        self.update_time_stamp(session_status)