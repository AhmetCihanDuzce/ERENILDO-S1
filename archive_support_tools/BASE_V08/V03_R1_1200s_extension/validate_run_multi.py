"""Independent audit for family-aware runs; does not launch an experiment."""
import argparse, hashlib, itertools, json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from src.run_checkpoint_multi import load, validate_witness

def read_jsonl(path):return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]

def validate(root,prefix,input_path,exhaustive=False):
    P,d=load(input_path); t=json.loads(prefix.with_suffix('.terminal.json').read_text())
    journal=read_jsonl(prefix.with_suffix('.accepted.jsonl')); events=read_jsonl(prefix.with_suffix('.oracles.jsonl'))
    assert t['status'] in ('SEARCH_COMPLETED','RIGHT_CENSORED') and t['error'] is None
    assert t['family']==d['_family'] and t['input_sha256']==hashlib.sha256(input_path.read_bytes()).hexdigest()
    for name,h in t['source_sha256'].items():assert hashlib.sha256((root/'src'/name).read_bytes()).hexdigest()==h
    accepts=t['accepted_points_with_witnesses']
    assert journal==accepts[:len(journal)]
    assert len({tuple(a['y_min']) for a in accepts})==len(accepts)==t['point_count']
    assert sorted(a['y_min'] for a in accepts)==t['points_minimization']
    assert all(a['accepted_elapsed_s']<=b['accepted_elapsed_s'] for a,b in zip(accepts,accepts[1:]))
    for a in accepts:
        y=validate_witness(P,d,a['x'],y=a['y_min'])
        assert 0<=a['accepted_elapsed_s']<=t['budget_s']
        assert ('profits_max' in a)==(d['_family']=='KP')
    ys=[a['y_min'] for a in accepts]
    assert all(not (all(x<=y for x,y in zip(a,b)) and a!=b) for a in ys for b in ys)
    totals={k:0 for k in t['counters']}; previous=0
    for e in events:
        assert previous<=e['completed_elapsed_s']<=t['budget_s'];previous=e['completed_elapsed_s']
        feasible=e['y_min'] is not None
        assert e['calls']==(P.p if t['method']=='standard' else P.p-1) if feasible else e['calls']==1
        totals['scalarizations']+=1;totals['feasible' if feasible else 'infeasible']+=1
        for dst,src in [('milp_calls','calls'),('bb_nodes','nodes'),('completed_oracle_solver_s','solver_s'),('oracle_wall_s','oracle_wall_s')]:totals[dst]+=e[src]
        assert totals==e['counters']
    missing=max(0,t['counters']['scalarizations']-totals['scalarizations'])
    assert len(events)<=t['counters']['scalarizations']
    if not missing:assert totals==t['counters']
    else:
        # At a hard cutoff the append-only oracle journal can be a short prefix;
        # terminal and atomic checkpoint aggregates remain the controller record.
        assert t['counters']['scalarizations']==t['counters']['feasible']+t['counters']['infeasible']
        assert t['counters']['milp_calls']==(P.p if t['method']=='standard' else P.p-1)*t['counters']['feasible']+t['counters']['infeasible']
        assert all(totals[k]<=t['counters'][k] for k in totals)
    cps=[]
    assert len(t['checkpoints'])==len(t['checkpoints_s'])
    for target,stored in zip(t['checkpoints_s'],t['checkpoints']):
        cp=json.loads(prefix.with_name(prefix.name+f'.checkpoint_{target:g}.json').read_text());assert cp==stored
        selected=[a for a in accepts if a['accepted_elapsed_s']<=target]
        ev=[e for e in events if e['completed_elapsed_s']<=target]
        assert cp['accepted_points_with_witnesses']==selected and cp['point_count']==len(selected)
        assert cp['points_minimization']==[a['y_min'] for a in selected]
        cc=cp['counters']
        assert cc['scalarizations']==cc['feasible']+cc['infeasible']
        assert cc['milp_calls']==(P.p if t['method']=='standard' else P.p-1)*cc['feasible']+cc['infeasible']
        if cp['status']=='SEARCH_COMPLETED' and cp['carried_forward_after_completion']:assert cc==t['counters']
        assert all(cc[k]>=0 and cc[k]<=t['counters'][k] for k in cc)
        assert cp['carried_forward_after_completion'] or cp['observed_elapsed_s']>=target
        cps.append({'checkpoint_s':target,'point_count':cp['point_count'],'milp_calls':cp['counters']['milp_calls'],'scalarizations':cp['counters']['scalarizations'],'observed_elapsed_s':cp['observed_elapsed_s'],'status':cp['status']})
    calls=[]
    for f in prefix.parent.glob(prefix.name+'.worker*.calls.jsonl'):
        rows=read_jsonl(f);assert [r['call'] for r in rows]==list(range(1,len(rows)+1));calls+=rows
    if t['status']=='SEARCH_COMPLETED':assert t['inflight_oracle']==t['queued_tasks']==0
    brute=None
    if exhaustive:
        if d['_family']=='AP':
            costs=P.C.reshape(P.p,int(d['n']),int(d['n']));all_y=set()
            for perm in itertools.permutations(range(int(d['n']))):
                all_y.add(tuple(int(sum(costs[k,i,perm[i]] for i in range(int(d['n'])))) for k in range(P.p)))
        else:
            assert d['_family']=='KP' and P.n<=20;all_y=set()
            for x in itertools.product((0,1),repeat=P.n):
                if int(sum(w*v for w,v in zip(d['weights'],x)))<=d['capacity']:
                    all_y.add(tuple(map(int,P.C@x)))
        nd={y for y in all_y if not any(z!=y and all(a<=b for a,b in zip(z,y)) for z in all_y)}
        assert {tuple(a) for a in ys}==nd
        brute={'feasible_objective_vectors':len(all_y),'pareto_points':len(nd),'exact_match':True}
    notes=[]
    if len(journal)<len(accepts):notes.append('accepted.jsonl is an exact prefix; full witness records are in terminal/checkpoint files')
    if missing:notes.append(f'oracles.jsonl is an exact observed prefix with {missing} fewer rows than the terminal scalarization total; terminal/checkpoint controller counters were retained without reconstructing events')
    if len(calls)!=t['counters']['milp_calls']:
        notes.append('individual MILP journal count differs from controller aggregate; both records retained without reconstruction')
    return {'audit':'PASS_WITH_JOURNAL_NOTES' if notes else 'PASS','family':d['_family'],'status':t['status'],'input_sha256':t['input_sha256'],'accepted_witnesses_verified':len(accepts),'nondominance_within_observed_set':True,'independent_full_pareto_reference':brute,'controller_oracle_events':len(events),'controller_scalarizations':t['counters']['scalarizations'],'individual_milp_records':len(calls),'controller_milp_calls':t['counters']['milp_calls'],'acceptance_journal_rows':len(journal),'terminal_acceptance_records':len(accepts),'journal_notes':notes,'checkpoints':cps,'worker_ready':t['worker_ready'],'elapsed_s':t['elapsed_s'],'shutdown_elapsed_s':t['shutdown_elapsed_s']}

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--prefix',required=True);a.add_argument('--input',required=True);a.add_argument('--exhaustive',action='store_true');a.add_argument('--output',required=True)
    v=a.parse_args();root=Path(__file__).resolve().parent
    result=validate(root,Path(v.prefix),Path(v.input),v.exhaustive)
    Path(v.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
