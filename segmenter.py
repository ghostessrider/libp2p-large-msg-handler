import hashlib
import math
import uuid
from dataclasses import dataclass, field
from typing import List

@dataclass(frozen=True)
class SegmentEnvelope:
    msg_id: str
    total_segments: int
    segment_index: int
    payload_hash: str
    payload: bytes
    is_parity: bool = False

    def is_valid(self) -> bool:
        return hashlib.sha256(self.payload).hexdigest() == self.payload_hash

def _xor_bytes(*chunks: bytes) -> bytes:
    target_len = max(len(c) for c in chunks)
    result = bytearray(target_len)
    for chunk in chunks:
        padded = chunk.ljust(target_len, b"\x00")
        for i, byte in enumerate(padded):
            result[i] ^= byte
    return bytes(result)

@dataclass
class Segmenter:
    segment_size: int = 512
    redundancy_factor: float = 0.0
    parity_window: int = 5
    _msg_id: str = field(default_factory=lambda: str(uuid.uuid4()), init=False)

    def segment(self, data: bytes) -> List[SegmentEnvelope]:
        if not data:
            raise ValueError("Empty payload")

        self._msg_id = str(uuid.uuid4())
        total_primary = math.ceil(len(data) / self.segment_size)
        primary_chunks = []
        primary_envs = []

        for idx in range(total_primary):
            start = idx * self.segment_size
            chunk = data[start : start + self.segment_size]
            primary_chunks.append(chunk)
            primary_envs.append(SegmentEnvelope(
                msg_id=self._msg_id,
                total_segments=total_primary,
                segment_index=idx,
                payload_hash=hashlib.sha256(chunk).hexdigest(),
                payload=chunk
            ))

        parity_envs = []
        if self.redundancy_factor > 0:
            num_parity = max(1, math.ceil(total_primary * self.redundancy_factor))
            stride = max(1, total_primary // num_parity)
            for p_idx in range(num_parity):
                window_start = (p_idx * stride) % total_primary
                selected = [primary_chunks[(window_start + k) % total_primary] for k in range(self.parity_window)]
                p_payload = _xor_bytes(*selected)
                parity_envs.append(SegmentEnvelope(
                    msg_id=self._msg_id,
                    total_segments=total_primary,
                    segment_index=total_primary + p_idx,
                    payload_hash=hashlib.sha256(p_payload).hexdigest(),
                    payload=p_payload,
                    is_parity=True
                ))

        return primary_envs + parity_envs

    @staticmethod
    def message_hash(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()