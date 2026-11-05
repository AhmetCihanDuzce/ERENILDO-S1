# Sources and attribution

Scientific scope is the common Python/HiGHS implementation of generalized PEA with two alternative lexicographic oracles. The weighted lexicographic principle and the PEA tree/child rules are prior work; this release does not claim their invention or a direct speed comparison against the original authors' software. The research code names `standard` and `block2` refer to the two implementations used in the V04 panel.

- KP/AP: source-identified benchmark files associated with Kirlik and Sayın (2014), supplied through the project's preserved MOOLibrary source evidence. Exact DAT files and byte hashes are included.
- TSP: Pettersson test data associated in the project's primary-source audit with the three-objective and four-objective Figshare datasets: https://figshare.com/articles/4814695 and https://figshare.com/articles/4814698. Native LPs, source hashes, converted exact-cost DFJ JSONs and the original parser are included. Source costs are symmetric; directed arc variables do not imply asymmetric-cost experiments.
- Generalized PEA background: Prinz, Nemesch and Ruzika (2026), *A High-Performance Parallel Algorithm for Multi-Objective Integer Optimization*, https://arxiv.org/abs/2602.11872. The archived Python code is the project's reimplementation, not a distribution of original C++ code.
- V04 analysis and source reconciliation: the preserved V04 manuscript audit ZIP, P33 KP/AP split archives and V27 TSP incremental archive. `metadata/SOURCE_ARCHIVES_SHA256.csv` identifies the exact input archive bytes used to assemble this release.

Scientific source files are preserved unchanged. Release wrappers, manifests, documentation and flattening paths are packaging additions. Full nested source member paths and terminal byte hashes are retained in the provenance records. The inaccessible single-file P33 master is not a dependency of this release; the available split archives provide the relevant source evidence.

No third-party full-text articles are included. Existing source notices remain in the archived code. This packaging step does not invent a new license grant or alter benchmark ownership. A final public-deposit license and repository/DOI can be set by the authors with the final release; this snapshot does not fabricate a public repository or DOI.


## V05 revision

The historical source and primary evidence are unchanged. A separately versioned status-checked implementation and limited software-validation records are additional materials. See metadata/V05_CHANGELOG_EN.md and metadata/LITERATURE_AUDIT_V05_EN.md.
