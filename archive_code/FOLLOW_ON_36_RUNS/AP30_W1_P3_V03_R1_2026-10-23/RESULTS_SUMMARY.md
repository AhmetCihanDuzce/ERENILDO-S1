# AP30 three-objective, one-worker results

Official MOOLibrary AP30 p=3 instance. Standard (generalized PEA) and Block2 (EREN–ILDO) were each run once with one worker and one HiGHS thread. Each run had a 1200 s wall-clock budget and snapshots at 300, 600, 900, and 1200 s. Input SHA-256: `12a1075b7a34d39fd9bfd8a95d0fd5e79d4e56b7b8ec124e5bfd94d1a96973ef`.

| Method | Status | Points at 300/600/900/1200 s | Terminal points | Committed MILP calls | Runtime (s) | Witness audit |
|---|---|---|---:|---:|---:|---|
| standard | RIGHT_CENSORED | 196/364/482/585 | 585 | 3342 | 1200.307 | PASS |
| block2 | RIGHT_CENSORED | 274/476/636/803 | 803 | 3082 | 1200.264 | PASS |

## Checkpoint comparison

At 300 s: raw union 274, of which 274 are nondominated in the observed union (0 dominated); 196 shared, 0 Standard-only, 78 Block2-only nondominated points. Union contribution: Standard 0.715, Block2 1.000.
At 600 s: raw union 476, of which 476 are nondominated in the observed union (0 dominated); 364 shared, 0 Standard-only, 112 Block2-only nondominated points. Union contribution: Standard 0.765, Block2 1.000.
At 900 s: raw union 636, of which 636 are nondominated in the observed union (0 dominated); 482 shared, 0 Standard-only, 154 Block2-only nondominated points. Union contribution: Standard 0.758, Block2 1.000.
At 1200 s: raw union 803, of which 803 are nondominated in the observed union (0 dominated); 585 shared, 0 Standard-only, 218 Block2-only nondominated points. Union contribution: Standard 0.729, Block2 1.000.

The two runs are right-censored: the 1200 s budget elapsed before full Pareto enumeration was certified. These counts therefore describe nondominated points recovered within the budget and do not establish complete frontiers or a general method ranking. The comparison is based on a single official instance. Witness validation checks assignment feasibility and objective consistency; this package does not contain an independent full Pareto reference.

MILP calls in the summary count calls belonging to completed oracle tasks committed before the cutoff. Individual completed calls, including those in unfinished oracles, are preserved in per-worker journals. Timing starts before worker construction and includes worker startup, coordination, and journal/checkpoint I/O; input parsing and parent imports are excluded.
