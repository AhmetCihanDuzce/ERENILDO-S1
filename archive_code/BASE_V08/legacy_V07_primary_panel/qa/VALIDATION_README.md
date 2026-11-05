# Validation performed for V04/R1

Date: 16 October 2026. No new MILP solve, optimizer model execution, or reference enumeration was run.

- All 510 original terminal bytes were matched to the V04 panel. All full objective-vector sets equal the supplied archived independent reference sets. Identity, completion/no-pending flags, paired counter formulas and worker invariance pass. This checks archived evidence; it is not a fresh generation of all independent fronts or a comparison of search-node sets.
- The unchanged V04 analysis regenerated eight CSV files plus ANALYSIS_QA.json byte for byte. Bootstrap seed 20261016, 50000 resamples. Figure 1 was regenerated from the verified table; PDF/image byte identity is not required.
- All 15 native LPs were reparsed and every TSP cost coefficient matched the frozen dense-DFJ input JSONs.
- All 510 schedule selections matched the required cell and source identity. All 9 archived runner versions were staged in fresh directories, their original hashes checked, help entry points invoked, and model imports/builds checked without solving. Independent-reference plans were checked without enumeration.
- Archived C++ reference sources were checked with g++ -std=c++17 -fsyntax-only when available; see PACKAGE_QA.json. Their enumeration/DP was not executed.
- Final ZIPs were extracted to a new directory and their integrity/data checker was run. No speed or hardware-equivalence result follows from these packaging checks.
