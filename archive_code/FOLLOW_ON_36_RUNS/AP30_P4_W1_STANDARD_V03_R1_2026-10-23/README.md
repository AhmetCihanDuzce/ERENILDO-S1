# AP30 p=4, one-worker Standard run

This single run solves the four-objective AP30 derived extension with Standard (generalized PEA), one worker and one HiGHS thread. Budget: 1200 s; snapshots: 300/600/900/1200 s. The four-objective input is a synthetic extension: objectives 1–3 are from the official MOOLibrary p=3 AP30 instance, and objective 4 was generated before performance runs using NumPy PCG64 seed 2026102301, integer costs 1–20. Exact input and solver source bytes are reused from the AP30 two- and four-worker cohorts.

`RIGHT_CENSORED` indicates that the time budget elapsed without certification of complete Pareto enumeration.
