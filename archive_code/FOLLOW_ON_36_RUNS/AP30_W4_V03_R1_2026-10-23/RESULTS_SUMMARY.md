# AP30: four-worker Standard and EREN–ILDO experiments

Each run uses four worker processes, one HiGHS thread per worker, a 1200 s wall-clock budget, and 300/600/900/1200 s snapshots. The p=3 input is an official benchmark; p=4 is a synthetic derived fourth-objective extension (PCG64 seed 2026102301).

| Objectives | Method | Status | Points at 300/600/900/1200 s | Terminal points | MILP calls | Runtime (s) | Audit |
|---:|---|---|---|---:|---:|---:|---|
| 3 | standard | RIGHT_CENSORED | 617/1063/1463/1846 | 1846 | 10650 | 1200.834 | PASS |
| 3 | block2 | RIGHT_CENSORED | 785/1355/1871/2389 | 2389 | 9324 | 1200.765 | PASS |
| 4 | standard | RIGHT_CENSORED | 198/312/402/496 | 496 | 8980 | 1200.210 | PASS |
| 4 | block2 | RIGHT_CENSORED | 210/337/441/548 | 548 | 7536 | 1200.222 | PASS |

RIGHT_CENSORED means the time budget elapsed without proof of full Pareto enumeration. SEARCH_COMPLETED means the exact enumeration procedure terminated. Witness checks establish assignment feasibility and objective consistency. The package does not provide an independent full Pareto reference.

Batch status: BATCH_COMPLETE. Completed configurations: 4/4.

## Paired observations

For p=3, the observed terminal nondominated union contains 2389 points: 1846 shared, 0 Standard-only, and 543 Block2-only.
For p=4, the observed terminal nondominated union contains 548 points: 496 shared, 0 Standard-only, and 52 Block2-only.

In both tested inputs, Block2 recovered every point found by Standard within the budget and additional points. This is an observation from one instance per objective count, not a general speed or superiority guarantee. All four runs are right-censored, so full-front completion-time speedup is undefined.

## Counters and timing

MILP calls in the table count calls belonging to completed oracle tasks committed by the controller before the cutoff. Individual completed worker calls, including calls in unfinished oracles, are retained separately in worker call journals. Physical checkpoint persistence and shutdown may finish after the target; only points accepted at or before the target enter its snapshot.
