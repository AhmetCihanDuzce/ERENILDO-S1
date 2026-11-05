from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((R/"SHA256_MANIFEST.json").read_text())
for rel,h in manifest.items():
 assert digest(R/rel)==h, f"SHA-256 mismatch: {rel}"
assert len(list((R/"evidence"/"primary").glob("*.json")))==516
assert len(list((R/"evidence"/"later_repeats").glob("*.json")))==6
assert len(list((R/"evidence"/"oracles").glob("*.json")))==86
assert len(list((R/"evidence"/"journals").glob("*.json")))==4
print(json.dumps({"status":"PASS","primary_runs":516,"main_panel_runs":510,"supplementary_runs":6,"later_sensitivity_runs":6,"independent_references":86,"journals":4,"file_hashes":len(manifest)},indent=2))
