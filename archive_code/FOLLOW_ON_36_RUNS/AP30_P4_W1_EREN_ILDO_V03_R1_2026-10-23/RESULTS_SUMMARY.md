# AP30 four-objective, one-worker EREN–ILDO run

Objectives 1–3 match the official MOOLibrary AP30 p=3 instance; objective 4 is a synthetic derived extension generated before the run with NumPy PCG64 seed 2026102301 and integer costs 1–20. Input SHA-256: `46b70079fbccbbe620d01207d4ab0d2c7272286ab85eea153deb643627522a1a`.

| Method | Workers | Status | Points at 300/600/900/1200 s | Terminal points | Committed MILP calls | Runtime (s) | Audit |
|---|---:|---|---|---:|---:|---:|---|
| EREN–ILDO (Block2) | 1 | RIGHT_CENSORED | 76/123/170/211 | 211 | 2565 | 1200.095 | PASS |

`RIGHT_CENSORED` means the 1200 s budget elapsed before full Pareto enumeration was certified. Counts report points recovered within the budget, not a proven full-front size. All checkpoint and terminal assignment witnesses were revalidated for feasibility and objective consistency. No independent full Pareto reference is included.

MILP calls count completed oracle tasks committed by the controller before cutoff; individual worker journals also retain calls from unfinished oracles. Timing includes worker startup, coordination, and journal/checkpoint I/O, but excludes parent imports and input parsing.
