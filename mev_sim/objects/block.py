from dataclasses import dataclass, field
from typing import List

@dataclass
class Block:
    slot: int
    builder_id: str
    t_built: float
    txs: List[Tx] = field(default_factory=list)

    def score(self) -> float:
        # placeholder: později fee/profit
        return float(len(self.txs))
