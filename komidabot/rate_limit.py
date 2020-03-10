import time
from collections import deque
from datetime import datetime


class Limiter:
    def __init__(self, max_rate: int):
        self.max_rate = max_rate
        self.last_times = deque()

    def __call__(self):
        now = datetime.now()

        if len(self.last_times) < self.max_rate:
            self.last_times.append(now)
            return

        delta = (now - self.last_times.popleft()).total_seconds()

        if delta < 1:
            time.sleep(1.0 - delta)

        self.last_times.append(now)
