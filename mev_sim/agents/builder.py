from .base import MEVAgent
import random
from dataclasses import dataclass
from mev_sim.config.sim_constants import *
from mev_sim.config.blockchain_constants import *
from mev_sim.objects.transaction import Tx
from mev_sim.objects.block import Block
from collections import defaultdict

class Builder(MEVAgent):
    def __init__(self, mev_agent_id, tick):
        super().__init__(mev_agent_id=mev_agent_id, tick=tick)
        self.best_block = Block(slot=-1, builder_id=self.id, t_built=0.0, txs=[])
        self.nonce = 0

    def on_event(self, event, engine):
        if event.type == BUILDER_TICK:
            
            self.sync_mempool(engine)
            mempool = list(self.known_txs.values())
            
            #prepocita nejlepsi block
            self.best_block = self.order_based_fee(mempool, engine.state.burn_fee)
            #prida svoje transakce
        
        engine.schedule(engine.time + self.tick, BUILDER_TICK, {"builder_id": self.id})

    @staticmethod
    def order_based_fee(mempool, burn_fee):
        valid_txs = [tx for tx in mempool if tx.max_fee >= burn_fee]
    
        by_sender = defaultdict(list)
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