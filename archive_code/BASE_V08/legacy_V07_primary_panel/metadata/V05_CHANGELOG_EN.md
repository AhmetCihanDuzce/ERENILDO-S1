# V05 revision record

The primary evidence panel is unchanged: 85 instances, 510 archived completed
runs, and 255 method pairs. The V04 statistical code, source analysis inputs,
expected numeric tables, Figure 1, independent reference files, and original
terminal JSON bytes are preserved. V05 does not admit new timing observations.

## Manuscript changes

- Narrow the title and contribution to lexicographic stage aggregation within
  the specified generalized PEA reimplementation.
- Explain the direct two-stage/augmented scalarization connections to QSM,
  Kirlik--Sayin, DPA, and Karsu--Ulus, and the mathematical precedents in
  Ozlen--Azizoglu and FPA. Distinguish internal lexicographic priorities from
  lexicographically ordered anytime outputs in Foschini et al. (2026).
- Add four references: Ozlen--Azizoglu (2009), Karsu--Ulus (2022), Foschini et al.
  (2026), and Beiranvand--Hare--Lucet (2017). Update the triobjective PEA entry
  to the publisher's volume 38(5), 1651--1672; retain its publisher Cite as year
  of 2025.
- Identify the basic PEA variant and explicitly exclude the recursive
  infeasibility-avoidance/start-solution improvement in Section 5.1 of the
  generalized PEA preprint from the implemented baseline.
- Replace stale counter-provenance wording with direct archived-counter
  verification: 1,530 fields over 255 pairs, with no mismatch.
- Report the existing-data distinction between 43,615 feasible oracle calls
  and the sum of 13,608 per-instance Pareto cardinalities; 84/85 instances
  have more feasible oracle calls than accepted distinct images.
- Disclose the historical status-handling limitation and the scope of the
  V05 correction. Consolidate repeated caveats and separate uncertainty from
  repeated-runtime variance. Renumber tables consistently; numeric cells and
  all 19 displayed equations in each language remain unchanged.

## Corrected implementation

`src/frozen/` remains the historical implementation. `src/validated/common/`
is the separately versioned V05 implementation. It preserves the objective
bounds, weights, priorities, and PEA child-generation rules.

The V05 backend requires successful HiGHS execution. Only a proven infeasible
model may return a missing solution. Other nonoptimal statuses raise
`SolverUnresolvedError`. The oracle independently checks the returned status
and rejects infeasibility after an already optimal stage as inconsistent.
Existing worker ERROR handling then prevents exact acceptance and prevents
the unresolved task from incrementing the infeasible counter.

The historical code could conflate nonoptimal statuses with infeasibility.
The original aggregate terminals do not preserve every individual MILP status;
V05 does not retrospectively prove that this path was never taken. Full archived
front/reference equality supports the accepted output sets. New software tests
do not remeasure or replace all 510 historical runs.

## Checks actually performed

- Ten unit-test methods cover 99 backend/oracle/traversal scenarios, using
  mocked statuses without optimization.
- Eight small end-to-end validation runs: both methods on AP p3 n5 instance 1,
  KP p5 n10 instance 1, and TSP p4 n6 instance 1 at one worker, plus both methods
  on the same small TSP at two workers. These execute 2,593 MILP solves.
- All eight match the archived full reference sets and feasible, infeasible,
  scalarization, and MILP counters. Their elapsed times are validation records,
  excluded from every primary performance table and bootstrap calculation.
- Two injected worker checks return a time-limit status at the oracle boundary,
  execute zero optimization calls, produce FAILED_WORKER, increment no infeasible
  counter, and cannot receive exact acceptance.
- The archived 510-terminal/reference evidence and original analysis are checked
  independently of these software regressions.

The validation is limited to the stated cases. It is neither a renewed performance
study nor a proof of numerical exactness for arbitrary coefficients or instances.

The Turkish model appendix also uses 16 native editable inline Word math symbols in place of plain-text variable notation. This is a notation change, with all displayed equations retained.
