import random
import time
from dataclasses import dataclass
from typing import Callable, List, Optional
from segmenter import SegmentEnvelope

@dataclass
class NetworkCondition:
    loss_rate: float = 0.1
    max_latency_ms: float = 50.0
    seed: Optional[int] = None

    def __post_init__(self):
        self._rng = random.Random(self.seed)

    def should_drop(self) -> bool:
        return self._rng.random() < self.loss_rate

    def jitter(self) -> float:
        return self._rng.uniform(0, self.max_latency_ms) / 1000.0

class Publisher:
    def publish(self, segments: List[SegmentEnvelope], condition: NetworkCondition, on_deliver: Callable):
        scheduled = []
        for env in segments:
            if condition.should_drop():
                continue
            
            arrival_time = time.monotonic() + condition.jitter()
            scheduled.append((arrival_time, env))

        scheduled.sort(key=lambda x: x[0])

        for arrival, env in scheduled:
            wait = max(0, arrival - time.monotonic())
            if wait > 0:
                time.sleep(wait)
            on_deliver(env)