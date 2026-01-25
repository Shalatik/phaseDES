from mev_sim.agents.builder_strategies import *

# ---------- IMMUTABLE -------------

SLOT_LEN = 12.0

SEED = 6
P_SEND = 0.2

N_SLOTS = 2
N_USERS = 5
USER_TICK_INTERVAL = 0.5
N_BUILDERS = 1
BUILDER_TICK_INTERVAL = 3
N_VALIDATORS = 1

STRATEGY_REGISTRY = {
	"fee_order": lambda cfg: OrderBasedFeeStrategy(),
	# "sandwich_only": lambda cfg: SandwichOnlyStrategy(),
	# "arbitrage_only": lambda cfg: ArbitrageOnlyStrategy(),
	# "mev_greedy": lambda cfg: MevGreedyStrategy(),
}

# ---------- IMMUTABLE -------------

ACTIVE_BUILDERS = [
	{"type": "fee_order"},
	# {"type": "sandwich_only"},
	# {"type": "arbitrage_only"},
	# {"type": "mev_greedy"},
]

SLOT_START = "SLOT_START"
SLOT_END   = "SLOT_END"
SEND_TX    = "SEND_TX"
TX_ARRIVE  = "TX_ARRIVE"
USER_TICK_EVENT  = "USER_TICK"
BUILDER_TICK_EVENT = "BUILDER_TICK"

