"""Independent evidence audit; never launches a performance experiment."""
import argparse, hashlib, itertools, json
from pathlib import Path

def read_jsonl(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]

def validate(root, prefix, input_path, exhaustive=False):
    d=json.loads(input_path.read_text())
    t=json.loads(prefix.with_suffix('.terminal.json').read_text())
    journal_accepts=read_jsonl(prefix.with_suffix('.accepted.jsonl'))
    events=read_jsonl(prefix.with_suffix('.oracles.jsonl'))
    assert t['status'] in ('SEARCH_COMPLETED','RIGHT_CENSORED') and t['error'] is None
    assert t['input_sha256']==hashlib.sha256(input_path.read_bytes()).hexdigest()
    for name,h in t['source_sha256'].items():
        assert hashlib.sha256((root/'src'/name).read_bytes()).hexdigest()==h
    accepts=t['accepted_points_with_witnesses']
    assert journal_accepts==accepts[:len(journal_accepts)], 'Acceptance journal is not an exact prefix of terminal accepted records'
    assert len({tuple(a['y_min']) for a in accepts})==len(accepts)==t['point_count']
    assert sorted(a['y_min'] for a in accepts)==t['points_minimization']
    assert all(a['accepted_elapsed_s']<=b['accepted_elapsed_s'] for a,b in zip(accepts,accepts[1:]))
    for a in accepts:
        x=a['x']; assert len(x)==d['n'] and all(v in (0,1) for v in x)
        assert sum(w*v for w,v in zip(d['weights'],x))<=d['capacity']
        y=[-sum(c*v for c,v in zip(row,x)) for row in d['profits']]
        assert y==a['y_min'] and [-v for v in y]==a['profits_max']
        assert 0<=a['accepted_elapsed_s']<=t['budget_s']
        assert any(e['y_min']==y and e['completed_elapsed_s']<=a['accepted_elapsed_s'] for e in events)
    ys=[a['y_min'] for a in accepts]
    assert all(not (all(x<=y for x,y in zip(a,b)) and a!=b) for a in ys for b in ys)
    totals={k:0 for k in t['counters']}
    previous=0
    for e in events:
        assert previous<=e['completed_elapsed_s']<=t['budget_s'];previous=e['completed_elapsed_s']
        feasible=e['y_min'] is not None
        assert e['calls']==(d['p'] if t['method']=='standard' else d['p']-1) if feasible else e['calls']==1
        totals['scalarizations']+=1;totals['feasible' if feasible else 'infeasible']+=1
        for dst,src in [('milp_calls','calls'),('bb_nodes','nodes'),('completed_oracle_solver_s','solver_s'),('oracle_wall_s','oracle_wall_s')]:totals[dst]+=e[src]
        assert totals==e['counters']
    oracle_journal_missing=t['counters']['scalarizations']-totals['scalarizations']
    if oracle_journal_missing:
        # A completed controller can have a durable terminal/checkpoint record
        # while its append-only oracle journal ends at an earlier committed
        # prefix. Retain this as an explicit journal limitation; never invent
        # the missing event rows.
        assert t['status']=='SEARCH_COMPLETED' and oracle_journal_missing>0
        assert events and events[-1]['counters']==totals
        assert all(totals[k]<=t['counters'][k] for k in totals)
        assert t['counters']['scalarizations']==t['counters']['feasible']+t['counters']['infeasible']
        assert t['counters']['milp_calls']==(d['p']-1)*t['counters']['feasible']+t['counters']['infeasible']
    else:
        assert totals==t['counters']
    cps=[]
    assert len(t['checkpoints'])==len(t['checkpoints_s'])
    for target,stored in zip(t['checkpoints_s'],t['checkpoints']):
        cp=json.loads(prefix.with_name(prefix.name+f'.checkpoint_{target:g}.json').read_text())
        assert cp==stored
        selected=[a for a in accepts if a['accepted_elapsed_s']<=target]
        ev=[e for e in events if e['completed_elapsed_s']<=target]
        assert cp['accepted_points_with_witnesses']==selected
        assert cp['point_count']==len(selected) and cp['points_minimization']==[a['y_min'] for a in selected]
        if cp['status']=='SEARCH_COMPLETED' and cp['carried_forward_after_completion']:
            assert cp['counters']==t['counters']
        else:
            assert cp['counters']==(ev[-1]['counters'] if ev else {k:0 for k in totals})
        assert cp['carried_forward_after_completion'] or cp['observed_elapsed_s']>=target
        cps.append({'checkpoint_s':target,'point_count':cp['point_count'],'milp_calls':cp['counters']['milp_calls'],'scalarizations':cp['counters']['scalarizations'],'observed_elapsed_s':cp['observed_elapsed_s'],'status':cp['status']})
    calls=[]
    for f in prefix.parent.glob(prefix.name+'.worker*.calls.jsonl'):
        rows=read_jsonl(f)
        assert [r['call'] for r in rows]==list(range(1,len(rows)+1))
        assert all(r['status'] in ('HighsModelStatus.kOptimal','HighsModelStatus.kInfeasible') for r in rows)
        assert all(a['monotonic_ns']<=b['monotonic_ns'] for a,b in zip(rows,rows[1:]))
        calls+=rows
    # On a censored run, worker-call records can be below the committed
    # controller total (lost journal rows) or above it (completed MILP stages
    # inside oracle calls that were not committed before the cutoff).
    if t['status']=='SEARCH_COMPLETED':assert t['inflight_oracle']==t['queued_tasks']==0
    brute=None
    if exhaustive:
        assert d['n']<=12
        all_y=set()
        for x in itertools.product((0,1),repeat=d['n']):
            if sum(w*v for w,v in zip(d['weights'],x))<=d['capacity']:
                all_y.add(tuple(-sum(c*v for c,v in zip(row,x)) for row in d['profits']))
        nd={y for y in all_y if not any(z!=y and all(a<=b for a,b in zip(z,y)) for z in all_y)}
        assert {tuple(a) for a in ys}==nd
        brute={'feasible_objective_vectors':len(all_y),'pareto_points':len(nd),'exact_match':True}
    incomplete_accepts=len(journal_accepts)<len(accepts)
    call_delta=len(calls)-t['counters']['milp_calls']
    incomplete_calls=call_delta<0
    trailing_calls=call_delta>0 and t['status']=='RIGHT_CENSORED'
    notes=[]
    if incomplete_accepts:notes.append('accepted.jsonl is an exact prefix only; complete accepted witness sets and timestamps are retained in atomic checkpoints and terminal JSON')
    if oracle_journal_missing:notes.append(f'oracles.jsonl ends at an exact committed prefix and is missing {oracle_journal_missing} terminal oracle event rows; full accepted witnesses and aggregate counters are retained in terminal/checkpoints, and missing event rows were not reconstructed')
    if incomplete_calls:notes.append('individual MILP call journal has fewer rows than the controller aggregate, including after shutdown; completed-oracle aggregate MILP totals remain cross-checked against scalarization identities and oracle events')
    if trailing_calls:notes.append('additional individual MILP records belong to solver stages completed inside censored, uncommitted oracle calls')
    return {'audit':'PASS_WITH_JOURNAL_NOTES' if notes else 'PASS','status':t['status'],'input_sha256':t['input_sha256'],'accepted_witnesses_verified':len(accepts),'nondominance_within_observed_set':True,'independent_full_pareto_reference':brute,'controller_oracle_events':len(events),'controller_scalarizations':t['counters']['scalarizations'],'oracle_journal_missing_records_vs_controller_total':oracle_journal_missing,'individual_milp_records':len(calls),'controller_milp_calls':t['counters']['milp_calls'],'individual_milp_records_minus_controller_calls':call_delta,'individual_milp_journal_missing_records_vs_controller_total':max(0,-call_delta),'trailing_milp_records_beyond_committed_oracles':max(0,call_delta),'acceptance_journal_rows':len(journal_accepts),'terminal_acceptance_records':len(accepts),'acceptance_journal_missing_records':len(accepts)-len(journal_accepts),'journal_notes':notes,'checkpoints':cps,'worker_ready':t['worker_ready'],'elapsed_s':t['elapsed_s'],'shutdown_elapsed_s':t['shutdown_elapsed_s']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prefix',required=True);p.add_argument('--input',required=True);p.add_argument('--exhaustive',action='store_true');p.add_argument('--output',required=True)
    a=p.parse_args();root=Path(__file__).resolve().parent
    r=validate(root,Path(a.prefix),Path(a.input),a.exhaustive)
    Path(a.output).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
