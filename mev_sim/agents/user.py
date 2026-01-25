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
            # rozhodnutí: poslat tx?
            if self.rng.random() < P_SEND:
                fee = engine.state.burn_fee * 1.5
                target_amm_pool = engine.state.amm_pool_a.snapshot() if self.rng.random() < 0.5 else engine.state.amm_pool_b.snapshot()
                target_token = ETH_TO_USDC if self.rng.random() < 0.5 else USDC_TO_ETH
                
                if target_token == ETH_TO_USDC:
                    amount = int(self.rng.random() * ETH_TO_WEI)
                else:
                    amount = int(self.rng.random() * 1000 * USDC_MICRO)
                
                tx = Tx(
                    txid=f"{self.id}-tx{self.nonce}",
                    sender=self.id,
                    t_created=engine.time,
                    
                    tx_type="swap",
                    gas_used=GAS_SWAP,
                    priority_fee=1.0, #FIXME:
                    max_fee=fee,
                    nonce=self.nonce,
                    real_index=0,
                    status="pending",
                    
                    payload={
                        "amount": amount,
                        "token": target_token,
                        "amm_pool": target_amm_pool['name'],
                    },
                )
                self.nonce += 1
                engine.schedule(engine.time, SEND_TX, {"tx": tx})

            # vždy naplánuj další tick
            engine.schedule(engine.time + self.tick, USER_TICK_EVENT, {"user_id": self.user_id})
