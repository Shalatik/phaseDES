from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass()
class Tx:
    txid: str
    sender: str
    t_created: float

    tx_type: str
    gas_used: int
    priority_fee: float
    max_fee: float
    nonce: int
    status: str
    real_index: Optional[int] = None

    payload: Dict[str, Any] = field(default_factory=dict)
    
    def effective_priority_fee(self, burn_fee):
        return min(self.priority_fee, self.max_fee - burn_fee)