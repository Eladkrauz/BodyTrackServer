from Utilities.Logger import Logger as Log
from Utilities.ErrorHandler import ErrorHandler as Error
from Utilities.ErrorHandler import ErrorCode as ErrorCode
from Utilities.ConfigLoader import ConfigLoader as Config
from Utilities.ConfigLoader import ConfigParameters
from Server.Components.SessionManager import SessionData
from Utilities.SessionIdGeneratorMock import GenerateSessionId

import inspect

def main() -> None:
    Log.info(Config.get(key=ConfigParameters.SUPPORTED_EXERCIES, critical_value=True))
    data = SessionData(
        session_id=GenerateSessionId(length=10),
        exercise_type="TYPE"
    )
    print(data)

main()