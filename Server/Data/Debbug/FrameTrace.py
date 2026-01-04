from dataclasses import dataclass, field
from typing import List, Dict
import time

from Data.Debbug.FrameEvent import FrameEvent

def now_str() -> str:
    t = time.time()
    base = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))
    millis = int((t - int(t)) * 1000)
    return f"{base}.{millis:03d}"

@dataclass
class FrameTrace:
    frame_id: int
    timestamp: str = field(default_factory=now_str)
    events: List[FrameEvent] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "events": [
                {
                    "stage": e.stage,
                    "success": e.success,
                    "result_type": e.result_type,
                    "result": e.result,
                    "info": e.info
                }
                for e in self.events
            ]
        }
