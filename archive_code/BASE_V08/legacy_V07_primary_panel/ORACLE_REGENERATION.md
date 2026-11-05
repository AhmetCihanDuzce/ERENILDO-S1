# Independent reference regeneration

The fast `verify_release.py` checker compares all 510 original terminal vector sets to the 85 **supplied** archived independent references. It does not regenerate those references. If a fresh independent reconstruction is needed, the following opt-in wrapper is provided:

```bash
python scripts/regenerate_reference.py --instance KP_p-4_n-10_ins-1 --out reference_runs/KP_example
python scripts/regenerate_reference.py --instance AP_p-3_n-15_ins-1 --out reference_runs/AP15_example
python scripts/regenerate_reference.py --instance TSP3-10-1 --out reference_runs/TSP_example
```

These commands only print plans. Explicitly append `--execute` to perform a fresh reference calculation. Use a new output folder. NumPy is needed; KP/AP also require a C++17 compiler such as `g++`. No HiGHS or other MILP solver is called by the reference wrapper.

- **KP:** the unchanged archived C++ enumerator examines every binary selection in Gray-code order, filters the capacity inequality and extracts the exact integer nondominated objective set. KP profits are converted to minimization signs exactly as in the frozen input model.
- **AP n=5,10:** the unchanged C++ assignment enumerator examines all permutations. n=10 has 10! assignments and can be expensive.
- **AP n=15:** the unchanged independent subset dynamic program retains the complete nondominated cost set per column subset. It does **not** enumerate 15! permutations. Memory/time can be substantial.
- **TSP n=6,8,10:** the release wrapper enumerates all (n-1)! Hamilton tours with city 0 fixed and computes objective vectors using integer arithmetic from the frozen cost arrays. It applies an independent lexicographic skyline scan, then compares the complete vector set to the supplied reference. n=10 has 9!=362,880 tours. Symmetric reverse tours are both examined, so their duplicate images are removed before the skyline scan.

The wrapper writes a new reference and a full-set match result, leaving archived references untouched. Its staging and input conversion are release additions; the archived C++ sources and original TSP reference script are retained separately under `src/frozen/independent/`. Reference-generation entry points in historical files may contain historical paths; use this wrapper for the relocatable workflow.

**Release QA scope:** fresh enumeration/DP was not run for this packaging task. Syntax, plans and model/source conversion were checked; the archived fronts and completed solver outputs were not replaced. A later release may record optional fresh reference regeneration separately from solver experiments.
