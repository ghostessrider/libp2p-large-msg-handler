import argparse
import sys
import os
from mesh_network import NetworkCondition, Publisher
from reassembler import Reassembler
from segmenter import Segmenter

def progress_bar(msg_id, buffer, total):
    received = sum(1 for idx in buffer if idx < total)
    bar = "".join(["[#]" if i in buffer else "[ ]" for i in range(min(total, 20))])
    if total > 20: bar += "..."
    pct = int((received / total) * 100)
    print(f"\rProgress: {bar} {pct}% ({received}/{total})", end="", flush=True)

def run_simulation(args):
    payload = os.urandom(args.payload_kb * 1024)
    p_hash = Segmenter.message_hash(payload)
    
    seg = Segmenter(segment_size=args.segment_size, redundancy_factor=args.redundancy)
    envelopes = seg.segment(payload)
    msg_id = envelopes[0].msg_id

    condition = NetworkCondition(loss_rate=args.loss, max_latency_ms=args.jitter)
    reassembler = Reassembler(on_progress=progress_bar if not args.no_progress else None)

    print(f"Simulation started: {len(payload)} bytes, {len(envelopes)} envelopes")
    Publisher().publish(envelopes, condition, reassembler.receive)
    print("\nInitial reassembly attempt...")
    
    res = reassembler.reassemble(p_hash, msg_id)
    if not res.success and not args.no_retry:
        missing_envs = [e for e in envelopes if e.segment_index in res.missing_indices]
        Publisher().publish(missing_envs, NetworkCondition(0, 0), reassembler.receive)
        res = reassembler.reassemble(p_hash, msg_id)

    print(f"Final Status: {'Success' if res.success else 'Failed'}")
    print(f"Integrity Verified: {res.hash_verified}")
    return res.success

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--loss", type=float, default=0.1)
    parser.add_argument("--jitter", type=float, default=50.0)
    parser.add_argument("--segment-size", type=int, default=512)
    parser.add_argument("--payload-kb", type=int, default=8)
    parser.add_argument("--redundancy", type=float, default=0.0)
    parser.add_argument("--no-retry", action="store_true")
    parser.add_argument("--no-progress", action="store_true")
    args = parser.parse_args()
    sys.exit(0 if run_simulation(args) else 1)