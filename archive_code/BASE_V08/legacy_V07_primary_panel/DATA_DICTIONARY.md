# Data dictionary

`analysis_v08/inputs/PRIMARY_516.csv` defines the 510-run main panel and the six-run TSP3-12-1 supplementary panel. `LATEST_INDEX_516.csv` adds the six later TSP3-10-5 sensitivity records while preserving their separate panel status. `analysis_v08/evidence/primary/` contains the 516 primary terminal JSON files; `oracles/` contains independent reference images; `journals/` contains the four one- and two-worker TSP3-12-1 progress journals; `later_repeats/` contains six sensitivity records.

`outputs/01_PRIMARY_258_PAIRS.csv` contains 255 main-panel and three supplementary method pairs. `02_TIMING_STRATIFIED.csv` and `04_JOINT_INSTANCE_CLUSTERS.csv` contain descriptive timing summaries. Empty numeric fields indicate censored, unavailable, or inapplicable quantities and must not be treated as zero. A hostname match is not proof of physical hardware equality.
