# AP30 two-worker study

The same official p=3 AP30 input and synthetic p=4 extension (PCG64 seed 2026102301) are run with two worker processes using Standard and Block2 (EREN–ILDO). Input and solver source bytes are identical to the completed four-worker cohort. Each worker uses one HiGHS thread. Each of four sequential runs has a 1200 s budget and 300/600/900/1200 s snapshots.

The runner retains the original source protocol metadata label mentioning AP30_W4 solely to keep its source hash identical. Each run separately records the actual worker count (2), assigned CPUs, solver thread settings, and input hashes.

Run `python3 run_requested_batch.py` in a fresh directory with no run records. Existing output prefixes are protected from overwriting. `RIGHT_CENSORED` indicates a budget-limited run without a full enumeration proof. Four-objective data is a synthetic derived extension, not an official four-objective benchmark. Individual solver calls and completed-oracle counters have distinct scopes, retained in per-worker journals and checkpoint records.
