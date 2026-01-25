from mev_sim.core.engine import Engine
from mev_sim.config.sim_constants import *
from mev_sim.config.blockchain_constants import *
from mev_sim.agents.user import User
from mev_sim.agents.builder import Builder
from mev_sim.agents.validator import Validator
import logging
from mev_sim.core.state import SimState
from mev_sim.objects.amm_pool import AMMPool
from dataclasses import replace

def run_sim(n_slots=1, n_users=3, user_tick=0.5, n_builders=1, builder_tick=3, n_validators=1):
    logger = logging.getLogger("mev_sim.run")
    
    state = SimState(
        amm_pool_a=AMMPool(str(AMM_POOL_A_NAME), int(AMM_POOL_A_ETH), int(AMM_POOL_A_USDC)),
        amm_pool_b=AMMPool(str(AMM_POOL_B_NAME), int(AMM_POOL_B_ETH), int(AMM_POOL_B_USDC)),
        burn_fee=INITIAL_BURN_FEE,
    )
    engine = Engine(state=state)
    
    # vytvoř usery
    users = {
        u: User(user_id=u, tick=user_tick)
        for u in range(n_users)
    }
    
    builders = {
        b: Builder(mev_agent_id=b, tick=builder_tick)
        for b in range(n_builders)
    }

    validators = {
        v: Validator(validator_id=v)
        for v in range(n_validators)
    }

    # sloty
    for s in range(n_slots):
        t0 = s * SLOT_LEN
        engine.schedule(t0, SLOT_START, {"slot": s})
        engine.schedule(t0 + SLOT_LEN, SLOT_END, {"slot": s})

    # start user ticků (t=0 pro všechny)
    for u in users:
        engine.schedule(0.0, USER_TICK, {"user_id": u})

    for b in builders:
        engine.schedule(0.0, BUILDER_TICK, {"builder_id": b})
        
    def handler(event, engine):
        if event.type == SLOT_START:
            logger.info(f"[t={engine.time:.3f}] {event.type} {event.payload}")
            return
        
        if event.type == SLOT_END:
            validators[0].on_event(event, engine, builders)
            logger.info(f"[t={engine.time:.3f}] {event.type} {event.payload}")
            return

        if event.type == USER_TICK:
            user_id = event.payload["user_id"]
            #logger.info(f"[t={engine.time:.3f}] USER_TICK user={user_id}")
            users[user_id].on_event(event, engine)
            return

        if event.type == SEND_TX:
            tx = event.payload["tx"]
            
            idTx = engine.state.mempool_next_index
            tx_with_index = replace(tx, real_index=idTx)
            engine.state.mempool_next_index += 1
            
            engine.state.mempool[tx_with_index.txid] = tx_with_index
            
            logger.info(f"[t={engine.time:.3f}] User {tx.sender} MEMPOOL_ADD idx={idTx} sent tx {tx_with_index.txid}")
            return
        
        if event.type == BUILDER_TICK:
            builder_id = event.payload["builder_id"]
            logger.info(f"[t={engine.time:.3f}] BUILDER_TICK builder={builder_id}")
            builders[builder_id].on_event(event, engine)
            return
        
        logger.info(f"[t={engine.time:.3f}] {event.type} {event.payload}")

    engine.run(until=n_slots * SLOT_LEN, handler=handler)
