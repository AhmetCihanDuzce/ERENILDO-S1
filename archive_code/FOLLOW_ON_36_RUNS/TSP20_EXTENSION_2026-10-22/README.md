# TSP20 Extension Experiment (2026-10-22)

This separate extension evaluates one registered n=20 instance for each objective dimension (p=3 and p=4), with Standard and EREN–ILDO/Block2, using 1, 2, and 4 workers. Each condition has a 1200 s cap and checkpoints at 300, 600, 900, and 1200 s. It is separate from the frozen n=15/25/40 cohorts. The official archives contain five registered replicates per (p,n); this extension uses replicate 1 only and does not claim coverage of all replicates.

The official Pettersson–Özlen TSP objective coefficients were parsed from the archived LP sources. The solver uses the common directed-arc binary MTZ encoding in the V03 R1 runner; it does not execute the source LP verbatim. Costs are symmetric in the official sources. Results are reported as exact only if the recorded terminal status is SEARCH_COMPLETED. A RIGHT_CENSORED run is a completed time-capped attempt and does not establish the full Pareto front.

Run `python run_batch.py` to execute the fixed 12-cell batch sequentially and audit each terminal result. Runner source is preserved in `src/`; source archives and parsed input JSON are in `raw/`, `source/`, and `inputs/`.
