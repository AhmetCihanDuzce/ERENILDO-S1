#!/usr/bin/env python3
"""Parse the archived Pettersson–Özlen LP objective blocks into runner JSON."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "raw" / "TSP3-40-1.lp"
OUTPUT = ROOT / "inputs" / "TSP3-40-1.json"
N = 40

term_re = re.compile(r"\s*(?:\+\s*)?(\d+)\s+X(\d+)_(\d+)\s*")
costs = [[[0 for _ in range(N)] for _ in range(N)] for _ in range(3)]
obj = 0
counts = [0, 0, 0]
for line in SOURCE.read_text(encoding="utf-8").splitlines():
    match = term_re.fullmatch(line)
    if match:
        value, i, j = map(int, match.groups())
        if not (1 <= i <= N and 1 <= j <= N and i != j):
            raise ValueError(f"Invalid arc coefficient: {line!r}")
        if costs[obj][i - 1][j - 1] != 0:
            raise ValueError(f"Duplicate coefficient in objective {obj + 1}: {line!r}")
        costs[obj][i - 1][j - 1] = value
        counts[obj] += 1
        continue
    marker = re.fullmatch(r"<\s*([123])", line.strip())
    if marker and obj < 3 and int(marker.group(1)) == obj + 1 and counts[obj] > 0:
        obj += 1
        if obj == 3:
            break

if obj != 3 or counts != [N * (N - 1)] * 3:
    raise ValueError(f"Expected three complete cost matrices, markers={obj}, terms={counts}")
for k, matrix in enumerate(costs):
    if any(matrix[i][i] != 0 for i in range(N)):
        raise ValueError(f"Nonzero diagonal in objective {k + 1}")
    if any(matrix[i][j] <= 0 for i in range(N) for j in range(N) if i != j):
        raise ValueError(f"Missing/nonpositive cost in objective {k + 1}")
    if any(matrix[i][j] != matrix[j][i] for i in range(N) for j in range(N)):
        raise ValueError(f"Source is not symmetric in objective {k + 1}")

source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
spec = {
    "schema": "EREN-ILDO/1",
    "problem": "TSP",
    "instance": "TSP3-40-1",
    "n": N,
    "p": 3,
    "costs": costs,
    "directed": True,
    "formulation": "mtz_binary",
    "source": {
        "archive": "TSP3_Tests.zip",
        "archive_sha256": hashlib.sha256((ROOT / "raw" / "TSP3_Tests.zip").read_bytes()).hexdigest(),
        "source_lp": "TSP3-40-1.lp",
        "source_lp_sha256": source_sha,
        "coefficient_terms_per_objective": counts,
        "symmetry_verified": True,
    },
}
OUTPUT.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({
    "output": str(OUTPUT),
    "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
    "source_lp_sha256": source_sha,
    "arc_coefficient_terms": counts,
    "symmetric": True,
    "min_cost": min(v for m in costs for row in m for v in row if v),
    "max_cost": max(v for m in costs for row in m for v in row),
}, sort_keys=True))
