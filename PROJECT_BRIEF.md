# Project handoff for a resume-writing chat

Use the facts below to tailor a resume and project discussion for **Master Thesis: Understanding Power Consumption Through Frequency-Time Grid Visualization** at Ericsson. Emphasize the implemented work and measured computational results. Preserve the distinction between **simulated energy**, **measurement-derived normalized traffic**, and **actual external telemetry ingestion**. Do not invent employment, Ericsson affiliation, a completed thesis, field deployment or measured hardware savings.

## Project identity

**Name:** RAN Energy Observatory — Frequency–Time Resource Allocation and Energy Analysis for 4G/5G.

**Owner:** Amikula Pavan Kumar Goud.

**Type:** Independent applied telecommunications research and software project.

**Repository:** https://github.com/Pavan-amikula/ran-energy-observatory

**Deliverables:** Working FastAPI application; professional responsive dashboard; symbol-level PRB grids; three scheduling/power policies; CSV packet-trace import; JSON export; external allocation telemetry API and visualization; paced SSE replay; reproducible experiment scripts; numerical results; static research figures; a recorded application demonstration embedded in the README; source and data provenance; automated tests; GitHub Actions workflow; Docker recipe; research notes and interview walkthrough.

**Interface refinement:** Reviewed telecom/instrument dashboards, public project interfaces and community discussions. Added reproducible experiment presets, synchronized policy previews, a hover/pinned/keyboard cell inspector, numeric PRB axes, linked grid/power navigation, delivered-work context, state composition, unapplied-input indication and labelled PNG export. Browser interactions were checked at 360, 390, 768, 1024 and 1280 px; screenshots and the actual-app recording were refreshed. See `docs/interface-research.md` for references and access limits.

## Problem and motivation

Mobile-network radio energy depends on when resources are allocated, whether required signals remain active, and whether idle gaps are long enough to justify entering sleep. Average PRB utilization hides this temporal structure. The project makes resource allocation visible in a frequency–time grid and connects it to explicit power-state assumptions, packet service and energy–latency tradeoffs.

The published principles behind Ericsson Micro Sleep Tx and Low Energy Scheduler motivate the experiment. The implementation consolidates flexible demand and serves urgent traffic without deliberate batching. It is an original research demonstrator of those principles, not a reproduction of proprietary software.

## Technology and implementation

- **Python, NumPy and Pydantic:** deterministic seeded packet generation, validated configuration, causal interval-boundary arrivals, UE-dependent effective payload capacities, packet queues, scheduling and numerical energy integration.
- **FastAPI / Uvicorn:** experiment API, CSV packet import, health endpoint, OpenAPI documentation, Server-Sent Events replay, external allocation ingestion and a bounded telemetry buffer.
- **JavaScript, HTML, CSS and Canvas:** responsive dashboard with policy tabs, frequency–time PRB heatmaps, per-cell tooltips, radio-state strips, time windows, replay and scrubbing, power comparison charts, KPI cards, assumption controls, upload and export.
- **4G / 5G grid configurations:** LTE 100 PRBs at 15 kHz using a 1 ms display/scheduling interval; NR 51 PRBs at 30 kHz using 0.5 ms slots; 14 average-duration symbols per scheduling interval. A visualization cell is one PRB over one symbol, not an individual resource element.
- **Scheduling:** cyclic UE-priority frequency-major baseline; identical baseline allocation with micro sleep; earliest-deadline-first consolidation with time-major resource packing and bounded flexible-traffic holding rules. IDs 1–2 represent urgent traffic; IDs 3–6 flexible traffic.
- **Power modelling:** active-idle plus load-dependent power, mandatory signalling mask, whole-symbol sleep eligibility, two entry symbols, one wake symbol and explicit wake energy. Sleep is selected only where modelled savings exceed transition cost.
- **Service metrics:** delivered throughput, packet completion, backlog bits, mean/p95 latency, deadline misses, censored incomplete packets, normalized per-UE delivery fairness, energy per delivered Mbit, sleep fraction and wake transitions.
- **Engineering:** pytest tests, Chromium/Playwright interaction validation, CSV/JSON experiment evidence, Matplotlib figures, GitHub Actions computational validation, native run instructions and a Docker recipe.

## Research and datasets

Reviewed primary sources include 3GPP/ETSI resource-grid specifications, Ericsson Micro Sleep Tx / Low Energy Scheduler publications, analytical base-station power models, measured 5G energy-modelling papers, srsRAN metrics/Grafana documentation, and 5G-LENA. The full notes cite sources and document which aspects are abstracted.

The project bundles **21 published measurement-derived normalized Milan internet-activity profiles**: one square ID, three week labels, seven days per week and 144 ten-minute bins per day, yielding 3,024 activity samples. The upstream repository commit and file hashes are recorded. Dataset-specific GPL and underlying Telecom Italia ODbL notices are kept separately from original MIT code.

The dashboard's Milan scenario compresses one published daily activity shape into the simulation horizon and uses it to modulate synthetic packet arrivals. Historical PRBs, packet schedules and radio power are not inferred from those normalized activity values.

## Completed experiments and defensible results

### 1. Paired scheduling evaluation

**90 paired configurations / 270 policy evaluations:** two radio configurations × three synthetic traffic profiles × three nominal loads × five fixed seeds. Each paired comparison holds packet arrivals, UE capacity and power assumptions fixed. Outputs include all seed-level records, group statistics and plots. Saturated cases reveal rising backlog and missed deadlines, avoiding a claim that energy savings always preserve service.

### 2. Equal delivered-work evaluation

For an NR bursty configuration at nominal load 0.28, use a common 160 ms horizon, stop arrivals after 120 ms, and allow 40 ms to drain queues. Across five seeds, every policy delivers exactly the same offered payload with zero backlog. The compact policy obtains:

- **30.90% mean modelled energy reduction** against the always-on baseline.
- **28.78–32.00%** reduction across the five fixed seeds.
- Mean energy **34.57 J → 23.89 J**.
- Mean of per-run p95 packet latency **3.545 ms → 4.125 ms**.
- **0% compact-policy deadline misses** in these specific trials.

These values depend on the specified illustrative power assumptions: 180 W active-idle, 120 W load slope, 45 W sleep and 0.15 mJ wake. They are simulation evidence, not measured power savings on Ericsson equipment. The compact policy changes EDF ordering and packing together, so the result does not isolate packing alone. The equal-work script asserts payload equality and zero backlog rather than assuming them.

### 3. Sensitivity analysis

Twelve combinations of sleep-state power and wake energy vary the energy assumptions while holding the traffic seed fixed. All raw outputs are exported to `results/sensitivity.csv` so model assumptions remain reviewable.

### 4. Machine-learning traffic experiment

Implemented a **six-lag ridge autoregression with daily sine/cosine features** to forecast the next normalized activity sample. Train on week labels 1–2, hold out week label 3, use only previously observed values at test time and compare with a persistence baseline. No shuffled split; 2,010 training examples and 1,002 held-out examples.

- Persistence MAE **0.03945**, ridge MAE **0.03614**: approximately **8.38% lower held-out MAE**.
- Persistence RMSE **0.05651**, ridge RMSE **0.05216**.

This is an offline normalized-traffic forecasting result. The original calendar dates of the week labels are unverified. It is not an energy predictor or a production closed-loop scheduler.

### 5. Validation and demo

**14 automated tests passed locally**, covering deterministic reproduction, bit conservation, correct sleep/wake energy accounting, required-signalling constraints, overload, latest-cell packet completion, incomplete-packet censoring, exact-horizon deadline misses, equal-work drain, LTE/NR dimensions, trace validation, telemetry ingestion and replay labelling.

Chromium interaction checks passed for three policy tabs, grid playback, time scrubbing, LTE selection, overload, CSV import, JSON export, telemetry connection and a 390 px mobile layout. The README includes a GIF excerpt and a full MP4 recorded from the actual running application.

The native Python application was executed. The Docker recipe was not executed locally. Repository CI status must be taken from the actual Actions run.

## Direct mapping to the thesis requirements

| Thesis requirement | Project evidence |
|---|---|
| Frequency–time domain in 4G/5G | LTE/NR configuration, PRB–symbol grids, numerology and time/frequency labels |
| Scheduling decisions and resource allocation | Controlled allocation policies, seeded common demand, deadline-aware consolidation |
| Energy Performance features | Sleep opportunity visualization, explicit radio states and transition accounting |
| Connecting allocations with power | Integrated state/load power estimate and overlaid power comparisons |
| Intuitive demonstration | Responsive dashboard, tooltips, scrubbing, recorded video and methodological explanation |
| Opportunities for improvement | Overload analysis, batching/energy tradeoffs, power sensitivity and concrete validation roadmap |
| Programming and problem solving | Python simulation, numerical modelling, REST APIs and browser application |
| Data analysis and visualization | Multi-seed paired evaluation, exported evidence, static research figures and interactive charts |
| Sustainable networks | Energy per useful delivery, micro sleep exploration and service-quality constraints |
| Machine learning bonus | Held-out normalized activity forecasting with a persistence baseline |

## Resume bullet candidates

Select two to four bullets appropriate to available resume space. Keep “simulated” or “modelled” attached to the energy result.

- Built a Python/FastAPI 4G/5G RAN analysis platform visualizing symbol-level PRB allocations, radio power states and energy–latency tradeoffs through an interactive frequency–time dashboard.
- Implemented deadline-aware traffic consolidation and transmit micro-sleep modelling; demonstrated **30.9% mean simulated energy reduction** over five equal-payload seeded trials, with **zero residual backlog** and explicit p95-latency reporting.
- Evaluated **90 paired LTE/NR configurations and 270 policy runs**, exporting reproducible energy, throughput, packet-latency, deadline-miss and backlog metrics across bursty, steady and overload demand.
- Developed validated REST allocation telemetry ingestion, paced SSE replay, CSV trace import and JSON experiment export; verified numerical and API behaviour with **14 automated tests** and browser interaction checks.
- Applied ridge autoregression to **3,024 published normalized mobile-traffic samples**, reducing held-out one-step forecasting MAE by **8.38%** against persistence using a week-labelled holdout.

## Relevant keywords

4G LTE; 5G NR; Radio Access Network; RAN; Energy Performance; network energy efficiency; sustainable telecommunications; frequency–time grid; Physical Resource Blocks; PRB allocation; OFDM symbols; numerology; subcarrier spacing; downlink scheduling; earliest deadline first; QoS; deadline-aware resource allocation; traffic consolidation; transmit micro sleep; sleep-state modelling; transition energy; power consumption modelling; energy–latency tradeoff; throughput; p95 latency; packet queues; backlog; reproducible experiments; paired-seed evaluation; sensitivity analysis; Python; NumPy; FastAPI; REST API; Server-Sent Events; data visualization; Canvas; JavaScript; CSV/JSON; machine learning; ridge regression; autoregressive forecasting; held-out evaluation; pytest; Playwright; GitHub Actions.

## Prompt to give the resume-writing chat

> Tailor my resume for Ericsson's “Master Thesis: Understanding Power Consumption Through Frequency-Time Grid Visualization” opportunity. Use the RAN Energy Observatory facts and verified results in this brief. Prioritize 4G/5G frequency–time visualization, PRB allocation, deadline-aware scheduling, power modelling, micro sleep, reproducible analysis, Python and sustainability. Select concise ATS-friendly project bullets and a relevant skills section. Preserve the qualifiers on simulated energy and normalized traffic. Do not invent employment, hardware deployment, proprietary Ericsson experience or completed thesis research. Ask me for my actual education, dates and other experience before writing those sections.
