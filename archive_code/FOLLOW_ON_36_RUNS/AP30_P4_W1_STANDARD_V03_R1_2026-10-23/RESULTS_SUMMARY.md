# AP30 four-objective, one-worker Standard run

Official input provenance: objectives 1–3 match the MOOLibrary AP30 p=3 instance; objective 4 is a synthetic derived extension generated before the performance run with NumPy PCG64 seed 2026102301 and integer costs 1–20. The exact input SHA-256 is `46b70079fbccbbe620d01207d4ab0d2c7272286ab85eea153deb643627522a1a`.

| Method | Workers | Status | Points at 300/600/900/1200 s | Terminal points | Committed MILP calls | Runtime (s) | Audit |
|---|---:|---|---|---:|---:|---:|---|
| Standard (generalized PEA) | 1 | RIGHT_CENSORED | 72/111/143/176 | 176 | 2788 | 1200.160 | PASS |

`RIGHT_CENSORED` means the 1200 s budget elapsed before complete Pareto enumeration was certified. Counts report recovered nondominated points within the budget, not a proven full-front size. All checkpoint and terminal assignment witnesses were revalidated for feasibility and objective consistency. No independent full Pareto reference is included.

MILP calls count those belonging to completed oracle tasks committed by the controller before cutoff; individual worker journals also retain completed calls in unfinished oracles. Timing includes worker startup, coordination, and journal/checkpoint I/O, but excludes parent imports and input parsing.
