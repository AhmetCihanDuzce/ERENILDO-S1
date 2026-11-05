# V03 R1 Results Overview

## Scope and evidence boundary

The V03 R1 extension used a 1,200 s cap and checkpoints at 300, 600, 900, and 1,200 s. It covers ten benchmark instances and 60 primary executions: 15 searches completed and 45 were right-censored at the cap. One separately labelled Standard, two-worker repeat for KP p=4, n=40 is supplementary evidence, not a new primary cell.

The older 85-instance, 510-run completed panel remains a separate historical cohort with its own protocol and records. No aggregate statistic combines that panel with V03 R1. The frozen 108-cell R1 matrix was not completed: 60 cells have current runs, six KP p=3, n=30 cells retain historical evidence (worker-specific timing was located only for one worker), and 42 cells have neither a current R1 run nor historical reuse. The experiment stage is closed at the present evidence boundary. The current R1 inputs have no independent complete Pareto reference files. Witness feasibility and within-set nondominance were audited; equality of objective sets between methods is reported only for six fully completed paired cells. It is not independent full-front validation. Censored point counts are progress records, not complete fronts.

| Family | p | n | Primary runs | Completed | Right-censored | Completed worker pairs | Observed points |
|---|---:|---:|---:|---:|---:|---|---:|
| AP | 3 | 20 | 6 | 1 | 5 | none | 554–2404 |
| AP | 4 | 20 | 6 | 0 | 6 | none | 257–594 |
| AP | 3 | 25 | 6 | 0 | 6 | none | 528–1419 |
| AP | 4 | 25 | 6 | 0 | 6 | none | 189–483 |
| KP | 4 | 30 | 6 | 5 | 1 | 2,4 | 457–563 |
| KP | 3 | 40 | 6 | 6 | 0 | 1,2,4 | 486–486 |
| KP | 4 | 40 | 6 | 3 | 3 | 4 | 590–901 |
| TSP | 3 | 15 | 6 | 0 | 6 | none | 31–111 |
| TSP | 4 | 15 | 6 | 0 | 6 | none | 18–45 |
| TSP | 4 | 25 | 6 | 0 | 6 | none | 3–8 |

## Fully completed matched comparisons

| Instance | Workers | Standard (s; MILPs) | EREN-ILDO (s; MILPs) | Call reduction | Elapsed ratio EREN/Standard | Sets equal |
|---|---:|---:|---:|---:|---:|---|
| KP_n40_p3_i1 | 1 | 515.867; 2,781 | 589.806; 1,877 | 32.51% | 1.143 | Yes |
| KP_n40_p3_i1 | 2 | 148.933; 2,781 | 367.818; 1,877 | 32.51% | 2.470 | Yes |
| KP_n40_p3_i1 | 4 | 82.103; 2,781 | 91.195; 1,877 | 32.51% | 1.111 | Yes |
| KP_n40_p4_i1 | 4 | 911.244; 16,583 | 648.568; 12,576 | 24.16% | 0.712 | Yes |
| KP_n30_p4_i1 | 2 | 546.627; 10,121 | 454.037; 7,717 | 23.75% | 0.831 | Yes |
| KP_n30_p4_i1 | 4 | 307.595; 10,121 | 267.120; 7,717 | 23.75% | 0.868 | Yes |

Across the three fully observed problem cases, completed MILP calls fell by 23.75% for KP p=4, n=30; 32.51% for KP p=3, n=40; and 24.16% for KP p=4, n=40. The six elapsed-time ratios ranged from 0.712 to 2.470. With one execution per cell, these are descriptive observations, not replicated timing estimates.

The AP p=3, n=20 four-worker EREN-ILDO run completed in 1,066.420 s with 2,404 observed images, while Standard was right-censored at 1,200 s with 1,650. No independent reference was available and the pair did not both complete.

## Supplemental repeat

The KP p=4, n=40 Standard two-worker repeat was right-censored at 1,200.048 s with 714 images, compared with 895 in the original primary run. The repeated set was a subset of the original and added zero new points. The original remains the primary record.

## Historical KP p=3, n=30 evidence

The KP_n30_p3_i5 records are old 1,800 s protocol results and not R1 runs. Only one-worker terminal records were located: Standard 3.349 s and EREN-ILDO 2.936 s, each with 69 identical objective points. They are excluded from R1 worker timing and scaling analyses. Worker-2 and worker-4 times are unavailable.

Run-level and checkpoint rows are provided in the CSV files. Raw terminals, checkpoints, audits, and code hashes are preserved in the accompanying evidence archive.
