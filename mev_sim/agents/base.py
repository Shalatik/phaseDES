class Agent:
    def __init__(self, agent_id: str):
        self.id = agent_id
        self.known_txs = {}

    def on_event(self, event, engine):
        pass
