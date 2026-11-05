# KP n=50, p=3, ins-1 — completed continuation panel

Official MOOLibrary instance `KP_p-3_n-50_ins-1.dat` was used. All runs shared normalized input SHA-256 `ea60a4c882df8b573b9bc0419176fcffbc946855c824899c6289e2098ab41717`, SciPy/HiGHS, and one solver thread per worker. No synthetic input was used.

## Results

| Workers | Method | Status | Search completion (s) | Points | MILP calls |
|---:|---|---|---:|---:|---:|
| 1 | Standard | SEARCH_COMPLETED | 480.628 | 507 | 2957 |
| 1 | EREN–ILDO (Block2) | SEARCH_COMPLETED | 410.186 | 507 | 1986 |
| 2 | Standard | SEARCH_COMPLETED | 203.924 | 507 | 2957 |
| 2 | EREN–ILDO (Block2) | SEARCH_COMPLETED | 244.320 | 507 | 1986 |
| 4 | Standard | SEARCH_COMPLETED | 203.962 | 507 | 2957 |
| 4 | EREN–ILDO (Block2) | SEARCH_COMPLETED | 135.477 | 507 | 1986 |

All six terminal objective sets are identical (507 vectors). Each method-worker cell has its own run; comparisons are descriptive.

## Matched method comparisons

EREN–ILDO used 971 fewer MILP calls at every worker count (32.84%). Its completion-time difference varied: at 1 worker it was 70.442 s faster (14.66%); at 2 workers it was 40.396 s slower (19.81%); at 4 workers it was 68.484 s faster (33.58%). Therefore lower MILP-call count did not imply lower wall time in every configuration.

## Checkpoints and worker scaling

Both 4-worker methods completed before 300 s; their 300/600/900/1200 s checkpoint files carry forward the completed 507-point set. The 1-worker Standard and Block2 runs had 333 and 381 points at 300 s, respectively; their union contained 381 nondominated points, with 48 points found only by Block2 at that checkpoint.

| Method | 1 worker (s) | 2 workers (s) | 4 workers (s) | Speedup 1→4 |
|---|---:|---:|---:|---:|
| Standard | 480.628 | 203.924 | 203.962 | 2.356× |
| EREN–ILDO (Block2) | 410.186 | 244.320 | 135.477 | 3.027× |

For Standard, 2 and 4 workers had nearly identical observed times. For Block2, time decreased as workers increased in this single run. These results are descriptive and not statistical estimates.

All new witnesses, objective values, uniqueness, mutual nondominance, checkpoint records, and MILP-call identities passed audit; terminal sets matched the five previously audited runs. The runner reported `SEARCH_COMPLETED`, but an independent full Pareto oracle was unavailable, so this status and cross-configuration agreement do not independently prove global completeness.
