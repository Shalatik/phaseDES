from dataclasses import dataclass
from typing import List, Protocol
import random
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

	def build_block(self, mempool, burn_fee, state, slot, t, builder) -> List[Tx]:
		return order_based_fee(mempool, burn_fee)


class SandwichOnlyStrategy:
	name = "sandwich_only"
 
	def build_block(self, mempool, burn_fee, state, slot, t, builder) -> List[Tx]:
		
		block = order_based_fee(mempool, burn_fee)
  
		for tx in block.txs:
			if tx.tx_type == "swap": # and tx.sender == "user"
				front_run_token = tx.payload["token"]
				amm_pool = tx.payload["amm_pool"]

				if front_run_token == ETH_TO_USDC:
					amount = int(self.rng.random() * ETH_TO_WEI * 5)
					back_run_token = USDC_TO_ETH
				else:
					amount = int(self.rng.random() * 1000 * USDC_MICRO * 5)
					back_run_token = ETH_TO_USDC

				tx_front_run = Tx(
					txid = f"B{builder.id}-tx{builder.nonce}",
					sender=builder.id,
					t_created=t,
					
					tx_type="swap",
					gas_used=GAS_SWAP,
					priority_fee=tx.priority_fee + 1.0,
					max_fee=state.burn_fee + 20,
					nonce=self.nonce,
					real_index=0,
					status="pending",
					
					payload={
						"amount": amount,
						"token": front_run_token,
						"amm_pool": amm_pool,
					},
				)

				tx_back_run = Tx(
					txid= f"B{builder.id}-tx{builder.nonce+1}",
					sender=builder.id,
					t_created=t,
					
					tx_type="swap",
					gas_used=GAS_SWAP,
					priority_fee=tx.priority_fee + 0.5,
					max_fee=state.burn_fee + 20,
					nonce=self.nonce + 1,
					real_index=0,
					status="pending",
					
					payload={
						"amount": amount,
						"token": back_run_token,
						"amm_pool": amm_pool,
					},
				)
                
				block.append(tx_front_run)
				block.append(tx_back_run)
    
				out = []
				inserted = False
				for tx in block_txs:
					if (not inserted) and tx.txid == victim.txid:
						out.append(tx_front_run)
						out.append(tx)          # victim
						out.append(tx_back_run)
						inserted = True
					else:
						out.append(tx)
    
				self.nonce += 2
				break # Jeden útok na slot stačí zatím TODO:
		return block

@staticmethod
def order_based_fee(mempool, burn_fee):
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