# AP30 four-worker study

Four sequential runs: p=3 Standard, p=3 Block2 (EREN–ILDO), p=4 Standard, p=4 Block2. Each has a 1200 s limit and 300/600/900/1200 s snapshots, four worker processes, and one HiGHS thread per worker. The supervisor executes each runner in a fresh process and validates checkpoint and terminal assignment witnesses.

The p=3 input is the official MOOLibrary AP_p-3_n-30_ins-1.dat benchmark. The p=4 input is a synthetic derived extension: objectives 1–3 are exactly the official costs and objective 4 is generated independently with PCG64 seed 2026102301, costs 1..20. This matches the earlier AP20/AP25 extension convention; it is not an official four-objective benchmark. Inputs and provenance were frozen before performance runs.

The solver code is taken from the latest V03 R1 source archive. The only change to run_checkpoint_multi.py is the protocol metadata label; the original file is retained in provenance/. The algorithms and time/checkpoint guards are unchanged.

Run `python3 prepare_inputs.py` only when source data is available at the documented source path. Run `python3 run_requested_batch.py` in a fresh directory. Existing run prefixes are protected from overwriting. Status SEARCH_COMPLETED means the exact enumeration terminated; RIGHT_CENSORED means the budget elapsed without a completion proof. Witness validation establishes feasibility and objective consistency; no independently known full Pareto reference is available for this instance.
