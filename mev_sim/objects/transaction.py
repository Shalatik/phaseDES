from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass(frozen=True)
class Tx:
    txid: str
    sender: str
    t_created: float
    data: Dict[str, Any] = field(default_factory=dict)