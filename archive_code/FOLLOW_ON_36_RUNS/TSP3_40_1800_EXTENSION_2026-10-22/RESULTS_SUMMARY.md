# TSP3-40-1: 3-objective, 40-city extension cohort

## Experimental setup

One registered three-objective TSP instance (TSP3-40-1), six configurations: Standard and Block2, each with 1, 2, and 4 worker processes. Each run used a wall-clock budget of 1800 s with snapshots at 600, 1200, and 1800 s. The input and solver implementation are unchanged from the recorded extension protocol. This is an extension cohort and does not replace or overwrite frozen protocol results.

The terminal status is `RIGHT_CENSORED` for all six runs: the time limit was reached before the enumeration procedure proved completion. Therefore the reported objective vectors are observed nondominated points, not a certified complete Pareto front. Checkpoint witnesses were revalidated against the encoded TSP constraints. All checkpoint and terminal audits passed.

## Results

| Workers | Method | Runtime (s) | Observed points at 600/1200/1800 s | Terminal points | MILP calls | Audit |
|---:|---|---:|---:|---:|---:|---|
| 1 | standard | 1800.004 | 1/2/2 | 2 | 9 | PASS |
| 1 | block2 | 1800.009 | 1/2/2 | 2 | 6 | PASS |
| 2 | standard | 1800.006 | 1/2/2 | 2 | 9 | PASS |
| 2 | block2 | 1800.017 | 1/2/2 | 2 | 6 | PASS |
| 4 | standard | 1800.009 | 1/2/2 | 2 | 9 | PASS |
| 4 | block2 | 1800.004 | 1/2/2 | 2 | 6 | PASS |

## Common observed objective vectors

All six configurations returned the same two objective vectors (minimization):

- (19334, 17873, 4823)
- (19886, 17988, 4820)

These common observations show agreement among tested configurations for this instance and budget. They do not establish that no additional nondominated vectors exist. Point counts at checkpoints are cumulative snapshots; the checkpoint files preserve each accepted witness.

## Reproducibility and interruptions

The directory contains the original LP source, parsed JSON input, solver source, environment description, per-run journals, checkpoint snapshots, terminal records, and a restored batch manifest. Partial or failed attempts are isolated in `interrupted/` and excluded from result rows. The successful two-worker Block2 run was restarted from zero after its first attempt stopped before 600 s; the final successful run has all three checkpoint files. Four-worker launch debugging attempts are also retained separately.

Input SHA-256: `0ce457ea3760df4f6b63e09074db304fe972c61c0d10fde82a1561af7266f513`.
