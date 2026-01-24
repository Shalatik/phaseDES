import random
from dataclasses import dataclass
from mev_sim.config.sim_constants import USER_TICK, SEND_TX
from mev_sim.config.sim_constants import *
from mev_sim.objects.transaction import Tx

class User:
    def __init__(self, user_id: int, tick: float):
        self.user_id = user_id
        self.id = f"A{user_id}"
        self.tick = tick

        # důležité: per-user RNG => determinismus i když přidáš další agenty/eventy
        self.rng = random.Random(SEED + user_id)
        self.tx_counter = 0

    def on_event(self, event, engine):
        if event.type == USER_TICK:
            # rozhodnutí: poslat tx?
            if self.rng.random() < P_SEND:
                tx = Tx(
                    txid=f"{self.id}-tx{self.tx_counter}",
                    sender=self.id,
                    t_created=engine.time
                )
                self.tx_counter += 1
                engine.schedule(engine.time, SEND_TX, {"tx": tx})

            # vždy naplánuj další tick
            engine.schedule(engine.time + self.tick, USER_TICK, {"user_id": self.user_id})
