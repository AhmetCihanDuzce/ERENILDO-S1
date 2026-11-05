# AP30: two-worker Standard and EREN–ILDO experiments

Each run uses two worker processes, one HiGHS thread per worker, a 1200 s wall-clock budget, and 300/600/900/1200 s snapshots. The p=3 input is an official benchmark; p=4 is a synthetic derived fourth-objective extension (PCG64 seed 2026102301).

| Objectives | Method | Status | Points at 300/600/900/1200 s | Terminal points | MILP calls | Runtime (s) | Audit |
|---:|---|---|---|---:|---:|---:|---|
| 3 | standard | RIGHT_CENSORED | 345/575/796/1015 | 1015 | 5832 | 1200.428 | PASS |
| 3 | block2 | RIGHT_CENSORED | 473/815/1096/1356 | 1356 | 5212 | 1200.577 | PASS |
| 4 | standard | RIGHT_CENSORED | 105/188/247/301 | 301 | 5028 | 1200.147 | PASS |
| 4 | block2 | RIGHT_CENSORED | 125/209/284/353 | 353 | 4467 | 1200.156 | PASS |

RIGHT_CENSORED means the time budget elapsed without proof of full Pareto enumeration. SEARCH_COMPLETED means the exact enumeration procedure terminated. Witness checks establish assignment feasibility and objective consistency. The package does not provide an independent full Pareto reference.

Batch status: BATCH_COMPLETE. Completed configurations: 4/4.

## Paired observations

For p=3, the observed terminal nondominated union contains 1356 points: 1015 shared, 0 Standard-only, and 341 Block2-only.
For p=4, the observed terminal nondominated union contains 353 points: 301 shared, 0 Standard-only, and 52 Block2-only.

In both tested inputs, Block2 recovered every point found by Standard within the budget and additional points. This is an observation from one instance per objective count, not a general speed or superiority guarantee. All four runs are right-censored, so full-front completion-time speedup is undefined.

## Counters and timing

MILP calls in the table count calls belonging to completed oracle tasks committed by the controller before the cutoff. Individual completed worker calls, including calls in unfinished oracles, are retained separately in worker call journals. Physical checkpoint persistence and shutdown may finish after the target; only points accepted at or before the target enter its snapshot.
