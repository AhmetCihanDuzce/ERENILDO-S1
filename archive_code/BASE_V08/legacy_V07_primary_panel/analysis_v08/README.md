# V08 analysis reproduction

This folder contains the manuscript's frozen 516-record analysis panel: 510 main-panel records and six TSP3-12-1 supplementary records. It also retains six later TSP3-10-5 reruns in a separate sensitivity folder. These later reruns are not additional independent benchmark instances.

Run `python analyze_step2.py` with NumPy installed to recreate the CSV summaries and QA record from the archived terminal evidence. No solver is launched. The analysis configuration records 50,000 resamples and master seed 20261018; individual deterministic streams are derived from SHA256 of the master seed and summary label. Run `python plot_figures_en.py` to regenerate three English figures from the output tables.

The source evidence, observed outputs and the two publication panels are separate: 516 primary records = 510 main + six supplementary; the six later reruns are sensitivity evidence only. Four TSP3-12-1 one- and two-worker records are right-censored and are not completion times.
