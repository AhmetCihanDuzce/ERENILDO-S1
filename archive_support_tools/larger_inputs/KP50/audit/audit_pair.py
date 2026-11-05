import json, pathlib, sys
from collections import Counter
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from run_checkpoint_multi import load, validate_witness
P,d=load(ROOT/'inputs/KP_p3_n50_ins1.json')
assert (P.p,P.n,d['_family'])==(3,50,'KP')
methods={}
for method in ('standard','block2'):
    prefix=ROOT/'runs'/f'KP_n50_p3_i1_{method}_w1'
    terminal=json.loads(prefix.with_suffix('.terminal.json').read_text())
    assert terminal['status']=='SEARCH_COMPLETED'
    accepted=terminal['accepted_points_with_witnesses']
    assert len(accepted)==terminal['point_count']
    points=[]
    for rec in accepted:
        vals=validate_witness(P,d,rec['x'],y=rec['y_min'])
        assert list(-vals)==rec['profits_max']
        points.append(tuple(map(int,-vals)))
    assert len(set(points))==len(points)
    for i,a in enumerate(points):
        for j,b in enumerate(points):
            if i!=j:
                assert not (all(x>=y for x,y in zip(b,a)) and any(x>y for x,y in zip(b,a)))
    counters=terminal['counters']
    multiplier=3 if method=='standard' else 2
    assert counters['milp_calls']==multiplier*counters['feasible']+counters['infeasible']
    assert counters['feasible']+counters['infeasible']==counters['scalarizations']
    cps={}
    for t in (300,600,900,1200):
        cp=json.loads(prefix.with_name(prefix.name+f'.checkpoint_{t}.json').read_text())
        witness_points=[]
        for rec in cp['accepted_points_with_witnesses']:
            vals=validate_witness(P,d,rec['x'],y=rec['y_min'])
            witness_points.append(tuple(map(int,-vals)))
        assert cp['point_count']==len(witness_points)
        assert len(set(witness_points))==len(witness_points)
        if t==300: assert all(r['accepted_elapsed_s']<=300 for r in cp['accepted_points_with_witnesses'])
        else: assert cp['carried_forward_after_completion'] is True
        cps[t]=set(witness_points)
    methods[method]={'terminal':terminal,'points':set(points),'checkpoints':cps}
assert methods['standard']['points']==methods['block2']['points']

def nondominated(points):
    return {a for a in points if not any(b!=a and all(x>=y for x,y in zip(b,a)) for b in points)}
rows=[]
for t in (300,600,900,1200):
    S=methods['standard']['checkpoints'][t]; E=methods['block2']['checkpoints'][t]
    U=nondominated(S|E)
    rows.append({'checkpoint_s':t,'standard_points':len(S),'block2_points':len(E),'union_nondominated':len(U),'standard_contribution':len(S&U),'block2_contribution':len(E&U),'common_nondominated':len(S&E&U),'standard_only_nondominated':len((S-E)&U),'block2_only_nondominated':len((E-S)&U),'standard_completion_status':methods['standard']['terminal']['status'],'block2_completion_status':methods['block2']['terminal']['status']})
summary={}
for method,x in methods.items():
 t=x['terminal'];summary[method]={'status':t['status'],'search_completed_elapsed_s':t['search_completed_elapsed_s'],'wall_elapsed_s':t['elapsed_s'],'point_count':t['point_count'],'milp_calls':t['counters']['milp_calls'],'scalarizations':t['counters']['scalarizations'],'feasible_subproblems':t['counters']['feasible'],'infeasible_subproblems':t['counters']['infeasible']}
std=summary['standard']; er=summary['block2']
summary['comparison']={'input_sha256':methods['standard']['terminal']['input_sha256'],'terminal_sets_identical':True,'shared_terminal_points':len(methods['standard']['points']),'standard_only_terminal_points':0,'block2_only_terminal_points':0,'milp_calls_saved':std['milp_calls']-er['milp_calls'],'milp_call_reduction_percent':100*(std['milp_calls']-er['milp_calls'])/std['milp_calls'],'search_completion_seconds_saved':std['search_completed_elapsed_s']-er['search_completed_elapsed_s'],'search_completion_time_reduction_percent':100*(std['search_completed_elapsed_s']-er['search_completed_elapsed_s'])/std['search_completed_elapsed_s'],'independent_full_pareto_reference':'NOT_AVAILABLE'}
(ROOT/'audit/PAIR_AUDIT.json').write_text(json.dumps({'audit':'PASS','family':'KP','n':50,'p':3,'workers':1,'input_sha256':summary['comparison']['input_sha256'],'methods':summary,'checkpoint_comparison':rows,'checks':['all decision witnesses feasible and objective values match','objective vectors unique and mutually nondominated within each terminal set','MILP call identities pass','all four checkpoint snapshots validate','terminal objective sets identical between methods'],'full_front_note':'Independent full Pareto oracle not available; both runs report SEARCH_COMPLETED. The paired agreement is not an independent completeness proof.'},indent=2)+'\n')
(ROOT/'PAIR_SUMMARY.json').write_text(json.dumps({'methods':summary,'checkpoint_comparison':rows},indent=2)+'\n')
with (ROOT/'CHECKPOINT_COMPARISON.csv').open('w') as f:
    headers=list(rows[0]);f.write(','.join(headers)+'\n')
    for row in rows:f.write(','.join(str(row[h]) for h in headers)+'\n')
print(json.dumps({'audit':'PASS','methods':{k:{a:v for a,v in val.items() if a!='checkpoints'} for k,val in summary.items() if k in ('standard','block2')},'comparison':summary['comparison'],'checkpoints':rows},indent=2))
