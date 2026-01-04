from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class FrameEvent:
    stage: str                 # "JointAnalyzer", "PhaseDetector", ...
    success: bool              # האם ה־Stage הצליח
    result_type: str           # "angles", "phase", "exception", ...
    result: Dict[str, Any]     # ייצוג פשוט (JSON-safe)
    info: Optional[Dict[str, Any]] = None
