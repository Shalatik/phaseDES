# mev_sim/domain/amm.py
from dataclasses import dataclass

@dataclass
class AMMPool:
    name: str
    eth_reserve: int
    usdc_reserve: int

    def snapshot(self) -> tuple[str, int, int]:
        return self.name, self.eth_reserve, self.usdc_reserve

    # sem si dáš swap funkce, pricing atd.
