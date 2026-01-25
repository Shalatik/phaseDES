import random
import logging
from mev_sim.config.sim_constants import *
from mev_sim.config.blockchain_constants import *
from mev_sim.config.sim_constants import SLOT_END
from mev_sim.core.engine import Engine

logger = logging.getLogger("mev_sim.agent.validator")

class Validator:
	def __init__(self, validator_id: int):
		self.validator_id = validator_id
		self.rng = random.Random(SEED)

	def on_event(self, event, engine, builders: dict):
		if event.type == SLOT_END:
			slot = event.payload["slot"]

			# vytáhni buildery z registry
			builder_keys = list(builders.keys())
			chosen_key = self.rng.choice(builder_keys)
			chosen_builder = builders[chosen_key]

			block = chosen_builder.best_block

			logger.info(
				f"[t={engine.time:.3f}] VALIDATOR slot={slot} chose={chosen_builder.id} "
				f"block_len={len(block.txs) if hasattr(block, 'txs') else len(block)}"
			)

			gas_used_in_block = self.execute_block(block, engine)
			engine.state.burn_fee = self.calculate_new_burn_fee(engine.state.burn_fee, gas_used_in_block)
			self.update_mempool(block, engine)


	def update_mempool(self, block, engine):
		for tx in block:
			engine.state.mempool.pop(tx.txid, None)

	def execute_block(self, block, engine):
		gas_used_in_block = 0
		success_count = 0
		for tx in block:
			status = self.execute_transaction(tx, engine)
			if status == "success":
				success_count += 1
			if tx.status != "reverted_no_gas":
				gas_used_in_block += tx.gas_used
		return gas_used_in_block

	def calculate_new_burn_fee(self, current_burn_fee, gas_used):
		delta = gas_used - BLOCK_TARGET_GAS
		change = current_burn_fee * (delta / BLOCK_TARGET_GAS) * BURN_FEE_MAX_CHANGE
		return max(MIN_BURN_FEE, current_burn_fee + change)

	def execute_transaction(self, tx, engine):
		agent = tx.sender

		tip_per_gas_gwei = tx.effective_priority_fee(engine.state.burn_fee)
		burned_wei = int(tx.gas_used * engine.state.burn_fee * WEI_TO_GWEI)
		validator_tip_wei = int(tx.gas_used * tip_per_gas_gwei * WEI_TO_GWEI)
		cost_wei = burned_wei + validator_tip_wei

		if agent.inventory_eth_wei < cost_wei:
			tx.status = "reverted_no_gas"
			return tx.status



		agent.inventory_eth_wei -= cost_wei


		target_amount = int(tx.payload['amount'])

		if target_amount == 0:
			target_amount = agent.last_received_amount

		target_token = tx.payload['token']
		amm_pool = engine.state.amm_pool_a if tx.payload["amm_pool"] == AMM_POOL_A_NAME else engine.state.amm_pool_b

		if target_token == ETH_TO_USDC and agent.inventory_eth_wei < target_amount:
			tx.status = "reverted_insufficient_funds"
			return tx.status
		if target_token == USDC_TO_ETH and agent.inventory_usdc_units < target_amount:
			tx.status = "reverted_insufficient_funds"
			return tx.status

		success, out = amm_pool.execute_swap(target_amount, target_token, tx.min_out)

		if success:
			if target_token == ETH_TO_USDC:
				agent.inventory_eth_wei -= target_amount
				agent.inventory_usdc_units += out
			else:
				agent.inventory_usdc_units -= target_amount
				agent.inventory_eth_wei += out

			agent.last_received_amount = out
			tx.status = "success"
		else:
			tx.status = "reverted_slippage"

		return tx.status



