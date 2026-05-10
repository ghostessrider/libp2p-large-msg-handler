# Gossipsub 1.4: Large Message SAR Simulation

[cite_start]This project is a technical Proof of Concept (PoC) for the Segmentation-Reassembly (SAR) model proposed in the libp2p Gossipsub 1.4 Candidate Recommendation[cite: 11, 12].

As an Electrical Engineering student at IIT Bhilai, I developed this simulation to explore the mechanics of decentralized large-payload dissemination. [cite_start]The focus is on maintaining node stability and data integrity in high-churn environments where packet loss and out-of-order delivery are the norms rather than exceptions[cite: 1, 4].

---

## Technical Overview

Gossipsub is traditionally optimized for small messages. [cite_start]Handling large payloads (e.g., AI model updates or state snapshots) requires a specialized layer to prevent network congestion and memory exhaustion[cite: 1, 12]. [cite_start]This simulation implements that layer through a three-stage SAR lifecycle[cite: 1].

### 1. Segmentation (The Packager)
The payload is divided into fixed-size envelopes. [cite_start]Each envelope is self-describing, allowing any receiving node to understand the context of the chunk without needing a handshake[cite: 1, 14].
* [cite_start]**Wire Format**: Implements a custom header including `msg_id`, `total_segments`, and `segment_index`[cite: 13, 16].
* [cite_start]**Redundancy**: Includes an optional XOR-based parity layer to provide basic Forward Error Correction (FEC), reducing the need for expensive re-fetches[cite: 10, 35].

### 2. Mesh Simulation (The Environment)
A P2P mesh is inherently chaotic. The `mesh_network.py` script replicates this by simulating:
* [cite_start]**Packet Loss**: Randomly drops segments to test gap detection and recovery[cite: 4].
* [cite_start]**Jitter**: Introduces variable latency, forcing out-of-order arrival (e.g., Segment #5 arriving before Segment #1)[cite: 4].

### 3. Reassembly (The Defensive Engine)
The reassembler acts as the "brain" of the subscriber node. [cite_start]It doesn't just stitch data together; it defends the node[cite: 1, 15].
* [cite_start]**Resource Guarding**: Hard limits on segment counts and active message contexts prevent heap exhaustion during potential DoS probes[cite: 1, 10].
* [cite_start]**Stale Eviction**: Incomplete transfers are automatically evicted after a 30-second TTL to reclaim memory[cite: 10, 47].
* [cite_start]**Tiered Verification**: Checks integrity at the segment level (Tier 1) and the final reassembled message level (Tier 2) using SHA-256[cite: 1, 28].

---

## Project Structure

* [cite_start]`segmenter.py`: Logic for chunking data and generating parity segments[cite: 10].
* [cite_start]`reassembler.py`: The state machine for buffering, gap detection, and reconstruction[cite: 10].
* [cite_start]`mesh_network.py`: The network simulator for churn and latency[cite: 4, 10].
* [cite_start]`demo.py`: A CLI tool to run the full lifecycle and view real-time progress[cite: 1, 10].
* [cite_start]`v1_4_spec.proto`: A formal Protobuf schema defining the intended wire format for cross-language interoperability between Python, Nim, and Go[cite: 1, 11].

---

## Design Rationale

Standard P2P implementations often struggle with memory management when messages get large. [cite_start]By implementing Byzantine-resistant guards and SAR-specific indexing, this PoC demonstrates a path toward a "Candidate Recommendation" status for the Gossipsub 1.4 spec[cite: 10, 12]. It prioritizes system-level efficiency—a mindset shaped by my background in computer architecture and hardware-software interfacing.

## Usage

Run a simulation with 10% packet loss and 10% redundancy:
```bash
python demo.py --loss 0.1 --redundancy 0.1