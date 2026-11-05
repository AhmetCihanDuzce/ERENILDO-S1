#!/usr/bin/env python3
"""Run the six approved TSP3-40-1 conditions sequentially with 600s snapshots."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
import run_checkpoint_multi as runner  # noqa: E402

INPUT = ROOT / "inputs" / "TSP3-40-1.json"
RUNS = ROOT / "runs"
DEADLINES = (600, 1200, 1800)
BUDGET = 1800
CONFIGS = [
    (1, "standard"), (1, "block2"),
    (2, "standard"), (2, "block2"),
    (4, "standard"), (4, "block2"),
]


def save(path: Path, obj: object) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with tmp.open("rb") as f:
        os.fsync(f.fileno())
    tmp.replace(path)


def audit(prefix: Path, result: dict) -> dict:
    P, d = runner.load(INPUT)
    expected = [600, 1200, 1800]
    files = [prefix.with_name(prefix.name + f".checkpoint_{t}.json") for t in expected]
    missing = [str(p) for p in files if not p.is_file()]
    if missing:
        raise RuntimeError(f"Missing checkpoint files: {missing}")
    cp_summary = []
    for path in files:
        cp = json.loads(path.read_text(encoding="utf-8"))
        witnesses = cp["accepted_points_with_witnesses"]
        if cp["point_count"] != len(witnesses):
            raise RuntimeError(f"Checkpoint count mismatch: {path.name}")
        vectors = set()
        for row in witnesses:
            y = runner.validate_witness(P, d, row["x"], y=row["y_min"])
            vectors.add(tuple(map(int, y)))
        if len(vectors) != cp["point_count"]:
            raise RuntimeError(f"Duplicate objective vectors: {path.name}")
        cp_summary.append({"checkpoint_s": cp["checkpoint_s"], "status": cp["status"], "point_count": cp["point_count"], "validated_witnesses": len(vectors)})
    return {
        "audit": "PASS",
        "terminal_status": result["status"],
        "terminal_point_count": result["point_count"],
        "terminal_milp_calls": result["counters"]["milp_calls"],
        "input_sha256": result["input_sha256"],
        "checkpoints": cp_summary,
    }


def main() -> int:
    progress_path = ROOT / "BATCH_PROGRESS.json"
    progress = {"batch": "TSP3-40-1 extension", "budget_s": BUDGET, "checkpoints_s": list(DEADLINES), "order": CONFIGS, "next_index_1based": 1, "completed": [], "current": None}
    save(progress_path, progress)
    for index, (workers, method) in enumerate(CONFIGS, start=1):
        name = f"TSP3-40-1_w{workers}_{method}"
        prefix = RUNS / name
        progress["next_index_1based"] = index
        progress["current"] = {"index": index, "name": name, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        save(progress_path, progress)
        print(json.dumps({"event": "RUN_START", "index": index, "total": len(CONFIGS), "name": name}), flush=True)
        result = runner.run(str(INPUT), method, BUDGET, DEADLINES, str(prefix), workers, qa=False)
        try:
            checked = audit(prefix, result)
        except Exception as exc:
            checked = {"audit": "FAIL", "error": repr(exc)}
        row = {
            "index": index,
            "name": name,
            "workers": workers,
            "method": method,
            "budget_s": BUDGET,
            "checkpoints_s": list(DEADLINES),
            "status": result["status"],
            "elapsed_s": result["elapsed_s"],
            "search_completed_elapsed_s": result["search_completed_elapsed_s"],
            "point_count": result["point_count"],
            "milp_calls": result["counters"]["milp_calls"],
            "check": checked,
            "terminal_sha256": hashlib.sha256(prefix.with_suffix(".terminal.json").read_bytes()).hexdigest() if prefix.with_suffix(".terminal.json").exists() else None,
            "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        progress["completed"].append(row)
        progress["current"] = None
        progress["next_index_1based"] = index + 1
        save(progress_path, progress)
        print(json.dumps({"event": "RUN_END", **row}), flush=True)
    progress["status"] = "BATCH_COMPLETE"
    progress["next_index_1based"] = None
    save(progress_path, progress)
    return 0 if all(x["check"]["audit"] == "PASS" for x in progress["completed"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
