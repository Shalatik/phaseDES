from dataclasses import dataclass
from typing import Any

@dataclass(order=True)
class Event:
    time: float
    seq: int
    type: str
    payload: Any
