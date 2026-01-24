import random
import logging
from mev_sim.config.sim_constants import *
from mev_sim.config.blockchain_constants import *
from mev_sim.config.sim_constants import SLOT_END

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


