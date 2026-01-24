import heapq
import itertools
from .event import Event

class Engine:
    def __init__(self, state):
        self.time = 0.0
        self.state = state
        self._queue = []
        self._seq = itertools.count()
        self.agents = {}

    def schedule(self, time: float, etype: str, payload=None):
        event = Event(time, next(self._seq), etype, payload)
        heapq.heappush(self._queue, event)

    def run(self, until: float, handler):
        while self._queue:
            ev = heapq.heappop(self._queue)
            if ev.time > until:
                break
            self.time = ev.time
            handler(ev, self)
