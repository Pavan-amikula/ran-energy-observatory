"""Deterministic packet scheduler and explicitly illustrative radio power model.

Grid cells are PRB x average OFDM symbol, not individual resource elements.
No waveform, HARQ, interference, RF hardware or proprietary feature is emulated.
"""
from dataclasses import dataclass, asdict
from typing import Literal
import math
import csv
from pathlib import Path
import numpy as np
from pydantic import BaseModel, Field, model_validator

POLICIES = ("always_on", "micro_sleep", "compact")

class Config(BaseModel):
    radio: Literal["NR", "LTE"] = "NR"
    duration_ms: int = Field(160, ge=20, le=500)
    load: float = Field(.28, ge=0, le=1.5)
    seed: int = Field(42, ge=0, le=1000000)
    drain_ms: int = Field(0, ge=0, le=100)
    scenario: Literal["bursty", "steady", "overload", "milan"] = "bursty"
    batch_ms: float = Field(2, ge=0, le=8)
    active_w: float = Field(180, ge=1, le=5000)
    slope_w: float = Field(120, ge=0, le=5000)
    sleep_w: float = Field(45, ge=0, le=5000)
    wake_mj: float = Field(.15, ge=0, le=100)
    min_gap_symbols: int = Field(4, ge=3, le=28)
    @model_validator(mode="after")
    def power_order(self):
        if self.sleep_w > self.active_w:
            raise ValueError("sleep_w must not exceed active_w")
        if self.drain_ms >= self.duration_ms:
            raise ValueError("drain_ms must be smaller than duration_ms")
        return self
    @property
    def prbs(self): return 51 if self.radio == "NR" else 100
    @property
    def slot_ms(self): return .5 if self.radio == "NR" else 1.
    @property
    def symbols(self): return int(self.duration_ms / self.slot_ms) * 14
    @property
    def symbol_ms(self): return self.slot_ms / 14

@dataclass
class Packet:
    id: int
    arrival: int
    ue: int
    bits: int
    deadline: int
    urgent: bool

def traffic(c: Config) -> list[Packet]:
    """Seeded arrivals at scheduling interval boundaries; identical across policies."""
    rng = np.random.default_rng(c.seed)
    packets = []
    # Reference capacity assumes 4 useful bits/RE and 0.8 payload fraction.
    nominal = c.prbs * 14 * 12 * 4 * .8
    envelope = None
    if c.scenario == "milan":
        with (Path(__file__).resolve().parents[1]/'data'/'milan_profiles.csv').open() as f:
            envelope = np.array([float(r['thp_mon_milan13_w1_sid4259']) for r in csv.DictReader(f)])
        envelope = envelope / envelope.mean()
    for slot in range(c.symbols // 14):
        if slot * c.slot_ms >= c.duration_ms - c.drain_ms: break
        factor = 1.
        if c.scenario == "bursty": factor = .18 if slot % 32 < 23 else 3.1
        if c.scenario == "overload": factor = 2.8 if slot % 60 > 20 else .4
        if envelope is not None:
            factor = float(envelope[min(143,int(slot * 144 / (c.symbols//14)))])
        count = rng.poisson(c.load * nominal * factor / 6000)
        for _ in range(count):
            ue = int(rng.integers(1, 7))
            urgent = ue <= 2
            bits = int(rng.choice([2400, 4800, 9600, 14400]))
            packets.append(Packet(len(packets), slot * 14, ue, bits,
                                  slot * 14 + math.ceil((4 if urgent else 15) / c.symbol_ms), urgent))
    return packets

def validate_trace(rows: list[dict], c: Config) -> list[Packet]:
    if not rows or len(rows) > 50000: raise ValueError("provide 1–50,000 packets")
    result = []
    for i, r in enumerate(rows):
        t, ue, bits, deadline = float(r["arrival_ms"]), int(r["ue"]), int(r["bits"]), float(r["deadline_ms"])
        if not all(math.isfinite(v) for v in [t, deadline]): raise ValueError("times must be finite")
        if not 0 <= t < c.duration_ms or not 1 <= ue <= 6 or not 1 <= bits <= 10000000 or not 0 < deadline <= 1000:
            raise ValueError("invalid arrival, UE (1–6), payload or relative deadline")
        # Arrivals rounded up to scheduling boundary; never serve before arrival.
        arrival = math.ceil(t / c.slot_ms) * 14
        due = math.floor((t + deadline) / c.symbol_ms)
        result.append(Packet(i, arrival, ue, bits, due, deadline <= 4))
    return sorted(result, key=lambda p: (p.arrival, p.id))

def power_trace(grid: np.ndarray, c: Config, sleep: bool):
    load = np.count_nonzero(grid, axis=1) / c.prbs
    watts = c.active_w + c.slope_w * load
    state = np.where(load > 0, 0, 1)  # active, idle, sleep, wake
    transitions = 0
    if sleep:
        i = 0
        while i < len(load):
            if load[i] != 0: i += 1; continue
            end = i
            while end < len(load) and load[end] == 0: end += 1
            if end - i >= c.min_gap_symbols:
                # Two entry symbols and one wake symbol, including at horizon end.
                start, stop = i + 2, end - 1
                benefit_j = (stop - start) * (c.active_w - c.sleep_w) * c.symbol_ms / 1000
                cost_j = c.wake_mj / 1000
                if benefit_j > cost_j:
                    watts[start:stop] = c.sleep_w
                    state[start:stop] = 2
                    state[stop] = 3
                    watts[stop] += cost_j / (c.symbol_ms / 1000)
                    transitions += 1
            i = end
    return watts, state, transitions

def simulate(c: Config, policy: str, packets: list[Packet]) -> dict:
    if policy not in POLICIES: raise ValueError("unknown policy")
    grid = np.zeros((c.symbols, c.prbs), dtype=np.int16)
    # Simplified mandatory overhead mask, deliberately blocks whole-radio sleep.
    grid[::14, :3] = -1
    if c.radio == "LTE": grid[7::14, :3] = -1
    queue = []
    remaining = {p.id: p.bits for p in packets}
    completion = {}
    last_symbol = {}
    pointer = 0
    # UE-dependent effective payload capacity, fixed across policies (no ML).
    capacity = {u: int(12 * e * .8) for u, e in enumerate([2., 2.8, 3.4, 4., 4.8, 5.4], 1)}
    sent = {u: 0 for u in range(1, 7)}
    arrivals = {u: 0 for u in range(1, 7)}
    for p in packets: arrivals[p.ue] += p.bits
    for slot in range(c.symbols // 14):
        t = slot * 14
        while pointer < len(packets) and packets[pointer].arrival <= t:
            queue.append(packets[pointer]); pointer += 1
        eligible = queue
        if policy == "compact":
            # Causal: flush flexible backlog after a bounded wait or at capacity;
            # urgent traffic is always eligible. EDF protects near deadlines.
            backlog = sum(remaining[p.id] / capacity[p.ue] for p in queue)
            flush = backlog >= c.prbs * 10 or any(
                not p.urgent and ((t-p.arrival)*c.symbol_ms >= c.batch_ms or p.deadline-t <= 14)
                for p in queue)
            eligible = [p for p in queue if p.urgent or flush]
            eligible = sorted(eligible, key=lambda p: (p.deadline, p.arrival, p.id))
        else:
            eligible = sorted(queue, key=lambda p: ((p.ue-slot) % 6, p.arrival, p.id))
        # RR fills in frequency-first order across time, fragmenting idle gaps;
        # compact fills each symbol's frequency resources before advancing time.
        if policy == "compact":
            cells = [(s, f) for s in range(t, t+14) for f in range(c.prbs) if grid[s, f] == 0]
        else:
            cells = [(s, f) for f in range(c.prbs) for s in range(t, t+14) if grid[s, f] == 0]
        cell = 0
        for p in eligible:
            while remaining[p.id] and cell < len(cells):
                s, f = cells[cell]; cell += 1
                grid[s, f] = p.ue
                served = min(remaining[p.id], capacity[p.ue])
                remaining[p.id] -= served; sent[p.ue] += served
                last_symbol[p.id] = max(last_symbol.get(p.id, 0), s + 1)
                if remaining[p.id] == 0: completion[p.id] = last_symbol[p.id]
            if cell == len(cells): break
        queue = [p for p in queue if remaining[p.id] > 0]
    watts, states, transitions = power_trace(grid, c, policy != "always_on")
    latencies = [(completion[p.id]-p.arrival)*c.symbol_ms for p in packets if p.id in completion]
    misses = sum((p.id not in completion or completion[p.id] > p.deadline)
                 for p in packets if p.deadline <= c.symbols or p.id in completion)
    # Censored packets whose deadlines are beyond observation are reported separately.
    censored = sum(p.id not in completion and p.deadline > c.symbols for p in packets)
    ratios = np.array([sent[u]/arrivals[u] for u in arrivals if arrivals[u] > 0])
    energy = float(watts.sum() * c.symbol_ms / 1000)
    delivered = sum(sent.values())
    stats = dict(energy_j=round(energy, 6), mean_power_w=round(float(watts.mean()), 3),
        throughput_mbps=round(delivered/c.duration_ms/1000, 3),
        energy_per_mbit_j=round(energy/(delivered/1e6), 4) if delivered else None,
        p95_latency_ms=round(float(np.percentile(latencies,95)), 3) if latencies else None,
        mean_latency_ms=round(float(np.mean(latencies)),3) if latencies else None,
        deadline_miss_pct=round(100*misses/max(1,len(packets)-censored),3),
        deadline_misses=misses, censored_packets=censored, completed_packets=len(completion),
        packets=len(packets), offered_bits=sum(p.bits for p in packets), delivered_bits=delivered,
        backlog_bits=sum(remaining.values()), sleep_pct=round(float(np.mean(states==2)*100),2),
        utilization_pct=round(float(np.mean(grid>0)*100),2), wakeups=transitions,
        delivery_fairness=round(float(ratios.sum()**2/(len(ratios)*np.sum(ratios**2))),4) if len(ratios) and np.sum(ratios**2) else None)
    # Bin telemetry to scheduling intervals; the PRB grid remains symbol-level.
    frame = 14
    timeline = [dict(time_ms=round(i*c.symbol_ms,4), power_w=round(float(watts[i:i+frame].mean()),3),
                     utilization=round(float(np.mean(grid[i:i+frame]>0)),4),
                     sleep_fraction=round(float(np.mean(states[i:i+frame]==2)),4)) for i in range(0,c.symbols,frame)]
    return dict(policy=policy, stats=stats, grid=grid.T.tolist(), states=states.tolist(), timeline=timeline,
                ue_bits=sent)

def compare(c: Config, packets=None, source="seeded synthetic packet arrivals"):
    if packets is None and c.scenario == "milan":
        source = "Milan measurement-derived normalized activity envelope; compressed day; synthetic packet arrivals"
    ps = traffic(c) if packets is None else packets
    runs = {p: simulate(c,p,ps) for p in POLICIES}
    baseline = runs["always_on"]["stats"]["energy_j"]
    for run in runs.values():
        run["stats"]["saving_pct"] = round(100*(1-run["stats"]["energy_j"]/baseline),2)
    return dict(config=c.model_dump(), meta=dict(prbs=c.prbs, slot_ms=c.slot_ms, symbol_ms=c.symbol_ms,
                scs_khz=30 if c.radio=="NR" else 15, source=source,
                power="illustrative, uncalibrated radio model; not measured hardware"), runs=runs)
