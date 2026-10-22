# Interface review and design rationale

Reviewed 22 October 2026. The goal is an understandable telecommunications research workspace: inspect a scheduling decision, see its energy consequence, and check whether useful service was preserved. The final interface and code are original. Third-party layouts and product capabilities are references, not claimed integrations.

## Review scope and access

The review covered telecom dashboards, measurement instruments, interactive teaching tools, open-source project pages, public social discussions, and video listings. srsRAN's published Grafana screenshot, the 5G/6G Academy tool, and Grafana's design page were also opened in Chromium and visually inspected. The public LinkedIn and Reddit discussion text was available. YouTube search listings and links were found, but direct video-page retrieval was throttled/unavailable; no claim is made that the full videos were watched. No private accounts, comments or messages were accessed or posted.

## References and adopted ideas

| Reference | What was reviewed | Implication for this project |
|---|---|---|
| [srsRAN Grafana Metrics GUI](https://docs.srsran.com/projects/project/en/latest/user_manuals/source/grafana_gui.html) | Published dashboard screenshot and configuration guide; visual browser inspection | Put summary metrics before time-series detail; keep radio context visible and colors consistent |
| [srsRAN Kubernetes monitoring](https://docs.srsran.com/projects/project/en/latest/tutorials/source/k8s/source/index.html) | gNB monitoring flow and dashboard example | Give external allocation input its own view and connection status |
| [Grafana dashboard best practices](https://github.com/grafana/grafana/blob/main/docs/sources/visualizations/dashboards/build-dashboards/best-practices/index.md) | Official design guidance | Organize the view around a concrete question and proceed from summary to inspection |
| [Grafana: three dashboard design tips](https://grafana.com/blog/3-tips-to-improve-your-grafana-dashboard-design/) | Official article and example imagery; browser inspection | Limit chart types; use a restrained palette; combine colors with explicit state labels |
| [Grafana tutorial library](https://grafana.com/tutorials/) | Video/learning listings, including dashboard design | Use concise presets to make a first experiment understandable without prior setup |
| [Keysight RE Power Heatmap](https://helpfiles.keysight.com/csg/89600B/Webhelp/Subsystems/newradio/content/trc_re_power_heatmap.htm) | Official heatmap description | Explicit time/frequency orientation, units and inspection coordinates; preserve the distinction between a measured RE-power heatmap and this simulated PRB allocation grid |
| [Keysight NR modulation-analysis overview](https://www.keysight.com/ca/en/assets/7018-06904/technical-overviews/5992-4236.pdf) | Documented frame-summary/grid relationship | Keep a numerical comparison alongside the allocation view rather than relying on color alone |
| [Rohde & Schwarz NR signal generation/analysis](https://cdn.rohde-schwarz.com.cn/pws/dl_downloads/dl_application/application_notes/gfm322/GFM322_1e_5GNR_gen_analysis.pdf) | Published allocation-versus-symbol/carrier instrument panel description | Add a persistent cell inspector and numeric PRB/time coordinates |
| [5G/6G Academy RE Mapping Visualizer](https://www.5g6gacademy.com/tools/re-mapping-visualizer) | Interactive tool, controls and grid; browser inspection | Place explanatory controls near the grid and expose selected-cell information; do not imply our grid models its reference-signal mapping |
| [i14y Lab E2E Open RAN setup](https://www.i14y-lab.com/article/e2e-open-ran-setup) | First-party lab-demo page and monitoring description | Make an experiment demonstrable in a short walkthrough; distinguish replay from incoming data |
| [Sidelink 5G OAI dashboard](https://github.com/shariquetelco/Sidelink-5G-OAI-dashboard) | Author's README and documented monitoring/export panels | Clear domain terminology, connection status and export paths; no copied implementation or branding |
| [RF Spectrum Observatory](https://github.com/Pouria-007/RF-Spectrum-Observatory) | Author's documented spectrum, telemetry and demo organization | Keep a coherent visual language between resource maps and power traces; preserve recorded demo artifacts |
| [5G Digital Twin](https://github.com/poornachandran2006/5G_Digital_Twin) | Author's documented dashboard/replay panels | Use synchronized comparisons and explicit replay controls; no inference that this project implements its ML/RL capabilities |
| [Nils Fuerste's LinkedIn post on srsRAN Grafana](https://www.linkedin.com/posts/nils-fuerste_building-a-telco-test-lab-using-srsran-activity-7416735826388365312-kArX) | Public post describing the monitoring pipeline and missing-data troubleshooting | Show whether telemetry is connected, waiting or receiving, separately from simulation results |
| [Reddit: Grafana dashboard design discussion](https://www.reddit.com/r/grafana/comments/1cil9tb/improve_your_grafana_dashboards_with_these/) | Public discussion on clarity, reuse and design, including a Grafana employee's video link | Reduce visual noise, make current data context explicit, and give new users a useful starting point |
| [Grafana YouTube presentation linked in that discussion](https://www.youtube.com/watch?v=gJ55IKaKUOA) | Public reference link; video retrieval unavailable | Discovery reference only; no video-specific design claim |
| [YouTube: Grafana Dashboard Tutorial](https://www.youtube.com/watch?v=GM-jgkDmJx8) | Search listing; direct retrieval throttled | Discovery reference only; no claim of viewing the video |
| [srsRAN UL-heavy scenario demonstration](https://media.ccc.de/v/osmodevcon2024-214-srsran-project-application-in-ul-heavy-traffic-scenarios) | Public talk/demo listing | Include an overload preset and explain visible failure modes rather than presenting only favorable cases |

The social posts and independent project READMEs are their authors' descriptions, not independent verification of those systems. Instrument documentation is used for interaction conventions only. No third-party screenshot or video is bundled as a project output.

## Implemented interface improvements

1. **A compact research workbench:** usable sidebar links, a consistent product header, stronger visual hierarchy and less promotional headline space.
2. **Three experiment presets:** bursty continuous arrivals, an equal-work trial with a 40 ms drain, and overload. Presets adjust traffic/timing while retaining the user's power assumptions.
3. **Service context beside energy:** an explicit statement of unfinished demand, equal completed payload or degraded deadline service, with delivered-bit percentage. Labels remain descriptive rather than implying universal safe/unsafe thresholds.
4. **Numerical grid inspection:** PRB ticks, symbol/time coordinates, allocation class, radio state, symbol occupancy and interval-average model power. Hover, click-to-pin, keyboard arrows and Escape are supported.
5. **Synchronized comparison grids:** expandable previews of all three policies use the same time window and can select the detailed policy view.
6. **Linked power navigation:** the overview highlights the visible grid window; clicking the chart moves that window. Hover reports all three interval-average estimates at the chosen time.
7. **Radio-state composition:** the full-horizon bar and labelled percentages distinguish active, idle, micro sleep and wake.
8. **Reviewable output:** JSON experiment export, labelled grid PNG export, updated screenshots and a fresh recording of actual application interactions.
9. **Visible input state:** modified configuration is marked as unapplied; imported CSV can be explicitly cleared. The experiment result retains the source/configuration actually used.
10. **Responsive and keyboard paths:** checked at multiple desktop, tablet and mobile widths, including keyboard cell inspection and tab selection. This is practical verification, not a claim of full accessibility certification.

## Validation

The browser script exercises the new interactions against the running API. Existing numerical tests remain applicable because the interface update does not change the simulation engine, historical benchmark definitions or energy model. UI screenshots and video are regenerated from the updated app; the numerical study is not re-labelled as a new result.
