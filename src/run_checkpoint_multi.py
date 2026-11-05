"""Family-aware PEA runner. KP path mirrors the frozen runner; AP uses exact assignment constraints."""
import os
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='1'
import argparse, collections, hashlib, json, math, multiprocessing as mp
import pathlib, platform, queue, time, traceback

ROOT=pathlib.Path(__file__).resolve().parent.parent

def journal_row(stream, data):
    stream.write(json.dumps(data)+'\n');stream.flush();os.fsync(stream.fileno())

def save(path, data):
    tmp=path.with_suffix(path.suffix+'.tmp')
    with tmp.open('w') as f:
        json.dump(data,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
    tmp.replace(path)

def load(path):
    import numpy as np
    from pea_model import BinaryMOIP
    d=json.loads(pathlib.Path(path).read_text())
    # Older frozen AP inputs use the equivalent `family` field; preserve their
    # bytes and let the runner accept either schema key.
    family=d.get('problem',d.get('family','KP')).upper()
    if family=='KP':
        P=BinaryMOIP(-np.asarray(d['profits'],float),np.array([d['weights']],float),np.array([d['capacity']],float))
    elif family=='AP':
        n=int(d['n']); costs=np.asarray(d['costs'],dtype=float)
        if costs.shape!=(int(d['p']),n,n):raise ValueError('AP cost tensor must have shape (p,n,n)')
        # x[i,j] is 1 when assignment i -> j is selected.
        eq=np.zeros((2*n,n*n),dtype=float)
        for i in range(n):eq[i,i*n:(i+1)*n]=1
        for j in range(n):eq[n+j,j::n]=1
        P=BinaryMOIP(costs.reshape(int(d['p']),n*n),A_eq=eq,b_eq=np.ones(2*n))
    elif family=='TSP':
        # Frozen Pettersson TSP inputs use a binary MTZ order encoding.
        # Keep this adapter aligned with the project's frozen P04 TSP model:
        # arc variables enforce one in/out edge per city; binary position bits
        # enforce a single Hamiltonian tour (not merely a cycle cover).
        n=int(d['n']); p=int(d['p']); costs=np.asarray(d['costs'],dtype=float)
        if d.get('directed') is not True or d.get('formulation')!='mtz_binary':
            raise ValueError('TSP input must use directed mtz_binary formulation')
        if costs.shape!=(p,n,n) or np.any(np.diagonal(costs,axis1=1,axis2=2)!=0):
            raise ValueError('TSP cost tensor shape/diagonal is invalid')
        arcs=[(i,j) for i in range(n) for j in range(n) if i!=j]
        na=len(arcs); nbits=max(1,(n-1).bit_length()); total=na+(n-1)*nbits
        C=np.zeros((p,total),dtype=float)
        for a,(i,j) in enumerate(arcs): C[:,a]=costs[:,i,j]
        eq=np.zeros((2*n,total),dtype=float)
        for a,(i,j) in enumerate(arcs): eq[i,a]=1; eq[n+j,a]=1
        A=[]; b=[]
        z={(i,k):na+(i-1)*nbits+k for i in range(1,n) for k in range(nbits)}
        for i in range(1,n):
            row=np.zeros(total)
            for k in range(nbits): row[z[i,k]]=2**k
            A.extend((row,-row)); b.extend((n-1,-1))
        for a,(i,j) in enumerate(arcs):
            if i and j:
                row=np.zeros(total); row[a]=n
                for k in range(nbits): row[z[i,k]]+=2**k; row[z[j,k]]-=2**k
                A.append(row); b.append(n-1)
        P=BinaryMOIP(C,A_ub=np.asarray(A),b_ub=np.asarray(b),A_eq=eq,b_eq=np.ones(2*n))
    else:
        raise ValueError(f'Unsupported family in this runner: {family}')
    d['_family']=family
    return P,d

def validate_witness(P,d,x,upper=None,y=None):
    import numpy as np
    x=np.asarray(x,dtype='int64')
    assert x.shape==(P.n,) and np.all((x==0)|(x==1)), 'nonbinary or wrong-length witness'
    if P.A_ub is not None:assert np.all(P.A_ub@x<=P.b_ub+1e-8), 'inequality-infeasible witness'
    if P.A_eq is not None:assert np.allclose(P.A_eq@x,P.b_eq,rtol=0,atol=1e-8), 'equality-infeasible witness'
    if d['_family']=='KP':assert int(np.asarray(d['weights'],dtype='int64')@x)<=d['capacity'], 'infeasible KP witness'
    values=(P.C@x).astype('int64')
    if upper is not None:assert all(u is None or int(values[j])<=u for j,u in enumerate(upper)), 'objective bound violation'
    if y is not None:assert tuple(map(int,values))==tuple(map(int,y)), 'objective vector mismatch'
    return values

def worker(path, mode, qin, qout, cpu, calls_path):
    try:
        os.sched_setaffinity(0,{cpu})
        import numpy as np
        from pea_highs import PersistentHighsMOIP
        from generalized_pea_blocklex import lexsolve
        P,d=load(path)
        solver=PersistentHighsMOIP(P)
        original=solver.solve
        count=0
        call_log=open(calls_path,'a',buffering=1)
        def checked(c,upper=None):
            nonlocal count
            x,n,t,status=original(c,upper)
            count+=1
            if x is not None:validate_witness(P,d,x,upper)
            journal_row(call_log,{'call':count,'monotonic_ns':time.monotonic_ns(),'status':str(status),'solver_s':t,'bb_nodes':n})
            return x,n,t,status
        solver.solve=checked
        qout.put(('READY',{'pid':os.getpid(),'cpu':cpu,'highs_version':solver.H.version(),'threads_option':str(solver.H.getOptionValue('threads'))}))
        while True:
            combo=qin.get()
            if combo is None:break
            t0=time.perf_counter()
            y,c,n,st,mc=lexsolve(P,solver,combo,mode)
            x=None if y is None else list(map(int,solver.last_x))
            qout.put(('DONE',{'combo':combo,'y':y,'x':x,'calls':c,'nodes':n,'solver_s':st,'oracle_wall_s':time.perf_counter()-t0,'max_coefficient':mc}))
        call_log.close()
    except BaseException:
        qout.put(('ERROR',traceback.format_exc()))

def run(input_path, mode, budget=1200, deadlines=(300,600,900,1200), prefix=None, workers=1, qa=False):
    if mode not in ('standard','block2'):raise ValueError('Unknown method')
    if not qa and (budget,tuple(deadlines)) not in ((1200,(300,600,900,1200)),(1800,(600,1200,1800))):
        raise ValueError('Use a registered 1200s or 1800s schedule, or --qa for software tests')
    if not deadlines or sorted(set(deadlines))!=list(deadlines) or deadlines[0]<=0 or deadlines[-1]!=budget:
        raise ValueError('Checkpoints must increase and end at the time budget')
    import numpy as np, scipy
    from generalized_pea_blocklex import combo_key
    input_path=pathlib.Path(input_path).resolve()
    P,d=load(input_path)
    prefix=pathlib.Path(prefix or ROOT/'runs'/mode)
    prefix.parent.mkdir(parents=True,exist_ok=True)
    terminal=prefix.with_suffix('.terminal.json')
    if list(prefix.parent.glob(prefix.name+'.*')):raise RuntimeError('Existing run files must not be overwritten or appended: '+str(prefix))
    cpus=sorted(os.sched_getaffinity(0)); worker_cpus=cpus[:workers]; coordinator_cpu=cpus[-1]
    assert workers in (1,2,4) and len(cpus)>=workers+1
    metadata={'method':mode,'workers':workers,'solver_threads':1,'family':d['_family'],'input_sha256':hashlib.sha256(input_path.read_bytes()).hexdigest(),'instance':input_path.stem,'budget_s':budget,'checkpoints_s':list(deadlines),'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'allowed_cpus':cpus,'worker_cpus':worker_cpus,'coordinator_cpu':coordinator_cpu,'hostname':platform.node(),'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path(__file__).parent.glob('*.py')}}
    metadata.update(protocol_revision='PUBLICATION_CHECKPOINT_RUNNER',measurement_kind='qa' if qa else 'performance',auto_advance=False,worker_ready=[],clock_scope='before worker process construction/start through controller stop; parent imports and input parsing excluded; checkpoint and durable journal I/O included',cpu_quota=pathlib.Path('/sys/fs/cgroup/cpu.max').read_text().strip(),memory_limit=pathlib.Path('/sys/fs/cgroup/memory.max').read_text().strip(),load_average_start=os.getloadavg())
    ctx=mp.get_context('spawn'); qin=ctx.Queue(); qout=ctx.Queue()
    seen=set(); pending=collections.deque(); points={}; accepts=[]; snapshots=[];events=[]
    counts={'scalarizations':0,'feasible':0,'infeasible':0,'milp_calls':0,'bb_nodes':0,'completed_oracle_solver_s':0.0,'oracle_wall_s':0.0}
    inflight=0; completed_at=None; status='RUNNING'; error=None; next_cp=0; last_flush=0
    journal=open(prefix.with_suffix('.accepted.jsonl'),'a',buffering=1)
    oracle_journal=open(prefix.with_suffix('.oracles.jsonl'),'a',buffering=1)
    start=time.perf_counter(); metadata['start_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    metadata['start_monotonic_ns']=time.monotonic_ns()
    procs=[ctx.Process(target=worker,args=(str(input_path),mode,qin,qout,cpu,str(prefix.with_name(prefix.name+f'.worker{j}.calls.jsonl')))) for j,cpu in enumerate(worker_cpus)]
    def elapsed():return time.perf_counter()-start
    def snapshot(target):
        selected=[r for r in accepts if r['accepted_elapsed_s']<=target]
        cp_counts={k:0 for k in counts}
        for event in events:
            if event['completed_elapsed_s']<=target:cp_counts=event['counters']
            else:break
        row={'checkpoint_s':target,'observed_elapsed_s':elapsed(),'status':'RIGHT_CENSORED' if target==budget and status=='RUNNING' else status,'search_completed_elapsed_s':completed_at,'point_count':len(selected),'points_minimization':[r['y_min'] for r in selected],'accepted_points_with_witnesses':selected,'carried_forward_after_completion':status=='SEARCH_COMPLETED','counters':dict(cp_counts),'inflight_oracle':inflight,'queued_tasks':len(pending),'queue_scope':'observed snapshot time, not retrospective target time','counter_scope':'validated controller oracle commits at or before target; individual completed MILPs separately in calls.jsonl','input_sha256':metadata['input_sha256'],'method':mode,'workers':workers}
        snapshots.append(row);save(prefix.with_name(prefix.name+f'.checkpoint_{target:g}.json'),row)
    def flush():
        save(prefix.with_suffix('.progress.json'),{**metadata,'status':status,'elapsed_s':elapsed(),'point_count':len(points),'counters':counts,'queued_tasks':len(pending),'inflight_oracle':inflight,'error':error,'checkpoints':snapshots,'accepted_points_with_witnesses':accepts})
    try:
        for proc in procs:proc.start()
        os.sched_setaffinity(0,{coordinator_cpu})
        ready=0
        while status=='RUNNING':
            now=elapsed()
            while next_cp<len(deadlines) and now>=deadlines[next_cp]:snapshot(deadlines[next_cp]);next_cp+=1
            if now>=budget:status='RIGHT_CENSORED';break
            if ready==workers:
                while pending and inflight<workers:qin.put(pending.popleft());inflight+=1
                if not pending and inflight==0:status='SEARCH_COMPLETED';completed_at=elapsed();break
            if now-last_flush>=15:flush();last_flush=now
            next_deadline=deadlines[next_cp] if next_cp<len(deadlines) else budget
            try:kind,data=qout.get(timeout=max(.001,min(.1,next_deadline-now,budget-now)))
            except queue.Empty:
                if any(not p.is_alive() for p in procs):raise RuntimeError('Worker exited without terminal message')
                continue
            now=elapsed()
            while next_cp<len(deadlines) and now>=deadlines[next_cp]:snapshot(deadlines[next_cp]);next_cp+=1
            if now>=budget:status='RIGHT_CENSORED';break
            if kind=='ERROR':raise RuntimeError(data)
            if kind=='READY':
                metadata['worker_ready'].append(data);ready+=1;assert ready<=workers
                if ready==workers:root=(None,)*(P.p-1);pending.append(root);seen.add(combo_key(root))
                continue
            assert kind=='DONE' and inflight
            combo=data['combo'];y=None if data['y'] is None else tuple(data['y'])
            if y is not None:validate_witness(P,d,data['x'],y=y)
            committed_at=elapsed()
            if committed_at>=budget:status='RIGHT_CENSORED';break
            inflight-=1
            counts['scalarizations']+=1;counts['milp_calls']+=data['calls'];counts['bb_nodes']+=data['nodes'];counts['completed_oracle_solver_s']+=data['solver_s'];counts['oracle_wall_s']+=data['oracle_wall_s']
            counts['infeasible' if y is None else 'feasible']+=1
            event={'completed_elapsed_s':committed_at,'combo':combo,'y_min':y,'calls':data['calls'],'nodes':data['nodes'],'solver_s':data['solver_s'],'oracle_wall_s':data['oracle_wall_s'],'counters':dict(counts)}
            events.append(event);journal_row(oracle_journal,event)
            if y is None:continue
            store=all(yi is None or all(int(yi[j])<=y[j] for j in range(i+1,P.p)) for i,yi in enumerate(combo))
            if store and y not in points:
                accepted_at=elapsed()
                if accepted_at>budget:status='RIGHT_CENSORED';break
                rec={'accepted_elapsed_s':accepted_at,'y_min':list(y),'x':data['x']}
                if d['_family']=='KP':rec['profits_max']=[-v for v in y]
                points[y]=rec;accepts.append(rec);journal_row(journal,rec)
            for j in range(P.p-1):
                if all(i==j or yi is None or y[j]>=int(yi[j]) for i,yi in enumerate(combo)):
                    child=list(combo);child[j]=y;child=tuple(child);key=combo_key(child)
                    if key not in seen:seen.add(key);pending.append(child)
        if status=='SEARCH_COMPLETED':
            assert counts['scalarizations']==counts['feasible']+counts['infeasible']==len(seen)
            assert counts['milp_calls']==(P.p if mode=='standard' else P.p-1)*counts['feasible']+counts['infeasible']
            while next_cp<len(deadlines):snapshot(deadlines[next_cp]);next_cp+=1
        elif status=='RIGHT_CENSORED':
            while next_cp<len(deadlines) and deadlines[next_cp]<=budget:snapshot(deadlines[next_cp]);next_cp+=1
    except BaseException:error=traceback.format_exc();status='ERROR'
    finally:
        measured=elapsed()
        if status=='SEARCH_COMPLETED':
            for _ in procs:qin.put(None)
        for proc in procs:
            proc.join(timeout=.3 if status=='SEARCH_COMPLETED' else .01)
            if proc.is_alive():proc.terminate();proc.join(timeout=2)
            if proc.is_alive():proc.kill();proc.join(timeout=2)
        journal.close();oracle_journal.close()
        result={**metadata,'status':status,'elapsed_s':measured,'shutdown_elapsed_s':elapsed(),'search_completed_elapsed_s':completed_at,'point_count':len(points),'points_minimization':sorted(map(list,points)),'accepted_points_with_witnesses':accepts,'counters':counts,'inflight_oracle':inflight,'queued_tasks':len(pending),'error':error,'checkpoints':snapshots,'verification':'binary witnesses checked against the family-specific linear constraints; no independent full Pareto reference for this input'}
        save(terminal,result);flush();os.sched_setaffinity(0,set(cpus))
    print(json.dumps({'method':mode,'status':status,'elapsed_s':measured,'point_count':len(points),'milp_calls':counts['milp_calls']}),flush())
    return result

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--input',required=True);a.add_argument('--method',choices=['standard','block2'],required=True);a.add_argument('--budget',type=float,default=1200);a.add_argument('--checkpoints',default='300,600,900,1200');a.add_argument('--prefix');a.add_argument('--workers',type=int,default=1);a.add_argument('--qa',action='store_true')
    v=a.parse_args();r=run(v.input,v.method,v.budget,tuple(map(float,v.checkpoints.split(','))),v.prefix,v.workers,v.qa)
    raise SystemExit(2 if r['status']=='ERROR' else 0)
