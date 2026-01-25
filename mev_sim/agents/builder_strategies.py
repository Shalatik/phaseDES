from dataclasses import dataclass
from typing import List, Protocol
from mev_sim.objects.transaction import Tx
from collections import defaultdict
from mev_sim.config.sim_constants import *
from mev_sim.config.blockchain_constants import *

class BuilderStrategy(Protocol):
	name: str
	
	def build_block(self, mempool: List[Tx], burn_fee: int, state, slot: int, t: float) -> List[Tx]:
		pass

class OrderBasedFeeStrategy:
	name = "fee_order"

	def build_block(self, mempool, burn_fee, state, slot, t) -> List[Tx]:
		valid_txs = [tx for tx in mempool if tx.max_fee >= burn_fee]
	
		by_sender = defaultdict(list)
		for tx in valid_txs:
			by_sender[tx.sender].append(tx)
		for s in by_sender:
			by_sender[s].sort(key=lambda x: x.nonce)

		final_block = []
		current_gas = 0
		candidates = [by_sender[s][0] for s in by_sender if by_sender[s]]

		while candidates:
			candidates.sort(key=lambda x: (x.effective_priority_fee(burn_fee), x.real_index), reverse=True)
			best_tx = candidates.pop(0)

			if current_gas + best_tx.gas_used <= BLOCK_GAS_LIMIT:
				final_block.append(best_tx)
				current_gas += best_tx.gas_used
				
				sender = best_tx.sender
				tx_list = by_sender[sender]
				current_idx = tx_list.index(best_tx)
				if current_idx + 1 < len(tx_list):
					candidates.append(tx_list[current_idx + 1])
		return final_block