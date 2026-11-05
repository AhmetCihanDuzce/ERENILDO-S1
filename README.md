# Supplementary S1 Reproducibility code

Code accompanying *Reducing MILP Calls in Exact Pareto Enumeration through Lexicographic Objective Aggregation*.

Supplementary S1: **[GITHUB_SUPPLEMENTARY_S1_URL]**  
Supplementary S2 results and supporting material: **[GITHUB_SUPPLEMENTARY_S2_URL]**

This repository contains code and execution instructions. Inputs, complete reference sets where available, run results, checkpoint records, supporting notes, and audit outputs are in Supplementary S2. Extract the two distributions as sibling directories named `Supplementary_S1` and `Supplementary_S2`, or supply `--results /path/to/Supplementary_S2` explicitly. The root README and `reproduce.py` are the publication entry points; older instructions under `archive_code/` document their original snapshots.

## Installation

Use Linux for solver execution and CPU-affinity controls. The publication checks were run with Python 3.12.14. An isolated environment is recommended:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

NumPy 2.3.5 and SciPy 1.17.0 match the recorded software versions. SciPy supplies the HiGHS backend used by the code; standalone `highspy` is not required. Matplotlib 3.10.8 is used for optional figure regeneration. Historical timing records also include Python 3.13.5. New elapsed times depend on hardware and execution conditions.

## Verify the archived results

From this directory, use a **new output directory outside both repositories** for each command:

```bash
python reproduce.py verify --results ../Supplementary_S2 --out ../../verify_output
```

This checks both publication manifests, restores source-byte identities after decompression, verifies the 510 main-panel terminals against 85 reference sets, and audits all 612 primary records. The complete-record audit also checks 41,614 binary witnesses in the fixed-budget and larger-input cohorts, call identities, the four time-limited twelve-city TSP journals, and all 265 fully completed method pairs. It reads archived results without running optimization.

## Reproduce the primary statistical analysis

```bash
python reproduce.py analyze --results ../Supplementary_S2 --out ../../analysis_output
python reproduce.py analyze --results ../Supplementary_S2 --out ../../analysis_with_figures --figures
```

The nine primary-analysis CSV files must match the archived expected outputs byte for byte. The bootstrap has 50,000 resamples and master seed 20261018. These commands stage the original relative paths in the output directory and execute the frozen analysis; they do not run a solver. Optional plots regenerate the analysis figures. The figure files embedded in the supplied manuscript are separately preserved in S2 under `figures/manuscript/`.

## Validate solver-state handling

```bash
python reproduce.py test --results ../Supplementary_S2 --out ../../status_tests
python reproduce.py test --results ../Supplementary_S2 --out ../../status_and_regression_tests --smoke
```

The unit suite covers 99 solver-state scenarios in ten test methods. `--smoke` additionally runs eight small regression executions and two injected worker failures. Validation results remain separate from primary benchmark timings.

## Prepare or execute an original main-panel instance

```bash
python reproduce.py prepare --instance AP_p-3_n-5_ins-1 --method eren-ildo --workers 1 --out ../../prepared_ap
```

Choose the exact identifier from `Supplementary_S2/archive_code_data/BASE_V08/legacy_V07_primary_panel/metadata/BENCHMARK_MANIFEST_85.csv`. Preparation stages the recorded runner, validated core, original input, reference, and schedule. Add `--execute` to run the prepared instance. The checked implementation is used for new runs; historical terminal records and primary tables remain frozen. The preparation report lists the recorded versions and timing protocol. The archived general-purpose reproduction scripts are retained for provenance; use this entry point for publication analysis.

## Run a JSON-format instance

`Supplementary_S2/tables/input_registry.csv` identifies the JSON input files. Use `run` for the additional fixed-budget and larger cases; use `prepare` for the original 85-input main panel, whose recorded models and schedules are staged together.

```bash
python reproduce.py run --instance KP_p3_n50_ins1 --method eren-ildo --workers 1 --budget 1200 --checkpoints 300,600,900,1200 --out ../../kp50_run
python reproduce.py run --instance TSP3-40-1 --method standard --workers 1 --budget 1800 --checkpoints 600,1200,1800 --out ../../tsp40_run
```

Alternatively provide `--input /path/to/input.json`. Methods are `standard` and `eren-ildo`; `block2` is an accepted archival alias for EREN–ILDO. Use 1, 2, or 4 workers and at least one additional allowed CPU for coordination. Registered performance schedules are 1200 s with 300/600/900/1200 s checkpoints and 1800 s with 600/1200/1800 s checkpoints. A custom budget requires `--qa` and is marked as a software test.

The runner requires an optimal solver status at every optimization stage before accepting an oracle solution. Only proven first-stage infeasibility closes an empty region. Worker errors propagate as `ERROR`. `SEARCH_COMPLETED` means enumeration completed; `RIGHT_CENSORED` means the overall cap was reached. In the latter case, reported images are accepted solutions found by the deadline, while complete-front enumeration remains unproved.

## Source provenance

`src/` contains the portable checked core and family runner. `provenance/portable_source_mapping.csv` records the original and distributed source hashes. Adaptations concern the local import root, acceptance of both registered checkpoint schedules, and the publication protocol label; search and model logic are preserved. `archive_code/` and `archive_support_tools/` retain historical code and software-test sources. Development-version strings in these archives identify provenance rather than additional methods.

`provenance/code_snapshot_index.csv` maps every original code-package file to S1 or S2 and permits lossless reconstruction of the supplied source snapshot. Original input and terminal bytes are preserved; large records in S2 use lossless gzip compression. Supporting scope and measurement details are in S2, Notes 1–6.
