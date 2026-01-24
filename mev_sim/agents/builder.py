from .base import Agent

class Builder(Agent):
    def __init__(self, agent_id):
        super().__init__(agent_id)
        self.best_block = []

    def rebuild(self):
        self.best_block = list(self.known_txs.values())
