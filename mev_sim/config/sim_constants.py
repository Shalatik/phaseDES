
# ---------- MUTABLE -------------

SLOT_LEN = 12.0

SEED = 6
P_SEND = 0.2

N_SLOTS = 2
N_USERS = 5
USER_TICK_INTERVAL = 0.5
BUILDER_TICK_INTERVAL = 3
N_VALIDATORS = 1

ACTIVE_BUILDERS = [
	# {"type": "fee_order"},
	{"type": "sandwich_only"},
	# {"type": "arbitrage_only"},
	# {"type": "mev_play_it_safe"},
	# {"type": "mev_greedy"},
]
