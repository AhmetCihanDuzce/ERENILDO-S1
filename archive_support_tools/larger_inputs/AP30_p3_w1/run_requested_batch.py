#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,sys,hashlib,time,os
ROOT=Path(__file__).resolve().parent

def save(path,obj):
 tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n');os.replace(tmp,path)

def audit(prefix,objectives):
 sys.path.insert(0,str(ROOT/'src'))
 import run_checkpoint_multi as r
 P,d=r.load(ROOT/'inputs'/f'AP_p{objectives}_n30_i01.json')
 result=json.loads(prefix.with_suffix('.terminal.json').read_text());checks=[]
 assert result['status'] in ['SEARCH_COMPLETED','RIGHT_CENSORED'],result.get('error')
 for seconds in (300,600,900,1200):
  cp=json.loads(prefix.with_name(prefix.name+f'.checkpoint_{seconds}.json').read_text());points=cp['accepted_points_with_witnesses']
  assert len(points)==cp['point_count'];seen=set()
  for row in points:
   y=r.validate_witness(P,d,row['x'],y=row['y_min']);seen.add(tuple(map(int,y)))
   assert row['accepted_elapsed_s']<=seconds
  assert len(seen)==len(points)
  checks.append({'checkpoint_s':seconds,'point_count':len(points),'validated_witnesses':len(seen),'status':cp['status']})
 for row in result['accepted_points_with_witnesses']:r.validate_witness(P,d,row['x'],y=row['y_min'])
 checked={'audit':'PASS','checkpoints':checks,'terminal_witnesses_validated':len(result['accepted_points_with_witnesses'])}
 save(ROOT/'audit'/f'{prefix.name}.audit.json',checked)
 return result,checked

def main():
 plan=json.loads((ROOT/'RUN_PLAN.json').read_text());state={'status':'RUNNING','completed':[],'current':None,'plan':plan}
 for i,(p,method) in enumerate(plan['order'],1):
  name=f'AP_n30_p{p}_i1_{method}_w1';prefix=ROOT/'runs'/name
  assert not list(prefix.parent.glob(prefix.name+'.*')),'Do not overwrite run records'
  state['current']={'index':i,'name':name,'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())};save(ROOT/'BATCH_PROGRESS.json',state)
  print(json.dumps({'event':'START','index':i,'name':name}),flush=True)
  cmd=[sys.executable,str(ROOT/'src/run_checkpoint_multi.py'),'--input',str(ROOT/'inputs'/f'AP_p{p}_n30_i01.json'),'--method',method,'--budget','1200','--checkpoints','300,600,900,1200','--prefix',str(prefix),'--workers','1']
  with (ROOT/'logs'/f'{name}.log').open('w') as log: proc=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
  try:
   assert proc.returncode==0,f'runner exit {proc.returncode}'
   result,check=audit(prefix,p)
  except Exception as exc:
   state['status']='ERROR';state['error']=repr(exc);save(ROOT/'BATCH_PROGRESS.json',state);raise
  row={'name':name,'index':i,'objectives':p,'workers':1,'method':method,'status':result['status'],'elapsed_s':result['elapsed_s'],'point_count':result['point_count'],'milp_calls':result['counters']['milp_calls'],'input_sha256':result['input_sha256'],'terminal_sha256':hashlib.sha256(prefix.with_suffix('.terminal.json').read_bytes()).hexdigest(),'check':check}
  state['completed'].append(row);state['current']=None;save(ROOT/'BATCH_PROGRESS.json',state)
  print(json.dumps({'event':'END',**row}),flush=True)
 state['status']='BATCH_COMPLETE';save(ROOT/'BATCH_PROGRESS.json',state)
if __name__=='__main__':main()
