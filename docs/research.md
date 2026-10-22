# Research foundation and modeling decisions

Research checked on 22 October 2026. This project is an interactive, reproducible scheduling and energy-analysis demonstrator. Its simulations are not measurements of Ericsson equipment. The primary-source review below informs the design; it does not imply that the referenced implementations or their reported experiments were executed here.

## What the thesis problem requires

The useful question is not simply how many PRBs are occupied. It is whether a scheduler can arrange the same useful traffic into a pattern that creates sufficiently long idle transmit intervals while respecting delay constraints. A frequency-time grid makes that mechanism visible. Energy, delivery, delay and sleep occupancy must be inspected together. A useful comparison therefore holds the arrival trace, radio configuration and power parameters fixed while changing the scheduling policy.

The following are **project design choices**, inferred from the sources, rather than 3GPP requirements: compare an immediate-service baseline with deadline-aware traffic consolidation; distinguish urgent and delay-tolerant traffic; show mandatory activity independently from user allocations; use a configurable state-based power model; and present energy-versus-delay results over several loads and seeds.

## Primary-source review

### 1. NR resource-grid definitions

3GPP TS 38.211 defines NR numerologies, slots, resource elements and resource blocks in clauses 4.2–4.4. A resource block spans 12 subcarriers. Normal cyclic prefix uses 14 symbols per slot; slot duration changes with numerology. A PRB is a frequency-domain block, so a visualization cell spanning an entire slot must be described as a PRB-slot allocation. For normal CP, the familiar slot-duration relationship is `1 ms / 2^mu`. A simplified grid must distinguish its chosen scheduling granularity from physical symbol-level mapping. [ETSI TS 138 211 V19.1.0, Release 19](https://www.etsi.org/deliver/etsi_TS/138200_138299/138211/19.01.00_60/ts_138211v190100p.pdf).

**Design implication:** label time in milliseconds and frequency in PRB indices, display numerology, and avoid calling a PRB-slot one resource element. A coarse reserved-activity mask can illustrate signaling constraints, but cannot claim full control-channel or reference-signal mapping.

### 2. Ericsson Micro Sleep Tx and Low Energy Scheduler

Ericsson describes Micro Sleep Tx as switching off power amplifiers at symbol times when neither required downlink signaling nor user data needs transmission. Its Low Energy Scheduler reschedules non-critical downlink traffic to empty more timeslots; time-sensitive transfers such as voice are excluded. The same case study separately identifies antenna-branch sleep and capacity-cell sleep. These operate at different scopes and should not be treated as interchangeable. [Ericsson, Tackling Network Energy Consumption, 2022, page 3](https://www.ericsson.com/4ae555/assets/local/cases/customer-cases/2022/tackling-network-energy-consumption.pdf).

**Design implication:** consolidate elastic traffic while bypassing batching for urgent packets. Empty frequency blocks alone do not imply a sleeping transmitter. Describe the algorithm as inspired by the published principle, not as a reproduction of proprietary Ericsson LESS.

### 3. LTE and NR have different idle opportunities

Ericsson explains how NR's leaner signaling design creates longer opportunities for transmit sleep than LTE's more frequent always-on transmissions. Its measurements are specific to the cited radio products and operating configurations, rather than universal conversion factors. [Ericsson Research, The ultra-lean design in 5G NR is starting to have a real-world impact, 2021](https://www.ericsson.com/en/blog/2021/10/5g-energy-consumption-impact-5g-nr).

**Design implication:** an LTE-like and an NR-like reserved-activity profile can teach the difference, but a coarse profile must be labeled illustrative. Do not transfer the article's percentage savings to this simulator or to arbitrary base stations.

### 4. System-level energy-performance context

Ericsson's review distinguishes fixed idle costs, transmitter sleep, processing demand and future energy-performance challenges. It places energy efficiency alongside network capacity and performance, rather than optimizing one isolated utilization counter. [Andersson et al., Improving energy performance in 5G networks and beyond, Ericsson Technology Review, 2022](https://www.ericsson.com/en/reports-and-papers/ericsson-technology-review/articles/improving-energy-performance-in-5g-networks-and-beyond).

**Design implication:** show useful delivered traffic and deadline misses next to modeled joules. An apparent energy improvement achieved by serving less traffic must be visible. Avoid presenting reduced radio-model energy as complete site electricity savings or verified carbon reduction.

### 5. A transparent power-model baseline

Holtkamp et al. develop a parameterized model with a static consumption component, a load-dependent component and a lower sleep-state consumption. They also discuss bandwidth, antenna chains and amplifier efficiency. Their evaluated parameter sets concern the equipment assumptions of that study; they are not calibration values for an arbitrary modern massive-MIMO radio. [Holtkamp, Auer, Giannini and Haas, A Parameterized Base Station Power Model, IEEE Communications Letters, 2013; author preprint](https://arxiv.org/html/1411.1571v1).

**Design implication:** an affine active-power approximation and explicit sleep state are defensible educational abstractions. Publish every wattage assumption. Integrate power over simulation time: `E_J = sum(P_W * dt_s)`, and report `Wh = J / 3600`. If transition costs are modeled, document whether they represent additional energy or a transition state to avoid double counting.

### 6. PRB utilization is insufficient to identify real power

Piovesan et al. examine analytical and learned power models for real 5G active antenna units. Their inputs include hardware/configuration details, traffic statistics and sleep-mode durations. They explicitly explain that PRB load does not uniquely determine total transmit power and consumption in multi-carrier equipment. Shared amplifiers complicate predictions from switching off one carrier. [Piovesan et al., Machine Learning and Analytical Power Consumption Models for 5G Base Stations, IEEE Communications Magazine; author preprint](https://arxiv.org/html/2209.11600v1).

**Design implication:** present power as an estimate under selected parameters. A single-sector abstraction should not imply modeling of multi-carrier shared amplifiers. A future measured-data model needs bandwidth, antenna/RF-chain configuration and energy-saving counters in addition to load.

### 7. Generalization matters for energy prediction

Chen et al. describe hourly real-world measurements from the ITU energy-modeling challenge and investigate base-station-specific energy fingerprints. Their analysis shows why identical visible inputs can correspond to different consumption across equipment. [Chen et al., Modelling the 5G Energy Consumption Using Real-world Data: Energy Fingerprint is All You Need, author preprint, revised 2025](https://arxiv.org/html/2406.16929v2).

**Design implication:** if fitting ML to measured energy, evaluate held-out base stations as well as future time intervals. Random row splits can hide equipment leakage. Any regressor fitted only to the demonstrator's generated labels is a surrogate of the simulator, not independent validation of physical power or evidence of measured-network accuracy.

### 8. srsRAN observability and dashboard precedent

srsRAN documents JSON metrics, scheduler/cell/UE counters, timestamps, throughput-related fields and PRB usage counters. Current output documentation describes a WebSocket subscription interface. Its Grafana guide also describes a Docker dashboard and a metrics-server transport workflow; interface details can differ between versions. [srsRAN Project, Outputs](https://docs.srsran.com/projects/project/en/latest/user_manuals/source/outputs.html); [srsRAN Project, Grafana Metrics GUI](https://docs.srsran.com/projects/project/en/latest/user_manuals/source/grafana_gui.html).

**Design implication:** borrow the observability pattern of timestamped telemetry, readable KPI cards and linked plots. Keep ingestion separate from rendering. Aggregate counters do not recover per-UE, per-PRB allocations; real grid reconstruction needs allocation-level instrumentation. A generic JSON import must not be advertised as a verified srsRAN adapter without testing its exact schema against a pinned release.

### 9. 5G-LENA as an external validation path

CTTC's 5G-LENA is an open-source NR module for ns-3. Its documented examples include end-to-end scenarios, schedulers, occupancy traces and flow-performance outputs. The module is distributed under GPLv2. [CTTC, 5G-LENA downloads](https://5g-lena.cttc.es/download/); [CTTC, 5G-LENA examples](https://cttc-lena.gitlab.io/nr/html/group__examples.html).

**Design implication:** future validation can replay external allocation traces and compare flow delay and occupancy with the lightweight model. This project should remain explicit about which engine generated a result. Reading 5G-LENA documentation is not evidence that its simulations were run. Referencing it does not require copying its implementation into this project.

### 10. Public mobile-activity data with explicit terms

Telecom Italia's Milan release contains aggregated telecommunications activity over geographic grid squares and ten-minute intervals, rather than physical base-station scheduling traces. The primary dataset record and its API provide unrestricted file access and explicit ODbL 1.0 terms. The originating ODI Trento catalog also identifies that license and temporal aggregation. [Telecom Italia, Telecommunications — SMS, Call, Internet — MI, Harvard Dataverse, 2015](https://doi.org/10.7910/DVN/EGZHFV); [ODI node Trento, Open Big Data](https://theodi.fbk.eu/openbigdata/).

**Design implication:** sum internet activity across country codes for a selected square and preserve the timestamp. Normalize only as a traffic envelope. The square is not a known serving cell; activity is not throughput, packet bytes, PRB allocation or measured power. Mapping its ten-minute envelope to millisecond arrivals is an explicit synthetic scenario transformation, with the time compression and scaling reported.

## Dataset access and provenance

### Original source: Telecom Italia Milan

- Dataset DOI: [10.7910/DVN/EGZHFV](https://doi.org/10.7910/DVN/EGZHFV).
- Metadata endpoint: `https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:10.7910/DVN/EGZHFV`.
- Example daily file: [sms-call-internet-mi-2013-11-01.txt, file 2674255](https://dataverse.harvard.edu/api/access/datafile/2674255), 322,874,887 bytes; metadata MD5 `658c49f8e3c7910bd3bb2bafbf62cdce`.
- Smaller daily alternative: [sms-call-internet-mi-2013-12-29.txt, file 2674317](https://dataverse.harvard.edu/api/access/datafile/2674317), 277,460,259 bytes.
- Schema: square ID, interval timestamp, country code, SMS in, SMS out, call in, call out, internet activity; tab-separated, missing activity fields possible.
- License: **ODbL 1.0**, attribution and database share-alike; keep derived traffic data licensing distinct from application source-code licensing. Preserve the requested attribution link: [from BigDataChallenge contest](https://theodi.fbk.eu/openbigdata/).
- Practical use: download one day outside source control, verify its checksum, and publish a small documented derived envelope with source file ID, date, square ID, aggregation rule and checksum. A daily source is hundreds of MB; the derived envelope is small. Missing time bins require an explicit fill policy, not silent removal.

These access details were checked through the repository metadata API. That check is separate from executing a full download or preprocessing run; execution evidence belongs in generated dataset metadata and results.

### Compact measurement-derived profiles for the bundled demonstration

The compact source is [arimvydas/mob-traffic-ds](https://github.com/arimvydas/mob-traffic-ds), pinned to commit `da1db1963b22437aadf6621d6d6c88ffbe2425f7`. Its [README at that revision](https://github.com/arimvydas/mob-traffic-ds/blob/da1db1963b22437aadf6621d6d6c88ffbe2425f7/README.md) identifies its source data as digitized from published work and describes the Milan profiles as extracted from Telecom Italia activity data for three weeks in December 2013. These are **published measurement-derived normalized activity profiles**, not original raw counters, packet traces, measured PRB grids or measured energy.

- Download: [traffic_normal.csv at pinned revision](https://raw.githubusercontent.com/arimvydas/mob-traffic-ds/da1db1963b22437aadf6621d6d6c88ffbe2425f7/data/traffic_normal.csv), 477,454 bytes.
- API fallback: `https://api.github.com/repos/arimvydas/mob-traffic-ds/contents/data/traffic_normal.csv?ref=da1db1963b22437aadf6621d6d6c88ffbe2425f7` returns base64 CSV content.
- Verified shape: 144 rows; `t_day` is fractional day at ten-minute increments. Milan columns follow `thp_{weekday}_milan13_w{week}_sid{square}`, with weekdays `mon` through `sun`, week labels `1`, `2`, `3`, and square labels `4259`, `4456`, `5060`, `5200`, `5085`.
- Example column: `thp_mon_milan13_w1_sid4259`. Its first three values are `0.1359398016466639`, `0.15484663597135365`, `0.1438864734771749`.
- Upstream repository license: [GPL-3.0 license file](https://github.com/arimvydas/mob-traffic-ds/blob/da1db1963b22437aadf6621d6d6c88ffbe2425f7/LICENSE). Preserve its notice with the selected data. The original Telecom Italia data terms remain relevant: retain ODbL attribution and share-alike notices for the derived database, separately from the application's code license.
- Exact calendar dates corresponding to the upstream week labels are not established by its README. Preserve those labels without inventing dates or a claim that these values reconstruct a specific original raw day.

This compact source supports a realistic diurnal traffic-envelope demonstration. Any generated arrival times, packet sizes, allocations and power values remain simulated, even when their demand envelope follows these profiles.

### Relevant sources not selected for automatic redistribution

**NetData:** the authors publish 4G/5G weekday/weekend measurements with traffic, PRB utilization, BBU/RRU energy and sleep counters. Its visible repository did not provide an explicit root license during this review. Public download access alone does not establish redistribution permission. Use it as a prospective calibration source only after the applicable rights are clarified. [Tsinghua FIB Lab, NetData](https://github.com/tsinghua-fib-lab/NetData).

**ITU 5G energy challenge:** the official data page requires registration, team creation and approval to download the original measurements. A Hugging Face mirror advertises MIT in metadata but its CSV endpoint returned HTTP 401 during access checking. Do not bypass gating or silently bundle copies from third-party solution repositories. [ITU challenge data instructions on Zindi](https://zindi.world/competitions/aiml-for-5g-energy-consumption-modelling/data); [mirror dataset card](https://huggingface.co/datasets/netop/5G-Network-Energy-Consumption).

## Evaluation and honest interpretation

The following validation protocol is a project recommendation, not a published performance claim:

1. Feed identical arrivals to both policies and log the random seed and all configuration values.
2. Check conservation: arrived bits must equal delivered, queued and explicitly dropped bits. Count deadline misses and end-of-window backlog so unfinished work cannot inflate savings.
3. Test zero traffic, low traffic, burst traffic and saturation. Preserve mandatory activity during user-data idle periods.
4. Report modeled joules, energy per delivered megabit, delivery ratio, deadline-miss ratio, p50/p95 queueing delay, active/sleep occupancy and transition count. Mark an undefined energy-per-bit result when nothing is delivered.
5. Sweep traffic load and batching allowance, showing the energy-delay tradeoff, including configurations where consolidation does not help.
6. If using multiple random seeds, report dispersion; if testing only one deterministic trace, report that limitation instead of implying a statistical confidence interval.
7. Keep simulated-time throughput distinct from wall-clock runtime and UI refresh rate. A dashboard can update live while visualizing simulated traffic.

The strongest recruiter-facing claim is a reproducible tool that explains a RAN energy-performance mechanism and evaluates its tradeoffs. A lightweight scheduler model does not by itself establish measured Ericsson energy savings, full 3GPP compliance, over-the-air operation, field deployment, or external-simulator validation. Those require separate experiments and evidence.
