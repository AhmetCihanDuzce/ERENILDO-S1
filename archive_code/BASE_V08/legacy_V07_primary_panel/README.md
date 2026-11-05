# EREN–ILDO reproducibility code and seeds (V07)

English-only release paired with `EREN_ILDO_Manuscript_EN_V10.docx`. The release preserves the frozen common-Python/HiGHS PEA implementation, the separately status-checked V05 implementation, fixed benchmark inputs and archived Pareto references, runner/source records, environment recipes, and seed provenance. It adds the V08 publication-analysis snapshot for 516 primary records: 510 main-panel runs over 85 instances plus six TSP3-12-1 supplementary runs. Six later TSP3-10-5 reruns are retained separately as sensitivity evidence and do not increase the primary instance count.

## Reproduce the manuscript analysis

From `analysis_v08/`, use Python 3.12.14 with NumPy 2.3.5 and run:

```bash
python analyze_step2.py
python plot_figures_en.py
```

The analysis reads archived records and never launches a solver. It writes the ten summary/QA files in `outputs/`; `expected_outputs/` preserves the archived values for byte comparison. The recorded bootstrap configuration uses 50,000 resamples and master seed 20261018, with deterministic per-summary streams derived from SHA256. Raw terminal records and their reference sets are in `analysis_v08/evidence/`.

## Seeds and fixed instances

The benchmark inputs are fixed, source-identified files; no random-generation seed is applicable to the published KP/AP/TSP instances. The seed registry records bootstrap seeds used for the reported intervals and explicitly records that the historical HiGHS backend did not set a solver random seed.

## Scope and limitations

The four unfinished TSP3-12-1 one- and two-worker runs remain right-censored; the two four-worker records are complete. Later reruns are kept outside the main panel. Exact wall times are not expected to reproduce across machines or resource limits. The historical status-handling limitation is documented; the V05 corrected layer is a separate implementation and does not remeasure the historical 510 runs. The legacy root-level `expected/`, `metadata/`, and V05 analysis files are retained as historical software-validation material; the manuscript's current result analysis is under `analysis_v08/`.

No third-party full-text publications are redistributed. The 2026 generalized PEA implementation is a project reimplementation, not the original authors' C++ software. See `SOURCES_AND_ATTRIBUTION.md`, `DATA_DICTIONARY.md`, and `metadata/SEED_REGISTRY.csv`.
