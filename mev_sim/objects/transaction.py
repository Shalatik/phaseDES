from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from mev_sim.config.blockchain_constants import *


@dataclass()
class Tx:
    txid: str
    sender: str
    t_created: float

    tx_type: str
    gas_used: int
    priority_fee: int
    max_fee: int
    nonce: int
    status: str
    real_index: Optional[int] = None

    payload: Dict[str, Any] = field(default_factory=dict)
    
    def effective_priority_fee(self, burn_fee):
        return min(self.priority_fee, self.max_fee - burn_fee)
    
    def make_transaction(txid, id, t, t_type, priority_fee, max_fee, nonce, payload):
        tx = Tx(
            txid=txid,
            sender=id,
            t_created=t,
            tx_type=t_type,
            gas_used=GAS_SWAP,
            priority_fee=priority_fee,
            max_fee=max_fee,
            nonce=nonce,
            real_index=0,
            status="pending",
            payload=payload,
        )
        return tx