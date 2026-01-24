from dataclasses import dataclass, field
from typing import List
from mev_sim.objects.transaction import Tx

@dataclass
class Block:
    slot: int
    builder_id: int
    t_built: float
    txs: List[Tx] = field(default_factory=list)

    def score(self) -> float:
        # placeholder: později fee/profit
        return float(len(self.txs))
