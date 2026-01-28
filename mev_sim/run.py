from mev_sim.core.engine import Engine
from mev_sim.config.sim_constants import *
from mev_sim.config.blockchain_constants import *
from mev_sim.config.sim_init import *
from mev_sim.agents.user import User
from mev_sim.agents.builder import Builder
from mev_sim.agents.validator import Validator
import logging
from mev_sim.core.state import SimState
from mev_sim.objects.amm_pool import AMMPool
from dataclasses import replace
from mev_sim.objects.account import Account
from mev_sim.utils.snapshots import format_pools, format_users
from mev_sim.agents.builder_strategies import *

def run_sim():
    logger = logging.getLogger("mev_sim.run")
    
    state = SimState(
        amm_pool_a=AMMPool(str(AMM_POOL_A_NAME), int(AMM_POOL_A_ETH), int(AMM_POOL_A_USDC)),
        amm_pool_b=AMMPool(str(AMM_POOL_B_NAME), int(AMM_POOL_B_ETH), int(AMM_POOL_B_USDC)),
        burn_fee=INITIAL_BURN_FEE,
    )
    engine = Engine(state=state)
    
    # sloty
    for s in range(N_SLOTS):
        t0 = s * SLOT_LEN
        engine.schedule(t0, SLOT_START, {"slot": s})
        engine.schedule(t0 + SLOT_LEN, SLOT_END, {"slot": s})

    users, builders, validators = init_agents(engine)
        
    user_ids = [users[u].id for u in users] 
    builder_ids = [builders[b].id for b in builders]    
       
        
    def handler(event, engine):
        if event.type == SLOT_START:
            slot = event.payload["slot"]
            logger.info(f"[t={engine.time:.3f}] SLOT_START slot={slot}")
            logger.info(f"[t={engine.time:.3f}] POOLS_START {format_pools(engine.state)}")
            logger.info(f"[t={engine.time:.3f}] USERS_START {format_users(engine.state, user_ids)}")
            logger.info(f"[t={engine.time:.3f}] BUILDER_START {format_users(engine.state, builder_ids)}")
            return
        
        if event.type == SLOT_END:
            slot = event.payload["slot"]
            validators[0].on_event(event, engine, builders)
            logger.info(f"[t={engine.time:.3f}] SLOT_END slot={slot}")
            logger.info(f"[t={engine.time:.3f}] POOLS_END {format_pools(engine.state)}")
            logger.info(f"[t={engine.time:.3f}] USERS_END {format_users(engine.state, user_ids)}")
            logger.info(f"[t={engine.time:.3f}] BUILDER_END {format_users(engine.state, builder_ids)}")
            logger.info(f"----------------------------------------------------------")
            return

        if event.type == USER_TICK_EVENT:
            user_id = event.payload["user_id"]
            users[user_id].on_event(event, engine)
            return

        if event.type == SEND_TX:
            tx = event.payload["tx"]
            
            idTx = engine.state.mempool_next_index
            tx_with_index = replace(tx, real_index=idTx)
            
            add_to_mempool(engine.state, tx_with_index)
            
            logger.info(f"[t={engine.time:.3f}] User {tx.sender} MEMPOOL_ADD idx={idTx} sent tx {tx_with_index.txid}")
            return
        
        if event.type == BUILDER_TICK_EVENT:
            slot = int(engine.time // SLOT_LEN)
            builder_id = event.payload["builder_id"]
            logger.info(f"[t={engine.time:.3f}] BUILDER_TICK builder={builder_id}")
            builders[builder_id].on_event(event, engine, slot)
            return
        
        logger.info(f"[t={engine.time:.3f}] {event.type} {event.payload}")

    engine.run(until=N_SLOTS * SLOT_LEN, handler=handler)


def init_agents(engine):
    users = {
        u: User(user_id=u, tick=USER_TICK_INTERVAL)
        for u in range(N_USERS)
    }
    
    builders = {}
    for b, cfg in enumerate(ACTIVE_BUILDERS):
        strat = STRATEGY_REGISTRY[cfg["type"]](cfg)
        builders[b] = Builder(mev_agent_id=b, tick=BUILDER_TICK_INTERVAL, strategy=strat)

    validators = {
        v: Validator(validator_id=v)
        for v in range(N_VALIDATORS)
    }

    for u in users:
        engine.schedule(0.0, USER_TICK_EVENT, {"user_id": u})

    for b in builders:
        engine.schedule(0.0, BUILDER_TICK_EVENT, {"builder_id": b})
        

    for u in users.values():
        engine.state.accounts[u.id] = Account(
            eth_wei=USER_WEI,    
            usdc_units=USER_USDC_MICRO,  
            nonce=0
        )

    for b in builders.values():
        engine.state.accounts[b.id] = Account(
            eth_wei=BUILDER_WEI,
            usdc_units=BUILDER_USDC_MICRO,
            nonce=0
        )
        
    return users, builders, validators

def add_to_mempool(state, tx_with_index):
    mempool = state.mempool

    if len(mempool) >= MEMPOOL_CAPACITY:
        lowest_fee_tx = min(
            mempool.values(),
            key=lambda tx: (tx.max_fee, tx.txid)
        )

        if tx_with_index.max_fee > lowest_fee_tx.max_fee:
            del mempool[lowest_fee_tx.txid]
            mempool[tx_with_index.txid] = tx_with_index
    else:
        mempool[tx_with_index.txid] = tx_with_index
    state.mempool_next_index += 1


