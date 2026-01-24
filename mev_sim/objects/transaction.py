from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass(frozen=True)
class Tx:
    txid: str
    sender: str
    t_created: float

    tx_type: str
    gas_used: int
    priority_fee: float
    max_fee: float
    nonce: int

    payload: Dict[str, Any] = field(default_factory=dict)