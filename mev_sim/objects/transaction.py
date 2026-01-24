from dataclasses import dataclass, field
from typing import Any, Dict, Optional

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
    real_index: Optional[int] = None

    payload: Dict[str, Any] = field(default_factory=dict)
    
    def effective_priority_fee(self, burn_fee):
        return min(self.priority_fee, self.max_fee - burn_fee)