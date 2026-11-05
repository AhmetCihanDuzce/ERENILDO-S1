#!/usr/bin/env python3
"""Parallel PEA/EREN confirmatory one-cell executor: no legacy SOTA inputs.
Uses frozen lexsolve, PEAs scion logic and independent exhaustive oracle.
One process per HiGHS instance, single HiGHS thread each, cpu-pinned.
One real checkpoint per planned deadline reached, no artificial checkpoints.
"""
import os
for e in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
 os.environ[e]='1'
import argparse,csv,hashlib,json,math,multiprocessing as mp,pathlib,queue,sys,time,uuid,platform,traceback
ROOT=pathlib.Path(__file__).resolve().parent.parent
ENGINE=pathlib.Path(__file__).resolve().parent

def sha(b):return hashlib.sha256(b).hexdigest()
def key(combo):return tuple(('D',j) if y is None else tuple(map(int,y)) for j,y in enumerate(combo))
def worker(wid,method,inputfile,qin,qout,cpu):
 try:
  os.sched_setaffinity(0,{cpu})
  sys.path.insert(0,str(ENGINE))
  from problem_instances import build_model
  from generalized_pea_blocklex import lexsolve
  from sota_python_common import dp
  P=build_model(json.loads(pathlib.Path(inputfile).read_text()))
  solver=dp.PersistentHighsMOIP(P)
  qout.put(('READY',wid,{'pid':os.getpid(),'cpu':cpu}))
  while True:
   task=qin.get()
   if task is None:return
   t0=time.perf_counter();cpu0=time.process_time()
   try:
    y,c,n,st,mc=lexsolve(P,solver,task,mode=method)
    qout.put(('DONE',wid,(task,y,c,n,st,mc,time.perf_counter()-t0,time.process_time()-cpu0)))
   except Exception as exc:
    qout.put(('ERROR',wid,{'error':repr(exc),'task':repr(task),'traceback':traceback.format_exc()}));return
 except Exception as exc:qout.put(('ERROR',wid,{'error':repr(exc),'where':'init','traceback':traceback.format_exc()}))

def main():
 a=argparse.ArgumentParser()
 a.add_argument('--instance',required=True);a.add_argument('--workers',type=int,required=True,choices=(1,2,4));a.add_argument('--mode',required=True,choices=('standard','block2'));a.add_argument('--run-label',required=True);a.add_argument('--out',required=True)
 v=a.parse_args()
 row=next((x for x in csv.DictReader((ROOT/'docs'/'FROZEN_BENCHMARKS_36.csv').open()) if x['instance']==v.instance),None)
 if row is None:raise ValueError('Not in frozen panel')
 pairrows=[x for x in csv.DictReader((ROOT/'docs'/'FROZEN_PRIMARY_SCHEDULE_216.csv').open()) if x['instance']==v.instance and int(x['workers'])==v.workers]
 if not pairrows or v.mode not in [r['mode'] for r in pairrows]:raise RuntimeError('Pair not in frozen schedule')
 ip=ROOT/'inputs'/f'{v.instance}.json';op=ROOT/'oracles'/f'{v.instance}.json'
 if not op.exists():raise RuntimeError(f'Oracle not yet computed independently: {op}')
 spec=json.loads(ip.read_text());ref=json.loads(op.read_text());p=int(spec['p']);budget=float(row['shared_budget_s'])
 assert sha(ip.read_bytes())==row['input_file_sha256']
 assert ref['input_semantic_sha256']==row['semantic_sha256']
 available=sorted(os.sched_getaffinity(0));assert len(available)>=v.workers+1
 cpus=available[:v.workers];coordinator_cpu=available[-1]
 out=pathlib.Path(v.out);out.parent.mkdir(parents=True,exist_ok=True)
 start=time.perf_counter();utc_start=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
 uid='p01-'+sha('|'.join((v.instance,str(v.workers),v.mode,v.run_label,utc_start)).encode())[:16]
 snap=[];tot={'scalarizations':0,'feasible':0,'infeasible':0,'milp_calls':0,'bb_nodes':0,'solver_time_sum_s':0.0,'worker_lexwall_sum_s':0.0,'worker_cpu_sum_s':0.0,'max_abs_objcoef':0.0}
 byworker={j:{'tasks':0,'solver_time_sum_s':0.0,'worker_lexwall_sum_s':0.0,'worker_cpu_sum_s':0.0} for j in range(v.workers)}
 yset=set();seen=set();pending=0;ready=[];status='UNRESOLVED';err=None;procs=[];ctx=mp.get_context('spawn');qin=ctx.Queue();qout=ctx.Queue()
 milestones=[j*budget/8 for j in range(1,9)];mile_idx=0
 def checkpoint(reason):
  snap.append({'elapsed_s':round(time.perf_counter()-start,6),'reason':reason,'scalarizations':tot['scalarizations'],'feasible':tot['feasible'],'infeasible':tot['infeasible'],'milp_calls':tot['milp_calls'],'observed_pareto_count':len(yset),'dispatched_unique_combinations':len(seen),'pending':pending})
 def flush():
  elapsed=time.perf_counter()-start
  payload={'run_id':uid,'instance':v.instance,'method':v.mode,'workers':v.workers,'run_label':v.run_label,'start_utc':utc_start,'finish_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'elapsed_s':round(elapsed,6),'budget_s':budget,'status':status,'error':err,'objective_count':p,'n':int(spec['n']),'family':spec['problem'],'input_semantic_sha256':row['semantic_sha256'],'input_file_sha256':sha(ip.read_bytes()),'oracle_reference_sha256':ref['objective_vectors_sha256'],'candidate_cores':available,'worker_cpu_affinity':cpus,'coordinator_cpu':coordinator_cpu,'run_source_sha256':sha(pathlib.Path(__file__).read_bytes()),'hostname':platform.node(),'python':platform.python_version(),'checkpoints':snap,'actual_checkpoint_count':len(snap),'counters':tot,'worker_counters':byworker,'unique_combinations':len(seen),'observed_pareto_size':len(yset),'observed_pareto_vectors':[list(y) for y in sorted(yset)] if status=='EXACT_QA_PASS' else [],'pareto_sha256':sha(json.dumps([list(y) for y in sorted(yset)],separators=(',',':')).encode()),'oracle_pareto_size':ref['pareto_size'],'exact_reference_match':status=='EXACT_QA_PASS','in_flight_or_queued_at_exit':pending,'solver_thread_policy':1,'two_method_pair_study':'parallel PEA oracle, no SOTA'}
  import scipy, numpy
  payload['scipy_version']=scipy.__version__;payload['numpy_version']=numpy.__version__
  out.write_text(json.dumps(payload,sort_keys=True,indent=2)+'\n')
 try:
  for j,cpu in enumerate(cpus):
   proc=ctx.Process(target=worker,args=(j,v.mode,str(ip),qin,qout,cpu),daemon=True)
   proc.start();procs.append(proc)
  # All workers must announce ready before dispatch; startup charged to wall time.
  while len(ready)<v.workers:
   rem=budget-(time.perf_counter()-start)
   if rem<=0:status='RIGHT_CENSORED';err='Startup exceeded budget';break
   try:kind,j,data=qout.get(timeout=min(rem,1.0))
   except queue.Empty:continue
   if kind=='ERROR':status='FAILED_WORKER';err=data;break
   if kind!='READY':status='FAILED_PROTOCOL';err=('wrong readiness',kind);break
   ready.append(data)
  if status=='UNRESOLVED':
   root=(None,)*(p-1);seen.add(key(root));pending=1;qin.put(root)
  # Controller on separate logical core, but cgroup total CPU quota may still bind.
  if hasattr(os,'sched_setaffinity'):os.sched_setaffinity(0,{coordinator_cpu})
  while status=='UNRESOLVED':
   now=time.perf_counter()-start
   while mile_idx<len(milestones) and now>=milestones[mile_idx]:
    checkpoint('SCHEDULED_REAL_OBSERVATION');mile_idx+=1
   if pending==0:
    got=[list(y) for y in sorted(yset)];expected=ref['objective_vectors']
    if got==expected:
     status='EXACT_QA_PASS'
     if tot['scalarizations'] != tot['feasible']+tot['infeasible'] or tot['scalarizations']!=len(seen):status='FAILED_COUNT_IDENTITY';err='scalarizations count identity failed'
     if tot['milp_calls']!= (p if v.mode=='standard' else p-1)*tot['feasible']+tot['infeasible']:status='FAILED_COUNT_IDENTITY';err='MILP count identity failed'
    else:status='FAILED_PARETO_MISMATCH';err=f'got {len(got)} expected {len(expected)}'
    break
   if now>=budget:status='RIGHT_CENSORED';err='Budget exhausted before proof of exact Pareto completion';break
   next_deadline=milestones[mile_idx] if mile_idx<len(milestones) else budget
   wait=max(0.001,min(1.0,budget-now,next_deadline-now))
   try:kind,j,data=qout.get(timeout=wait)
   except queue.Empty:continue
   if kind=='ERROR':status='FAILED_WORKER';err=data;break
   if kind!='DONE':status='FAILED_PROTOCOL';err=('unexpected worker message',kind);break
   combo,y,c,n,st,mc,lexwall,cputime=data
   pending-=1
   tot['scalarizations']+=1;tot['milp_calls']+=c;tot['bb_nodes']+=n;tot['solver_time_sum_s']+=st;tot['worker_lexwall_sum_s']+=lexwall;tot['worker_cpu_sum_s']+=cputime;tot['max_abs_objcoef']=max(tot['max_abs_objcoef'],mc)
   byworker[j]['tasks']+=1;byworker[j]['solver_time_sum_s']+=st;byworker[j]['worker_lexwall_sum_s']+=lexwall;byworker[j]['worker_cpu_sum_s']+=cputime
   if y is None:tot['infeasible']+=1;continue
   tot['feasible']+=1
   store=True
   for i in range(p-1):
    yi=combo[i]
    if yi is not None and any(int(yi[j])>int(y[j]) for j in range(i+1,p)):
     store=False;break
   if store:yset.add(tuple(y))
   for j in range(p-1):
    ok=True
    for i in range(p-1):
     if i==j:continue
     yi=combo[i];val=(-math.inf if yi is None else int(yi[j]))
     if int(y[j])<val:ok=False;break
    if ok:
     child=list(combo);child[j]=y;child=tuple(child);ck=key(child)
     if ck not in seen:
      seen.add(ck);pending+=1;qin.put(child)
   if len(seen)>200000:status='FAILED_TRAVERSAL_LIMIT';err='200k distinct combos';break
 except Exception as exc:
  status='FAILED_EXCEPTION';err={'error':repr(exc),'traceback':traceback.format_exc()}
 finally:
  checkpoint('TERMINAL_REAL_OBSERVATION')
  for _ in procs:
   try:qin.put_nowait(None)
   except Exception:pass
  for proc in procs:
   proc.join(timeout=.25)
   if proc.is_alive():proc.terminate();proc.join(timeout=2)
   if proc.is_alive():proc.kill();proc.join(timeout=2)
  flush()
 print(status,v.instance,v.workers,v.mode,'t',round(time.perf_counter()-start,3),'pf',len(yset),'milps',tot['milp_calls'],flush=True)
 sys.exit(0 if status=='EXACT_QA_PASS' else 3 if status=='RIGHT_CENSORED' else 2)
if __name__=='__main__':main()
