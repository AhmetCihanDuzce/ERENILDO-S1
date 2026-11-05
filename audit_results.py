"""Check every selected primary record and binary witness; no solver executions."""
from pathlib import Path
from collections import Counter, defaultdict
import argparse,csv,gzip,hashlib,json
import numpy as np

def load(root,path):
    path=root/path;data=path.read_bytes()
    if path.suffix=='.gz':data=gzip.decompress(data)
    return data,json.loads(data)

def audit(root,out):
    rows=list(csv.DictReader((root/'tables/primary_runs.csv').open(encoding='utf-8-sig')))
    inputs={r['input_sha256']:r for r in csv.DictReader((root/'tables/input_registry.csv').open(encoding='utf-8-sig'))}
    pairs=defaultdict(dict);witnesses=0;independent_checks=0
    for row in rows:
        raw,d=load(root,row['record_path'])
        assert hashlib.sha256(raw).hexdigest()==row['terminal_sha256'],row['record_path']
        assert d['instance']==row['instance'] and d['method']==row['raw_method'] and int(d['workers'])==int(row['workers'])
        ct=d['counters'];f,i,calls=(int(ct[k]) for k in ['feasible','infeasible','milp_calls'])
        assert (f,i,calls)==(int(row['feasible_oracles']),int(row['infeasible_oracles']),int(row['milp_calls']))
        assert int(ct['scalarizations'])==f+i
        assert calls==(int(row['p'])-(row['raw_method']=='block2'))*f+i
        points=d.get('observed_pareto_vectors',d.get('points_minimization'))
        if row.get('point_vectors_record_path'):
            _,journal=load(root,row['point_vectors_record_path'])
            assert journal['counters']==ct and journal['instance']==row['instance']
            points=journal['observed_pareto_vectors']
        ys={tuple(y) for y in points};assert len(ys)==len(points)==int(row['points'])
        complete=d['status'] in ['EXACT_QA_PASS','SEARCH_COMPLETED']
        assert ('Completed' if complete else 'Time limit')==row['status']
        if complete:
            assert d.get('in_flight_or_queued_at_exit',d.get('inflight_oracle',0))==0 and d.get('queued_tasks',0)==0
            pairs[(row['cohort'],row['instance'],row['workers'])][row['raw_method']]=(ys,f,i,calls)
        else:assert d['status']=='RIGHT_CENSORED'
        if row['cohort'] in ['main_panel','reference_tsp12']:
            _,ref=load(root,'archive_code_data/BASE_V08/legacy_V07_primary_panel/analysis_v08/evidence/oracles/'+row['instance']+'.json')
            refs={tuple(y) for y in ref.get('pareto_points',ref.get('objective_vectors'))}
            assert ys==refs if complete else ys<=refs
            independent_checks+=1
        accepted=d.get('accepted_points_with_witnesses')
        if accepted is None:continue
        assert len(accepted)==len(ys) and {tuple(a['y_min']) for a in accepted}==ys
        inp=inputs[d['input_sha256']];raw,ip=load(root,inp['path'])
        assert hashlib.sha256(raw).hexdigest()==d['input_sha256']
        X=np.asarray([a['x'] for a in accepted],dtype=np.int64)
        Y=np.asarray([a['y_min'] for a in accepted],dtype=np.int64)
        assert np.all((X==0)|(X==1))
        n,p=int(row['n']),int(row['p'])
        if row['family']=='KP':
            assert np.all(X@np.asarray(ip['weights'],dtype=np.int64)<=int(ip['capacity']))
            expected=-(X@np.asarray(ip['profits'],dtype=np.int64).T)
        elif row['family']=='AP':
            matrix=X.reshape(-1,n,n)
            assert np.all(matrix.sum(axis=1)==1) and np.all(matrix.sum(axis=2)==1)
            expected=X@np.asarray(ip['costs'],dtype=np.int64).reshape(p,-1).T
        else:
            arcs=[(a,b) for a in range(n) for b in range(n) if a!=b]
            edge=X[:,:len(arcs)];matrix=np.zeros((len(X),n,n),dtype=np.int64)
            for j,(a,b) in enumerate(arcs):matrix[:,a,b]=edge[:,j]
            assert np.all(matrix.sum(axis=1)==1) and np.all(matrix.sum(axis=2)==1)
            for route in matrix:
                city=0;seen=set()
                while city not in seen:seen.add(city);city=int(np.argmax(route[city]))
                assert city==0 and len(seen)==n
            costs=np.asarray(ip['costs'],dtype=np.int64)
            expected=edge@np.asarray([[costs[k,a,b] for a,b in arcs] for k in range(p)]).T
        assert np.array_equal(expected,Y)
        for j in range(0,len(Y),128):
            assert not (np.all(Y[None,:,:]<=Y[j:j+128,None,:],axis=2)&np.any(Y[None,:,:]<Y[j:j+128,None,:],axis=2)).any()
        assert all(0<=a['accepted_elapsed_s']<=d['budget_s'] for a in accepted)
        witnesses+=len(accepted)
    matched=0
    for v in pairs.values():
        if len(v)!=2:continue
        a,b=v['standard'],v['block2'];assert a[:3]==b[:3] and a[3]-b[3]==a[1];matched+=1
    assert len(rows)==612 and Counter(r['status'] for r in rows)=={'Completed':533,'Time limit':79}
    assert matched==265 and witnesses==41614 and independent_checks==516
    report=dict(status='PASS',primary_records=612,completed_method_pairs_equal=matched,
                binary_witnesses_verified=witnesses,reference_set_comparisons=independent_checks,new_solver_runs=0)
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2))
    print(json.dumps(report))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--results',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();audit(a.results.resolve(),a.out.resolve())
