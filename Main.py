from Utilities.Logger import Logger as Log
from Utilities.ErrorHandler import ErrorHandler as Error
from Utilities.ErrorHandler import ErrorCode as ErrorCode
from Utilities.ConfigLoader import ConfigLoader as Config
from Utilities.ConfigLoader import ConfigParameters
from Server.Components.SessionManager import SessionData
from Utilities.SessionIdGeneratorMock import GenerateSessionId
from Common.ClientServerIcd import ClientServerIcd as ICD

import inspect

def main() -> None:
    Config.initialize()
    Log.initialize()
    key = ConfigParameters.Minor.ARCHIVE_DIR_NAME
    try:
        raise Exception("Bye")
    except Exception as e:
        Error.handle(
            error=ErrorCode.CANT_ADD_URL_RULE_TO_FLASK_SERVER,
            origin=inspect.currentframe(),
            extra_info={
                "Exception type": f"{type(e).__name__}",
                "Reason": f"{str(e)}"
            }
        )

    print(Config.get([ConfigParameters.Major.COMMUNICATION, ConfigParameters.Minor.HOST], True))
main()