import random
from dataclasses import dataclass
from mev_sim.config.sim_constants import *
from mev_sim.config.sim_init import *
from mev_sim.config.blockchain_constants import *
from mev_sim.objects.transaction import Tx


class User:
    def __init__(self, user_id: int, tick: float):
        self.user_id = user_id
        self.id = f"A{user_id}"
        self.tick = tick
        self.nonce = 0

        self.rng = random.Random(SEED + user_id)

    def on_event(self, event, engine):
        if event.type == USER_TICK_EVENT:
            
            if self.rng.random() < P_SEND:
                fee = engine.state.burn_fee * 1.5
                target_amm_pool = engine.state.amm_pool_a.snapshot() if self.rng.random() < 0.5 else engine.state.amm_pool_b.snapshot()
                target_token = ETH_TO_USDC if self.rng.random() < 0.5 else USDC_TO_ETH
                
                if target_token == ETH_TO_USDC:
                    amount = int(self.rng.random() * ETH_TO_WEI)
                else:
                    amount = int(self.rng.random() * 1000 * USDC_MICRO)
                
                priority_fee = int((0.5 + 2.0 * self.rng.random()) * GWEI_TO_WEI)
                
                payload={"amount": amount,"token": target_token,"amm_pool": target_amm_pool['name']}
                burn_fee = engine.state.burn_fee + priority_fee + int(5 * GWEI_TO_WEI)
		        
                tx = Tx.make_transaction(f"{self.id}-tx{self.nonce}", self.id, engine.time, "swap", priority_fee, burn_fee, self.nonce, payload)

                self.nonce += 1
                engine.schedule(engine.time, SEND_TX, {"tx": tx})

            #naplanovani dalsiho ticku
            engine.schedule(engine.time + self.tick, USER_TICK_EVENT, {"user_id": self.user_id})
