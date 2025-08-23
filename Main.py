from Utilities.Logger import Logger as Log
from Utilities.ErrorHandler import ErrorHandler as Error
from Utilities.ErrorHandler import ErrorCode as ErrorCode
from Utilities.ConfigLoader import ConfigLoader as Config
import inspect

def main() -> None:
    Log.info(Config.get(key="SUPPORTED_EXERCISES"))
    Log.info(Config.print_all())
    Error.handle(
        opcode=ErrorCode.ERROR_CODE_5,
        origin=inspect.currentframe(),
        message="Can't read configuration file.",
        extra_info={
            "Expected file location": "C://hey/bye",
            "File does not exist there or is not readable": "Please make sure the file exists and has permissions.",
            "Can't run system without configuration file": "Aborting system."
            },
        critical=False
    )

    Error.handle(
        opcode=ErrorCode.ERROR_CODE_4,
        origin=inspect.currentframe(),
        message="The provided frame is not valid.",
        extra_info={
            "Expected frame type": "RGB",
            "Frame type provided": "BGR",
            "Can't process frame without valid type": "Aborting system."
            },
        critical=True
    )

main()