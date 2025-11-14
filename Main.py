from Server.Utilities.Logger import Logger as Log
from Server.Utilities.Error.ErrorHandler import ErrorHandler
from Server.Utilities.Error.ErrorCode import ErrorCode
from Server.Utilities.Config.ConfigLoader import ConfigLoader
from Server.Utilities.Config.ConfigParameters import ConfigParameters

import inspect

def main() -> None:
    ConfigLoader.initialize()
    Log.initialize()
    key = ConfigParameters.Minor.ARCHIVE_DIR_NAME
    try:
        raise Exception("Bye")
    except Exception as e:
        ErrorHandler.handle(
            error=ErrorCode.CANT_ADD_URL_RULE_TO_FLASK_SERVER,
            origin=inspect.currentframe(),
            extra_info={
                "Exception type": f"{type(e).__name__}",
                "Reason": f"{str(e)}"
            }
        )

    print(ConfigLoader.get([ConfigParameters.Major.COMMUNICATION, ConfigParameters.Minor.HOST], True))
main()