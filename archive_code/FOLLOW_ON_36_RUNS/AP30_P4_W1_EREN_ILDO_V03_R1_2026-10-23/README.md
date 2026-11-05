# AP30 p=4, one-worker EREN–ILDO run

This single run uses Block2 (EREN–ILDO), one worker, and one HiGHS thread. Budget: 1200 s; snapshots: 300/600/900/1200 s. Objectives 1–3 match the official MOOLibrary AP30 p=3 instance. Objective 4 is a synthetic derived extension generated before performance runs using NumPy PCG64 seed 2026102301, integer costs 1–20. Input and solver source bytes match the prior AP30 cohorts.

`RIGHT_CENSORED` means the budget elapsed before full Pareto enumeration was certified.
