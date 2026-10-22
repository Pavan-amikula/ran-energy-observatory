# Traffic data attribution and terms

`milan_profiles.csv` is a selected-column subset of [mob-traffic-ds](https://github.com/arimvydas/mob-traffic-ds) by Arimvydas (GitHub author), pinned at commit `da1db1963b22437aadf6621d6d6c88ffbe2425f7`. The upstream repository is licensed under GPL-3.0; a copy is in `GPL-3.0.txt`. Preserve that license and attribution when distributing this subset. It is not covered by this project's MIT code license.

The upstream README describes the Milan columns as weekly internet usage profiles extracted from Telecom Italia's published dataset, using three weeks from December 2013. These are **published measurement-derived normalized activity profiles**, not raw traffic volumes. Exact calendar dates of the three week labels have not been verified. Square ID 4259 is retained for 21 daily profiles, each with 144 ten-minute samples. No geography or subscriber identity is inferred.

Original data: Telecom Italia, *Telecommunications - SMS, Call, Internet - MI*, [Harvard Dataverse DOI](https://doi.org/10.7910/DVN/EGZHFV). This is **[from BigDataChallenge contest](https://theodi.fbk.eu/openbigdata/)**. The original database is available under the [Open Data Commons Open Database License 1.0](https://opendatacommons.org/licenses/odbl/1-0/). A derived database must preserve applicable ODbL attribution and share-alike obligations as well as the upstream GPL notice. Source and transformations are available in `scripts/fetch_profiles.py` and `provenance.json`.

The application uses one daily profile only as a dimensionless arrival-rate envelope, scaled to its mean and compressed into the simulated horizon. The packets, sub-millisecond scheduling and all power values remain synthetic/modelled. This is a shape stress test, not a reconstruction or measurement of the source network.

`example_packets.csv` is an original, manually constructed synthetic test fixture under the project's MIT license.
