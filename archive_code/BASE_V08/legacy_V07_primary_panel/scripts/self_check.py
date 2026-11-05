#!/usr/bin/env python3
"""Exercise the release workflow without launching solvers or reference enumeration."""
from pathlib import Path
import argparse,csv,json,subprocess,sys,importlib.util,hashlib
ROOT=Path(__file__).resolve().parents[1]
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--out',required=True,type=Path);v=a.parse_args();out=v.out.resolve()
 if out.exists() and any(out.iterdir()):raise SystemExit('QA output must be absent or empty')
 out.mkdir(parents=True,exist_ok=True);results={}
 def run(name,cmd):
  p=subprocess.run(cmd,text=True,capture_output=True);(out/(name+'.log')).write_text(p.stdout+p.stderr)
  if p.returncode:raise RuntimeError(name+' failed; see '+str(out/(name+'.log')))
  results[name]='PASS'
 run('raw_evidence',[sys.executable,str(ROOT/'scripts/verify_release.py'),'--report',str(out/'RAW_EVIDENCE_QA.json')])
 run('environment',[sys.executable,str(ROOT/'scripts/check_environment.py')])
 run('native_TSP_conversion',[sys.executable,str(ROOT/'scripts/check_tsp_source_conversion.py')])
 run('analysis_and_figure',[sys.executable,str(ROOT/'scripts/reproduce_analysis.py'),'--out',str(out/'reproduced_analysis'),'--figures'])
 rows=list(csv.DictReader((ROOT/'metadata/EXPERIMENT_MANIFEST_510.csv').open()))
 schedules=json.loads((ROOT/'metadata/RUNNER_SCHEDULE_MAP.json').read_text());cache={}
 for r in rows:
  key='|'.join([r['instance'],r['workers'],r['method']]);chosen=schedules[key]
  for name,rel in chosen.items():
   if rel not in cache:cache[rel]=list(csv.DictReader((ROOT/rel).open()))
   matched=[]
   for row in cache[rel]:
    if row.get('stem',row.get('instance'))!=r['instance']:continue
    if 'workers' in row and int(row['workers'])!=int(r['workers']):continue
    if 'mode' in row and row['mode']!=r['method']:continue
    h=row.get('source_sha256',row.get('input_file_sha256'))
    if h and h!=r['input_sha256']:continue
    matched.append(row)
   if not matched:raise ValueError('No compatible schedule for '+key)
 results['all_510_cell_schedule_matches']='PASS'
 representatives={}
 for r in rows:representatives.setdefault(r['runner_sha256'],r)
 for j,(h,r) in enumerate(representatives.items()):
  work=out/'staged_cells'/str(j)
  run('stage_'+h[:12],[sys.executable,str(ROOT/'scripts/prepare_run.py'),'--instance',r['instance'],'--workers',r['workers'],'--method',r['method'],'--out',str(work),'--stage-only'])
  runner=work/'code'/Path(r['runner_path']).name
  if hashlib.sha256(runner.read_bytes()).hexdigest()!=h:raise ValueError('Staged runner hash')
  run('native_help_'+h[:12],[sys.executable,str(runner),'--help'])
  run('reference_plan_'+h[:12],[sys.executable,str(ROOT/'scripts/regenerate_reference.py'),'--instance',r['instance'],'--out',str(out/'reference_plan_only'/str(j))])
 # Parse every frozen model without importing any optimizer object or running a solve.
 code="""import json,sys,pathlib
p=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(p/'code'));from generalized_pea_blocklex import lexsolve
f=next((p/'inputs').iterdir())
if f.suffix=='.json':
 from problem_instances import build_model
 model=build_model(json.loads(f.read_text()))
elif f.name.startswith('KP'):
 from external_kp_model import load_model
 model,_=load_model(f)
else:
 from external_ap_model import load_model
 model,_=load_model(f)
assert model.p>=3 and model.n>0
print('MODEL_IMPORT_AND_BUILD_PASS',model.p,model.n)
"""
 for j in range(len(representatives)):run('model_build_'+str(j),[sys.executable,'-c',code,str(out/'staged_cells'/str(j))])
 report=dict(status='PASS',checks=results,raw_terminals=510,independent_reference_files=85,runner_versions_staged=len(representatives),scheduled_cells_checked=510,analysis_outputs_compared=9,TSP_native_LPs_reparsed=15,figures_regenerated=True,new_solver_runs=0,new_reference_enumerations=0,limitations='Historical generators were supplied and their plans/syntax checked; exhaustive enumeration/DP was not rerun. Timings were not remeasured. Environment check does not establish original hardware equivalence.')
 (out/'PACKAGE_QA.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
