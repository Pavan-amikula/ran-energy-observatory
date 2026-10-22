# Recruiter and interview walkthrough

## Ninety-second walkthrough

1. **Problem, 15 seconds:** explain that empty frequency resources alone do not switch off a radio. Whole transmit-symbol gaps are the opportunity. The project makes the link between scheduling, resource allocation and energy visible.
2. **Grid, 20 seconds:** show always-on, micro sleep and compact tabs. Point out teal urgent UEs, purple flexible UEs, reserved signalling and the state strip. Scrub the same time region across policies.
3. **Tradeoff, 20 seconds:** compare energy, p95 latency, deadline misses and queued bits. Explain why energy savings without matching delivered work can mislead. Show `results/equal-work.json` and the 40 ms drain assertion.
4. **Stress test, 15 seconds:** select overload and high offered load. Highlight missed deadlines and accumulated backlog. Explain that the model does not claim energy optimization preserves service at arbitrary load.
5. **Evidence, 20 seconds:** open the benchmark CSV, source notes and forecast metrics. Describe the separately licensed normalized Milan activity profiles, held-out week-labelled forecasting experiment and explicit distinction between measured activity and modelled power.

## Technical questions to prepare

**Why frequency-time instead of average PRB utilization?** Two schedules with similar total utilization can expose different contiguous idle symbol intervals. Micro sleep depends on both gap length and required signalling.

**How is energy calculated?** Integrate instantaneous model power in watts over symbol duration in seconds. Wake energy is added exactly once per accepted sleep interval. The model refuses sleep when expected savings do not cover wake cost.

**What does the 30.90% result establish?** A mean simulated reduction across five fixed seeds for one explicit NR bursty equal-work configuration and specified power parameters. Every policy finishes the identical offered payload within a shared observation window. It does not establish a live-network saving.

**What changed in the compact policy?** Flexible traffic eligibility, EDF order and time-major resource packing. Therefore the current comparison does not isolate packing alone. A future ablation would hold EDF constant and vary packing and batching independently.

**How did you prevent a misleading latency result?** Report p95 alongside completed packets, backlog, deadline misses and censored packets; do not assign artificial zero latency to unfinished packets. Use drain experiments when comparing equal useful work.

**What is real-time here?** The HTTP allocation API accepts external frames and the browser polls a bounded buffer. The SSE stream is explicitly paced simulation replay. The included sender is simulated. A real radio needs a tested allocation adapter and synchronized power measurement.

**What is the ML contribution?** A six-lag ridge autoregression trained on two week-labelled sets of normalized activity profiles and evaluated on a third, compared with persistence. Forecasts use only observed previous samples. It is an offline traffic experiment and does not claim energy prediction or autonomous network control.

**Why not use an ITU energy dataset?** Access and redistribution terms must be satisfied. Relevant papers inform the design, but restricted or unclearly licensed data is not copied into a public portfolio. The bundled traffic subset preserves source-specific notices.

**How would you extend it at Ericsson?** First agree on trace and measurement access. Validate the reserved-activity mask and symbol occupancy against actual scheduler logs; calibrate static/load/state power and wake cost; then compare matched demand and QoS over longer multi-cell traces with realistic radio constraints.

## Recorded demo scope

`results/demo.mp4` is a recording of actual UI interaction. The animated README GIF is a shortened, resized excerpt. `scripts/capture_demo.py` regenerates browser screenshots and the source WebM when the local server is running. The MP4/GIF conversion uses FFmpeg via `imageio-ffmpeg`; no generated video imagery is used.
