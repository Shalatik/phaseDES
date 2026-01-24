class MEVAgent:
    def __init__(self, mev_agent_id: int, tick: float):
        self.id = mev_agent_id
        self.known_txs = {}
        self.tick = tick

    def sync_mempool(self, engine):
        self.known_txs = dict(engine.state.mempool)

    def on_event(self, event, engine):
        pass
