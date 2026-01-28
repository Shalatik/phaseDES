from dataclasses import dataclass, replace
from typing import List, Protocol, Tuple, Optional
import random
from mev_sim.objects.amm_pool import AMMPool
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
		candidates.sort(key=lambda tx: (max(0, min(tx.priority_fee, tx.max_fee - burn_fee)), tx.real_index), reverse=True)
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


class SandwichOnlyStrategy:
	name = "sandwich_only"

	def build_block(self, mempool, burn_fee, state, slot, t, builder) -> List[Tx]:
		block = order_based_fee(mempool, burn_fee)

		victim = None
		for tx in block:
			if tx.tx_type == "swap": # and tx.sender.startswith("A"):

				front_run_token = tx.payload["token"]
				amm_pool = tx.payload["amm_pool"]
				victim_amount = tx.payload["amount"]
				if front_run_token == ETH_TO_USDC and victim_amount >= (0.7 * ETH_TO_WEI ):
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

		# ------------------------------------------------
		txid_front = f"B{builder.id}-tx{builder.nonce}"
		txid_back  = f"B{builder.id}-tx{builder.nonce+1}"

		payload_front = {"amount": amount, "token": front_run_token, "amm_pool": amm_pool}
		tx_front_run = Tx.make_transaction(txid_front, builder.id, t, "sandwich", victim.priority_fee + 0.5, burn_fee + 20, builder.nonce, payload_front)

		payload_back = {"amount": amount, "token": back_run_token, "amm_pool": amm_pool}
		tx_back_run = Tx.make_transaction(txid_back, builder.id, t, "sandwich", victim.priority_fee - 0.5, burn_fee + 20, builder.nonce + 1, payload_front)

		builder.nonce += 2

		block.append(tx_front_run)
		block.append(tx_back_run)
		return order_based_fee(block, burn_fee) #TODO: tohle asi neni idealni

class ArbitrageOnlyStrategy:
	name = "arbitrage_only"

	def build_block(self, mempool, burn_fee, state, slot, t, builder) -> List[Tx]:
		block = order_based_fee(mempool, burn_fee)

		amm_pool_a = state.amm_pool_a
		amm_pool_b = state.amm_pool_b

		buy_on_a_sell_on_b= calculate_optimal_arb(amm_pool_a, amm_pool_b)

		builder_account = state.accounts[builder.id]
 
		#-----------------------------
		buy_pool_name  = AMM_POOL_A_NAME if buy_on_a_sell_on_b else AMM_POOL_B_NAME
		sell_pool_name = AMM_POOL_B_NAME if buy_on_a_sell_on_b else AMM_POOL_A_NAME

		txid_arbitrage_A = f"B{builder.id}-tx{builder.nonce}"
		txid_arbitrage_B  = f"B{builder.id}-tx{builder.nonce+1}"

		payloadA = {"amount": builder_account.usdc_units * 0.1, "token": USDC_TO_ETH, "amm_pool": str(buy_pool_name)}
		tx_arbitrage_A = Tx.make_transaction(txid_arbitrage_A, builder.id, t, "arbitrage", 2.0, burn_fee + 20, builder.nonce, payloadA)

		payloadB = {"amount": 0, "token": ETH_TO_USDC, "amm_pool": str(sell_pool_name)}
		tx_arbitrage_B = Tx.make_transaction(txid_arbitrage_B, builder.id, t, "arbitrage", 2.0, burn_fee + 20, builder.nonce + 1, payloadB)

		builder.nonce += 2
		return [tx_arbitrage_A, tx_arbitrage_B] + block

@staticmethod
def pool_price_usdc_per_eth(pool):
	return pool.usdc_reserve / pool.eth_reserve

@staticmethod
def calculate_optimal_arb(amm_pool_a, amm_pool_b):
	#kolik usdc stoji 1eth v poolu
	price_a = pool_price_usdc_per_eth(amm_pool_a)
	price_b = pool_price_usdc_per_eth(amm_pool_b)

	#z ktereho poolu se bude obchodovat kam
	buy_on_a_sell_on_b = price_a < price_b
	pool_buy  = amm_pool_a if buy_on_a_sell_on_b else amm_pool_b
	pool_sell = amm_pool_b if buy_on_a_sell_on_b else amm_pool_a

	return buy_on_a_sell_on_b


class ArbitrageBackrunStrategy:
    name = "arbitrage_backrun"

    def __init__(self, cfg=None):
        cfg = cfg or {}
        self.min_profit_usdc = int(cfg.get("min_profit_usdc", 10) * USDC_MICRO)
        self.max_victims_to_try = int(cfg.get("max_victims_to_try", 30))

    def build_block(self, mempool, burn_fee, state, slot, t, builder) -> List[Tx]:
        block = order_based_fee(mempool, burn_fee)

        # vyber kandidáty victim swapů v baseline bloku
        victim_candidates = [ (i, tx) for i, tx in enumerate(block) if tx.tx_type == "swap" ]
        if not victim_candidates:
            return block

        # pro determinismus: zkus jen první N swapů v pořadí bloku
        victim_candidates = victim_candidates[: self.max_victims_to_try]

        best = None
        # best = (profit, victim_index, amount_usdc_in, buy_on_a_sell_on_b)
        for idx, victim in victim_candidates:
            # dry-run: post-state po victim tx
            pa = clone_pool(state.amm_pool_a)
            pb = clone_pool(state.amm_pool_b)
            apply_swap_to_copy(victim, pa, pb)

            buy_on_a_sell_on_b = calculate_optimal_arb(pa, pb)
            if profit > (best[0] if best else 0):
                best = (profit, idx, amount_usdc_in, buy_on_a_sell_on_b)

        if best is None:
            return block

        profit, victim_idx, amount_usdc_in, buy_on_a_sell_on_b = best
        if profit < self.min_profit_usdc or amount_usdc_in <= 0:
            return block

        buy_pool_name  = AMM_POOL_A_NAME if buy_on_a_sell_on_b else AMM_POOL_B_NAME
        sell_pool_name = AMM_POOL_B_NAME if buy_on_a_sell_on_b else AMM_POOL_A_NAME

        # 2-tx backrun arbitráž (USDC -> ETH, pak ETH -> USDC)
        txid_1 = f"B{builder.id}-tx{builder.nonce}"
        txid_2 = f"B{builder.id}-tx{builder.nonce + 1}"

        tx_arb_1 = Tx(
            txid=txid_1,
            sender=builder.id,
            t_created=t,
            tx_type="swap",
            gas_used=GAS_SWAP,
            priority_fee=2.0,
            max_fee=burn_fee + 20,
            nonce=builder.nonce,
            real_index=0,
            status="pending",
            payload={
                "amount": int(amount_usdc_in),
                "token": USDC_TO_ETH,
                "amm_pool": str(buy_pool_name),
            },
        )

        # amount=0 => validator použije account.last_received_amount (ETH z tx_arb_1)
        tx_arb_2 = Tx(
            txid=txid_2,
            sender=builder.id,
            t_created=t,
            tx_type="swap",
            gas_used=GAS_SWAP,
            priority_fee=2.0,
            max_fee=burn_fee + 20,
            nonce=builder.nonce + 1,
            real_index=0,
            status="pending",
            payload={
                "amount": 0,
                "token": ETH_TO_USDC,
                "amm_pool": str(sell_pool_name),
            },
        )

        builder.nonce += 2

        # vlož backrun hned ZA victim tx
        out = block[: victim_idx + 1] + [tx_arb_1, tx_arb_2] + block[victim_idx + 1 :]
        return out


def simulate_arb_profit(pool_buy, pool_sell, usdc_in):
	# buy: USDC -> ETH
	eth_out = pool_buy.calculate_out(usdc_in, USDC_TO_ETH)

	# sell: ETH -> USDC
	usdc_back = pool_sell.calculate_out(eth_out, ETH_TO_USDC)
	return usdc_back - usdc_in



def clone_pool(pool: AMMPool) -> AMMPool:
    return AMMPool(pool.name, int(pool.eth_reserve), int(pool.usdc_reserve))

def apply_swap_to_copy(tx: Tx, pool_a: AMMPool, pool_b: AMMPool) -> None:
    """Aplikuje swap tx na kopii poolů (stejná logika jako validator/AMM)."""
    token = str(tx.payload["token"])
    amm_pool_name = str(tx.payload["amm_pool"])
    amount_in = int(tx.payload.get("amount", 0))

    # vyber správný pool
    pool = pool_a if amm_pool_name == str(AMM_POOL_A_NAME) else pool_b

    # dry-run výstupu
    amount_out = pool.calculate_out(amount_in, token)
    if amount_out <= 0:
        return

    # update rezerv na kopii (stejně jako execute_swap)
    if token == ETH_TO_USDC:
        pool.eth_reserve += amount_in
        pool.usdc_reserve -= amount_out
    else:
        pool.usdc_reserve += amount_in
        pool.eth_reserve -= amount_out





