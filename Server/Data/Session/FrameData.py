###############################################################
############ BODY TRACK // SERVER // DATA // SESSION ##########
###############################################################
###################### CLASS: FrameData #######################
###############################################################

###############
### IMPORTS ###
###############
from dataclasses import dataclass
import numpy as np
from Utilities.SessionIdGenerator import SessionId

########################
### FRAME DATA CLASS ###
########################
@dataclass
class FrameData:
    """
    ### Description:
    The `FrameData` dataclass represents a single video frame in an active session.
    
    ### Attributes:
    - `session_id` (SessionId): Unique identifier of the session.
    - `frame_id` (int): Sequential ID of the frame.
    - `content` (np.ndarray): The frame image (BGR format, NumPy array).
    """
    session_id: SessionId
    frame_id:   int
    content:    np.ndarray

    ######################
    ### VALIDATE FRAME ###
    ######################
    def validate(self) -> None:
        """
        ### Brief:
        The `validate` method performs lightweight validation of the frame data.

        ### Raises:
        - `ValueError` is the frame content is `None`
        - `TypeError` if the frame content is not an `np.ndarray`
        
        ### Notes:
        - Ensures the frame exists and is a NumPy array.
        - Leaves deeper checks (shape, channels) to `PoseAnalyzer`.
        """
        if self.content is None:
            from Utilities.Error.ErrorHandler import ErrorHandler
            from Utilities.Error.ErrorCode import ErrorCode
            import inspect
            ErrorHandler.handle(
                error=ErrorCode.FRAME_INITIAL_VALIDATION_FAILED,
                origin=inspect.currentframe(),
                extra_info={"Reason": "Frame content is None."}
            )
            raise ValueError("Invalid FrameData: content is None.")

        if not isinstance(self.content, np.ndarray):
            from Utilities.Error.ErrorHandler import ErrorHandler
            from Utilities.Error.ErrorCode import ErrorCode
            import inspect
            ErrorHandler.handle(
                error=ErrorCode.FRAME_INITIAL_VALIDATION_FAILED,
                origin=inspect.currentframe(),
                extra_info={"Reason": "Frame content is not a NumPy array."}
            )
            raise TypeError("Invalid FrameData: content is not a NumPy array.")

        from Utilities.Logger import Logger
        Logger.debug(f"FrameData {self.frame_id} (Session {self.session_id.id}) validated successfully.")

    #################
    ### TO STRING ###
    #################
    def __str__(self) -> str:
        """
        ### Brief:
        The `__str__` method returns a string representation of the `FrameData` instance.

        ### Returns:
        A `str` representation of the `FrameData` instance.
        """
        return f"Session ID: {self.session_id.id}, Frame ID: {self.frame_id}"