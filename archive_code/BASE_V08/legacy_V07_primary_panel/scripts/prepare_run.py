#!/usr/bin/env python3
"""Plan or stage one historical design cell. Only --execute launches a solver."""
from pathlib import Path
import argparse,csv,json,os,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
def main():
 a=argparse.ArgumentParser(description=__doc__)
 a.add_argument('--instance',required=True);a.add_argument('--workers',required=True,type=int,choices=[1,2,4]);a.add_argument('--method',required=True,choices=['standard','block2']);a.add_argument('--out',required=True,type=Path);a.add_argument('--label',default='V04_R1_REPRODUCTION')
 g=a.add_mutually_exclusive_group();g.add_argument('--execute',action='store_true');g.add_argument('--stage-only',action='store_true')
 v=a.parse_args();rows=list(csv.DictReader((ROOT/'metadata/EXPERIMENT_MANIFEST_510.csv').open()))
 r=next((r for r in rows if (r['instance'],int(r['workers']),r['method'])==(v.instance,v.workers,v.method)),None)
 if r is None:raise SystemExit('Cell is outside the V04 completed panel.')
 out=v.out.resolve();runner=Path(r['runner_path']).name;cmd=[sys.executable,str(out/'code'/runner),'--instance',v.instance,'--workers',str(v.workers),'--mode',v.method,'--run-label',v.label,'--out',str(out/'result.json')]
 sch=json.loads((ROOT/'metadata/RUNNER_SCHEDULE_MAP.json').read_text())['|'.join([r['instance'],r['workers'],r['method']])]
 report=dict(action='execute' if v.execute else 'stage_only' if v.stage_only else 'plan_only_no_files_or_solver',instance=v.instance,workers=v.workers,method=v.method,recorded_python=r['python'],recorded_scipy=r['scipy'],recorded_numpy=r['numpy'],runner_sha256=r['runner_sha256'],historical_wall_s=r['wall_s'],historical_MILP=r['MILP'],reference_budget_s=r['reference_budget_s'],historical_time_protocol=r['time_protocol'],schedule_inputs=sch,command=cmd,new_outputs=str(out))
 print(json.dumps(report,indent=2))
 if not (v.execute or v.stage_only):return
 if out.exists() and any(out.iterdir()):raise SystemExit('Choose an absent or empty workspace; archived evidence is never overwritten.')
 out.mkdir(parents=True,exist_ok=True)
 for p in (ROOT/'src/frozen/common').glob('*.py'):
  dest=out/'code'/p.name;dest.parent.mkdir(exist_ok=True);shutil.copyfile(p,dest)
 if r['family']=='KP':shutil.copyfile(ROOT/'src/frozen/models'/('KP_n'+r['n'])/'external_kp_model.py',out/'code/external_kp_model.py')
 shutil.copyfile(ROOT/r['runner_path'],out/'code'/runner)
 for name,src in sch.items():
  p=out/'docs'/name;p.parent.mkdir(exist_ok=True);shutil.copyfile(ROOT/src,p)
 for field,folder in [('input_path','inputs'),('oracle_path','oracles')]:
  p=out/folder/Path(r[field]).name;p.parent.mkdir(exist_ok=True);shutil.copyfile(ROOT/r[field],p)
 (out/'REPRODUCTION_PLAN.json').write_text(json.dumps(report,indent=2)+'\n')
 if not v.execute:return
 if sys.platform!='linux' or not hasattr(os,'sched_getaffinity'):raise SystemExit('Native runners require Linux CPU affinity.')
 if len(os.sched_getaffinity(0))<v.workers+1:raise SystemExit('Native runner needs at least workers+1 allowed CPUs.')
 if (Path('/mnt/data')/'sota_python_common.py').exists():raise SystemExit('A legacy /mnt/data/sota_python_common.py may shadow this release. Use a clean execution environment.')
 import importlib.metadata
 if importlib.metadata.version('scipy')!='1.17.0' or importlib.metadata.version('numpy')!='2.3.5':raise SystemExit('Install the pinned solver requirements before execution.')
 env=os.environ.copy()
 for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:env[name]='1'
 # Preserve frozen module bytes. This launcher changes paths and output labels only.
 result=subprocess.run(cmd,cwd=out,env=env)
 raise SystemExit(result.returncode)
if __name__=='__main__':main()
