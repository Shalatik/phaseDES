from .base import MEVAgent
import random
from dataclasses import dataclass
from mev_sim.config.sim_constants import *
from mev_sim.config.blockchain_constants import *
from mev_sim.objects.transaction import Tx
from mev_sim.objects.block import Block
from collections import defaultdict
from mev_sim.agents.builder_strategies import BuilderStrategy

class Builder(MEVAgent):
    def __init__(self, mev_agent_id, tick, strategy: BuilderStrategy):
        super().__init__(mev_agent_id=mev_agent_id, tick=tick)
        self.best_block = Block(slot=-1, builder_id=self.id, t_built=0.0, txs=[])
        self.nonce = 0
        self.strategy = strategy

    def on_event(self, event, engine, slot):
        if event.type == BUILDER_TICK_EVENT:
            
            self.sync_mempool(engine)
            mempool = list(self.known_txs.values())
            
            #prepocita nejlepsi block
            # final_block = self.order_based_fee(mempool, engine.state.burn_fee)
            # self.best_block = Block(slot=slot, builder_id=self.id, t_built=engine.time, txs=final_block)
            
            txs = self.strategy.build_block(mempool, engine.state.burn_fee, engine.state, slot, engine.time)
            self.best_block = Block(slot=slot, builder_id=self.id, t_built=engine.time, txs=txs)
            
            #prida svoje transakce
        
        engine.schedule(engine.time + self.tick, BUILDER_TICK_EVENT, {"builder_id": self.id})
