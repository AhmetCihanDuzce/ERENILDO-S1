# TSP20 Extension Results

**Batch:** 12/12 runs completed; every run used a 1200 s cap and checkpoints at 300, 600, 900, and 1200 s. **All 12 runs ended RIGHT_CENSORED**; the full Pareto sets were not certified within the cap. All observed solution witnesses passed the independent feasibility checks and each reported observed set was nondominated. There is no independent full-front oracle for n=20.

The extension uses the first registered replicate (i01) for each group, TSP3-20-1 and TSP4-20-1. Each p,n group has five official replicates; this is not an all-replicate study. Source identity and parsed-input hashes are in `PROVENANCE.json`.

| Objectives | Workers | Method | # at 300 s | # at 600 s | # at 900 s | # at 1200 s | End status | Audit |
|---:|---:|---|---:|---:|---:|---:|---|---|
| 3 | 1 | EREN–ILDO (Block2) | 4 | 6 | 9 | 11 | RIGHT_CENSORED | PASS |
| 3 | 1 | Standard | 3 | 5 | 8 | 11 | RIGHT_CENSORED | PASS_WITH_JOURNAL_NOTES |
| 3 | 2 | EREN–ILDO (Block2) | 4 | 8 | 11 | 15 | RIGHT_CENSORED | PASS |
| 3 | 2 | Standard | 4 | 7 | 9 | 14 | RIGHT_CENSORED | PASS |
| 3 | 4 | EREN–ILDO (Block2) | 6 | 13 | 20 | 27 | RIGHT_CENSORED | PASS_WITH_JOURNAL_NOTES |
| 3 | 4 | Standard | 6 | 11 | 19 | 24 | RIGHT_CENSORED | PASS_WITH_JOURNAL_NOTES |
| 4 | 1 | EREN–ILDO (Block2) | 1 | 3 | 5 | 6 | RIGHT_CENSORED | PASS |
| 4 | 1 | Standard | 3 | 3 | 4 | 6 | RIGHT_CENSORED | PASS_WITH_JOURNAL_NOTES |
| 4 | 2 | EREN–ILDO (Block2) | 3 | 4 | 8 | 9 | RIGHT_CENSORED | PASS |
| 4 | 2 | Standard | 3 | 4 | 7 | 9 | RIGHT_CENSORED | PASS |
| 4 | 4 | EREN–ILDO (Block2) | 4 | 7 | 10 | 13 | RIGHT_CENSORED | PASS_WITH_JOURNAL_NOTES |
| 4 | 4 | Standard | 4 | 8 | 12 | 15 | RIGHT_CENSORED | PASS_WITH_JOURNAL_NOTES |

## Interpretation

- On TSP3-20-1, the final observed-set sizes by worker count were Standard: 11, 14, and 24; EREN–ILDO: 11, 15, and 27 (1, 2, and 4 workers, respectively). The observed sizes increased with worker count for both methods.
- On TSP4-20-1, final observed-set sizes were Standard: 6, 9, and 15; EREN–ILDO: 6, 9, and 13. The 2-worker outcomes tied; Standard returned two more observed points at 4 workers.
- These are descriptive results from one replicate per p,n group, not repeated-seed inference. Since all runs were right-censored, point counts describe the nondominated solutions observed by each checkpoint and do not establish complete Pareto fronts or statistical superiority.
- All audits passed the main witness feasibility and observed-set nondominance checks. Six audits report `PASS_WITH_JOURNAL_NOTES`: the individual MILP journal count differs from the controller aggregate; both records were retained without reconstruction. See each `audits/*.json` and original call logs.

## Run protocol

- V03 R1 TSP extension, 1200 s total runtime, checkpoints at 300/600/900/1200 s.
- Standard PEA and EREN–ILDO/Block2; 1, 2, or 4 worker processes; one HiGHS solver thread per worker.
- Official Pettersson–Özlen LP objective coefficients were parsed and validated. The solver used the shared directed-arc binary MTZ formulation. The archived LP files were not executed verbatim.
- Runs were sequential. Inputs, runner source, validator, execution logs, checkpoint JSON, terminal JSON, witnesses, audits, and source archives are preserved in this package.

## Reproduction

Run `python run_batch.py` from the package root. The script executes all 12 cells in the recorded order, writes logs and run JSON under `runs/`, and independently audits each completed run into `audits/`. Existing run files are never overwritten.
