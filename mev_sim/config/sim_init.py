from mev_sim.agents.builder_strategies import *

# ---------- IMMUTABLE -------------

STRATEGY_REGISTRY = {
	"fee_order": lambda cfg: OrderBasedFeeStrategy(),
	"sandwich_only": lambda cfg: SandwichOnlyStrategy(),
	# "arbitrage_only": lambda cfg: ArbitrageOnlyStrategy(),
	# "mev_play_it_safe": lambda cfg: MevPlayItSafe(),
	# "mev_greedy": lambda cfg: MevGreedyStrategy(),
}

SLOT_START = "SLOT_START"
SLOT_END   = "SLOT_END"
SEND_TX    = "SEND_TX"
TX_ARRIVE  = "TX_ARRIVE"
USER_TICK_EVENT  = "USER_TICK"
BUILDER_TICK_EVENT = "BUILDER_TICK"