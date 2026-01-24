from mev_sim.core.engine import Engine
from mev_sim.config.sim_constants import *
from mev_sim.agents.user import User
import logging

def run_sim(n_slots=1, n_users=3, user_tick=0.5):
    engine = Engine()
    logger = logging.getLogger("mev_sim.run")
    
    # vytvoř usery
    users = {
        u: User(user_id=u, tick=user_tick)
        for u in range(n_users)
    }

    # sloty
    for s in range(n_slots):
        t0 = s * SLOT_LEN
        engine.schedule(t0, SLOT_START, {"slot": s})
        engine.schedule(t0 + SLOT_LEN, SLOT_END, {"slot": s})

    # start user ticků (t=0 pro všechny)
    for u in users:
        engine.schedule(0.0, USER_TICK, {"user_id": u})

    def handler(event, engine):
        # 1) globální eventy
        if event.type in (SLOT_START, SLOT_END):
            logger.info(f"[t={engine.time:.3f}] {event.type} {event.payload}")
            return

        # 2) eventy mířící na usery
        if event.type == USER_TICK:
            user_id = event.payload["user_id"]
            #logger.info(f"[t={engine.time:.3f}] USER_TICK user={user_id}")
            users[user_id].on_event(event, engine)
            return

        # 3) debug výpis (zatím)
        if event.type == SEND_TX:
            tx = event.payload["tx"]
            logger.info(f"[t={engine.time:.3f}] User {tx.sender} sent tx {tx.txid}")
            return

        logger.info(f"[t={engine.time:.3f}] {event.type} {event.payload}")

    engine.run(until=n_slots * SLOT_LEN, handler=handler)
