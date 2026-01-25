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
		# baseline: txs seřazené podle fee (předpoklad: vrací list[Tx])
		block = order_based_fee(mempool, burn_fee)

		# najdi první user swap (nebo si vyber jinak)
		victim = None
		for tx in block:
			if tx.tx_type == "swap": # and tx.sender.startswith("A"):  # nebo jak poznáš usery
				
				front_run_token = tx.payload["token"]
				amm_pool = tx.payload["amm_pool"]
				victim_amount = tx.payload["amount"]
				if front_run_token == ETH_TO_USDC and victim_amount >= (0.7 * ETH_TO_WEI ): #TODO: vyplati se?
					amount = int(builder.rng.random() * ETH_TO_WEI * 5)
					back_run_token = USDC_TO_ETH
					victim = tx
					break
				elif victim_amount >= (0.7 * 1000 * USDC_MICRO):
					amount = int(builder.rng.random() * 1000 * USDC_MICRO * 5)
					back_run_token = ETH_TO_USDC
					victim = tx
					break
				else:
					continue

		if victim is None:
			return block

		# unikátní txid + nonce
		txid_front = f"B{builder.id}-tx{builder.nonce}"
		txid_back  = f"B{builder.id}-tx{builder.nonce+1}"

		tx_front_run = Tx(
			txid=txid_front,
			sender=builder.id,
			t_created=t,
			tx_type="swap",
			gas_used=GAS_SWAP,
			priority_fee=victim.priority_fee + 0.5,
			max_fee=burn_fee + 20,
			nonce=builder.nonce,
			real_index=0,
			status="pending",
			payload={"amount": amount, "token": front_run_token, "amm_pool": amm_pool},
		)

		tx_back_run = Tx(
			txid=txid_back,
			sender=builder.id,
			t_created=t,
			tx_type="swap",
			gas_used=GAS_SWAP,
			priority_fee=victim.priority_fee - 0.5,
			max_fee=burn_fee + 20,
			nonce=builder.nonce + 1,
			real_index=0,
			status="pending",
			payload={"amount": amount, "token": back_run_token, "amm_pool": amm_pool},
		)

		builder.nonce += 2

		block.append(tx_front_run)
		block.append(tx_back_run)
		return order_based_fee(block, burn_fee) #TODO: tohle asi neni idealni


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