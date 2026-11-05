#!/usr/bin/env python3
"""Opt-in independent reference regeneration. Default prints a plan; no MILP solver."""
from pathlib import Path
import argparse,csv,json,sys,subprocess,shutil,itertools,math
ROOT=Path(__file__).resolve().parents[1]
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--instance',required=True);a.add_argument('--out',required=True,type=Path);a.add_argument('--execute',action='store_true');a.add_argument('--compiler',default='g++');v=a.parse_args()
 rows=list(csv.DictReader((ROOT/'metadata/BENCHMARK_MANIFEST_85.csv').open()));r=next((r for r in rows if r['instance']==v.instance),None)
 if r is None:raise SystemExit('Not in completed V04 benchmark panel')
 p,n=int(r['p']),int(r['n']);family=r['family'];out=v.out.resolve()
 method='exhaustive_binary_gray_code' if family=='KP' else 'assignment_permutations' if family=='AP' and n<=10 else 'assignment_subset_DP' if family=='AP' else 'complete_hamilton_tours'
 print(json.dumps(dict(instance=v.instance,action='execute_independent_reference' if v.execute else 'plan_only',method=method,max_candidates=2**n if family=='KP' else math.factorial(n-1) if family=='TSP' else math.factorial(n) if n<=10 else 'subset_DP_not_n_factorial_enumeration',MILP_solver_used=False,output=str(out)),indent=2))
 if not v.execute:return
 if out.exists() and any(out.iterdir()):raise SystemExit('Output must be absent or empty')
 out.mkdir(parents=True,exist_ok=True)
 import numpy as np
 sys.path.insert(0,str(ROOT/'src/frozen/common'))
 if family=='KP':sys.path.insert(0,str(ROOT/'src/frozen/models'/('KP_n'+r['n'])))
 if family in ('KP','AP'):
  compiler=shutil.which(v.compiler)
  if compiler is None:raise SystemExit('A C++17 compiler is needed for this independent reference')
  if family=='KP':
   from external_kp_model import load_model
  else:
   from external_ap_model import load_model
  model,spec=load_model(ROOT/r['input_path'])
  ints=lambda vals:' '.join(str(int(round(x))) for x in vals)
  if not np.all(model.C==np.rint(model.C)):raise ValueError('Noninteger source costs')
  if family=='KP':
   source='independent_bruteforce.cpp'
   content=f'{p} {n} {int(model.b_ub[0])}\n'+ints(model.A_ub[0])+'\n'+'\n'.join(ints(-row) for row in model.C)+'\n'
  else:
   source='independent_assignment_oracle.cpp' if n<=10 else 'independent_ap_dp.cpp'
   content=f'{p} {n}\n'+'\n'.join(ints(row) for row in model.C)+'\n'
  (out/'integer_model.txt').write_text(content)
  subprocess.run([compiler,'-O3','-std=c++17',str(ROOT/'src/frozen/independent'/source),'-o',str(out/'independent_oracle')],check=True)
  subprocess.run([str(out/'independent_oracle'),str(out/'integer_model.txt'),str(out/'raw_points.txt')],check=True)
  lines=(out/'raw_points.txt').read_text().splitlines()
  if family=='KP' or n<=10:lines=lines[1:]
  points=sorted({tuple(map(int,line.split())) for line in lines if line.strip()})
 else:
  spec=json.loads((ROOT/r['input_path']).read_text());cost=np.asarray(spec['costs'],dtype=np.int64)
  images=[];batch=[]
  def evaluate(rows):
   tours=np.asarray(rows,dtype=np.int64)
   value=cost[:,0,tours[:,0]].T.copy()
   value+=cost[:,tours[:,:-1],tours[:,1:]].sum(axis=2).T
   value+=cost[:,tours[:,-1],0].T
   return value
  for tour in itertools.permutations(range(1,n)):
   batch.append(tour)
   if len(batch)==4096:images.append(evaluate(batch));batch=[]
  if batch:images.append(evaluate(batch))
  ordered=np.unique(np.concatenate(images),axis=0);front=[]
  for y in ordered:
   if front and np.any(np.all(np.asarray(front)<=y,axis=1)):continue
   front.append(y.copy())
  points=[tuple(map(int,y)) for y in front]
 ref=json.loads((ROOT/r['oracle_path']).read_text());expected=sorted({tuple(y) for y in ref.get('pareto_points',ref.get('objective_vectors'))})
 result=dict(instance=v.instance,method=method,status='PASS' if points==expected else 'FAIL',pareto_size=len(points),matches_supplied_reference=points==expected,MILP_solver_used=False,objective_vectors=points)
 (out/'REGENERATED_REFERENCE.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:x for k,x in result.items() if k!='objective_vectors'},indent=2))
 if points!=expected:raise SystemExit(1)
if __name__=='__main__':main()
