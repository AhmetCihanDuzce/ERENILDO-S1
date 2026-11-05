# AP30 three-objective one-worker experiments

Official MOOLibrary AP30 p=3 instance, solved with Standard (generalized PEA) and Block2 (EREN–ILDO), each using one worker and one HiGHS thread. Each run has a 1200 s wall-clock budget and 300/600/900/1200 s checkpoints. Exact input and solver-source bytes are reused from the completed two- and four-worker cohorts.

`RIGHT_CENSORED` means the budget elapsed without proof of complete Pareto enumeration. Checkpoint and terminal assignment witnesses are audited.
