from Management.ServerManager import ServerManager
from datetime import datetime
import traceback, os, time, threading, traceback
from types import TracebackType
from typing import Optional, Tuple

######################
### MAIN EXECUTION ###
######################
def main() -> None:
    try:
        ServerManager()
    except Exception as e:
        time.sleep(2)
        print("\n##############################################")
        print("### EXCEPTION CAUGHT DURING SERVER RUNTIME ###")
        print("##############################################\n")
        print("Exception:     ", e.__class__.__name__)
        print("Reason:        ", str(e))
        class_name, method_name = get_project_origin(e)
        print("Class Name:    ", class_name)
        print("Method Name:   ", method_name)
        print("Timestamp:     ", datetime.now())
        print("Note:           This error was not logged.")
        countdown_or_input(e)

##############################################################################
############################## HELPER FUNCTIONS ##############################
##############################################################################

##########################
### COUNTDOWN OR INPUT ###
##########################
def countdown_or_input(e, seconds: int = 30):
    """
    Displays a countdown while waiting for user input.
    If user presses Enter or any key before timeout,
    prints the exception traceback.
    """
    triggered = threading.Event()

    def wait_for_input():
        input()  # waits for Enter / key
        triggered.set()

    input_thread = threading.Thread(target=wait_for_input, daemon=True)
    input_thread.start()

    for remaining in range(seconds, -1, -1):
        if triggered.is_set():
            length = len(e.__class__.__name__) + len("### TRACEBACK OF ###") + 1
            line = '#' * length
            print(); print(line)
            print("### TRACEBACK OF", str(e.__class__.__name__).upper(), "###")
            print(line); print()

            traceback.print_exception(type(e), e, e.__traceback__)
            return

        print(f"\rPress any key to display traceback. Process will die in: {remaining:2d}s ", end="", flush=True)
        time.sleep(1)

##########################
### GET PROJECT ORIGIN ###
##########################
def get_project_origin(exc:BaseException) -> Tuple[Optional[str], str]:
    """
    Returns (class_name, function_name) for the originating frame
    inside the given project root.

    class_name is None for module-level functions or static methods.
    """
    project_root = "BodyTrack/Server"
    project_root = os.path.abspath(project_root)
    tb: Optional[TracebackType] = exc.__traceback__

    # Walk traceback from oldest to newest.
    frames = []
    while tb:
        frames.append(tb)
        tb = tb.tb_next

    # Find the *first* frame that belongs to the project.
    for tb in reversed(frames):
        frame = tb.tb_frame
        filename = os.path.abspath(frame.f_code.co_filename)

        if not filename.startswith(project_root):
            continue

        locals_ = frame.f_locals
        func_name = frame.f_code.co_name

        if "self" in locals_:
            return type(locals_["self"]).__name__, func_name

        if "cls" in locals_:
            return locals_["cls"].__name__, func_name

        return None, func_name

# Run the main fuction.
main()