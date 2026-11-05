# TSP3-40-1: 1800-second worker/method extension

## Scope

This is a separately labelled extension to the frozen larger-instance panel. It uses the first registered Pettersson–Özlen three-objective 40-city input (`TSP3-40-1`) and six sequential conditions: Standard PEA and EREN–ILDO/Block2 at 1, 2, and 4 workers. It does not replace or silently revise the frozen TSP n=40, four-worker panel.

Each condition receives one 1800-second run with snapshots at 600, 1200, and 1800 seconds. These are snapshots within a single run, not independent restarts. The six runs are executed in this order: (1) worker count 1, Standard then Block2; (2) worker count 2, Standard then Block2; (3) worker count 4, Standard then Block2. Every worker has one HiGHS thread.

## Input provenance and formulation

`raw/TSP3_Tests.zip` is the raw TSP3 archive retained with the TSP20 extension package. The selected LP file is `raw/TSP3-40-1.lp`; the input JSON is derived from its three objective coefficient blocks by `parse_petters_tsp_lp.py`. The parser checks all 1,560 directed arc coefficients per objective, zero diagonals, and symmetry. Source and derived-input SHA-256 digests are included in `inputs/TSP3-40-1.json` and `audit/PREFLIGHT.json`.

The runner uses the project's directed-arc binary MTZ formulation, not the original LP file verbatim. A sequential Hamiltonian witness is checked before the batch starts. The terminal audit rechecks each saved witness against the constraints and objective values. A time-censored run is not treated as proof that the full Pareto set was found; this input has no independent complete Pareto oracle in this package.

## Environment

See `ENVIRONMENT.json` for versions, CPU quota, memory limit, and permitted CPUs captured immediately before execution. Each run is single-threaded per worker and pins workers to separate CPUs; the controller is pinned to another permitted CPU.

## Files

- `src/`: runner and algorithm/model modules. The runner copy is configured for this 1800-second extension only.
- `raw/`: source LP and original raw TSP3 archive.
- `inputs/`: parsed, hash-identified input JSON.
- `runs/`: accepted-point journals, oracle journals, per-worker MILP call logs, progress, terminal records, and the three checkpoint snapshots for every run.
- `audit/`: preflight and post-run audit summary.
- `BATCH_PROGRESS.json`: atomically updated batch progress and per-run terminal audit.

## Re-run

From this directory, run:

```bash
python3 run_batch.py
```

The batch script refuses to overwrite existing files through the runner. If a condition was interrupted, preserve the partial files and start a separately named attempt; do not append its times to an earlier attempt.
