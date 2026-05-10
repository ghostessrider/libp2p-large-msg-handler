import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from segmenter import SegmentEnvelope

MAX_SEGMENTS_PER_MSG = 5000
MAX_ACTIVE_MESSAGES = 10
STALE_TTL_SECONDS = 30.0

@dataclass
class ReassemblyResult:
    success: bool
    data: Optional[bytes]
    missing_indices: List[int]
    hash_verified: bool
    received_count: int
    total_segments: int

@dataclass
class _MessageContext:
    total_segments: int
    buffer: Dict[int, SegmentEnvelope] = field(default_factory=dict)
    last_activity: float = field(default_factory=time.monotonic)

    def touch(self):
        self.last_activity = time.monotonic()

class Reassembler:
    def __init__(self, on_progress=None):
        self._contexts: Dict[str, _MessageContext] = {}
        self._on_progress = on_progress

    def _evict_stale(self):
        now = time.monotonic()
        to_delete = [mid for mid, ctx in self._contexts.items() if now - ctx.last_activity > STALE_TTL_SECONDS]
        for mid in to_delete:
            del self._contexts[mid]

    def receive(self, envelope: SegmentEnvelope) -> bool:
        self._evict_stale()
        mid = envelope.msg_id

        if envelope.total_segments > MAX_SEGMENTS_PER_MSG:
            return False
        
        if mid not in self._contexts and len(self._contexts) >= MAX_ACTIVE_MESSAGES:
            return False

        if mid not in self._contexts:
            self._contexts[mid] = _MessageContext(total_segments=envelope.total_segments)

        ctx = self._contexts[mid]
        if not envelope.is_valid() or envelope.segment_index in ctx.buffer:
            return False

        ctx.buffer[envelope.segment_index] = envelope
        ctx.touch()
        
        if self._on_progress:
            self._on_progress(mid, ctx.buffer, ctx.total_segments)
        return True

    def reassemble(self, publisher_hash: str, msg_id: str = None) -> ReassemblyResult:
        if not self._contexts:
            return ReassemblyResult(False, None, [], False, 0, 0)

        target_id = msg_id or next(iter(self._contexts))
        ctx = self._contexts[target_id]
        
        missing = sorted(set(range(ctx.total_segments)) - set(ctx.buffer.keys()))
        if missing:
            return ReassemblyResult(False, None, missing, False, len(ctx.buffer), ctx.total_segments)

        data = b"".join(ctx.buffer[i].payload for i in range(ctx.total_segments))
        hash_ok = hashlib.sha256(data).hexdigest() == publisher_hash
        
        return ReassemblyResult(hash_ok, data if hash_ok else None, [], hash_ok, len(ctx.buffer), ctx.total_segments)