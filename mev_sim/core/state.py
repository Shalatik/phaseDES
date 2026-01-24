# mev_sim/sim/state.py
from dataclasses import dataclass
from mev_sim.objects.amm_pool import AMMPool

@dataclass
class SimState:
    amm_pool_a: AMMPool
    amm_pool_b: AMMPool
    burn_fee: float  # wei
