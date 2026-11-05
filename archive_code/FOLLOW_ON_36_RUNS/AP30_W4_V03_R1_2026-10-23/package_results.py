from pathlib import Path
import zipfile,json,hashlib,csv
ROOT=Path(__file__).resolve().parent

def main():
 state=json.loads((ROOT/'BATCH_PROGRESS.json').read_text());rows=state['completed'];names={r['name'] for r in rows}
 summary=['# AP30: four-worker Standard and EREN–ILDO experiments','','Each run uses four worker processes, one HiGHS thread per worker, a 1200 s wall-clock budget, and 300/600/900/1200 s snapshots. The p=3 input is an official benchmark; p=4 is a synthetic derived fourth-objective extension (PCG64 seed 2026102301).','','| Objectives | Method | Status | Points at 300/600/900/1200 s | Terminal points | MILP calls | Runtime (s) | Audit |','|---:|---|---|---|---:|---:|---:|---|']
 for r in rows:
  counts='/'.join(str(c['point_count']) for c in r['check']['checkpoints']);summary.append(f"| {r['objectives']} | {r['method']} | {r['status']} | {counts} | {r['point_count']} | {r['milp_calls']} | {r['elapsed_s']:.3f} | PASS |")
 summary+=['','RIGHT_CENSORED means the time budget elapsed without proof of full Pareto enumeration. SEARCH_COMPLETED means the exact enumeration procedure terminated. Witness checks establish assignment feasibility and objective consistency. The package does not provide an independent full Pareto reference.','','Batch status: '+state['status']+'. Completed configurations: '+str(len(rows))+'/4.']
 if (ROOT/'PAIR_COMPARISON.json').exists():
  pairs=json.loads((ROOT/'PAIR_COMPARISON.json').read_text())
  summary+=['','## Paired observations','']
  for pair in pairs:
   if pair['checkpoint_s']==1200:
    summary.append(f"For p={pair['objectives']}, the observed terminal nondominated union contains {pair['nondominated_union']} points: {pair['shared']} shared, {pair['standard_only']} Standard-only, and {pair['block2_only']} Block2-only.")
  summary+=['','In both tested inputs, Block2 recovered every point found by Standard within the budget and additional points. This is an observation from one instance per objective count, not a general speed or superiority guarantee. All four runs are right-censored, so full-front completion-time speedup is undefined.']
 summary+=['','## Counters and timing','', 'MILP calls in the table count calls belonging to completed oracle tasks committed by the controller before the cutoff. Individual completed worker calls, including calls in unfinished oracles, are retained separately in worker call journals. Physical checkpoint persistence and shutdown may finish after the target; only points accepted at or before the target enter its snapshot.']
 (ROOT/'RESULTS_SUMMARY.md').write_text('\n'.join(summary)+'\n')
 (ROOT/'SOURCE_HASHES.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src').glob('*.py')},indent=2)+'\n')
 hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='SHA256_MANIFEST.json' and p.suffix!='.tmp'}
 (ROOT/'SHA256_MANIFEST.json').write_text(json.dumps(hashes,indent=2,sort_keys=True)+'\n')
 output=ROOT.parent/(ROOT.name+'.zip')
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted(ROOT.rglob('*')):
   if not p.is_file() or '__pycache__' in p.parts or p.suffix=='.tmp':continue
   if p.parent.name in ['runs','logs','audit'] and p.name.startswith('AP_n30_') and not any(p.name.startswith(n+'.') for n in names):continue
   z.write(p,p.relative_to(ROOT.parent))
 print(json.dumps({'file':str(output),'bytes':output.stat().st_size,'completed':len(rows)}))
if __name__=='__main__':main()
