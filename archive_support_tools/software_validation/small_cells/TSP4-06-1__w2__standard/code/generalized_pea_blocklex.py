from __future__ import annotations
import json, sys, math
from pathlib import Path
from time import perf_counter
import numpy as np, pandas as pd
BASE=Path('/mnt/data'); sys.path.insert(0,str(BASE))
from sota_python_common import dp, core, fnv64
from pea_highs import SolverUnresolvedError


def load_kp(p,n,inst):
    path=BASE/(f'kirlik_p{p}_subset.json')
    rec=json.load(open(path))
    d=next(x for x in rec if int(x['n'])==n and int(x['id'])==inst)
    P=core.BinaryMOIP(C=-np.asarray(d['profits'],float),
                      A_ub=np.asarray([d['weights']],float),
                      b_ub=np.asarray([d['capacity']],float))
    return P,d


def obj_bounds(P):
    lb=np.array([sum(min(0,int(v)) for v in P.C[j]) for j in range(P.p)],dtype=int)
    ub=np.array([sum(max(0,int(v)) for v in P.C[j]) for j in range(P.p)],dtype=int)
    return lb,ub


def _certified_solve(solver, c, upper, completed_stages):
    """Keep solver status evidence at the oracle boundary.

    After an optimal stage, its incumbent remains feasible under the added
    optimum bound. Later infeasibility is an inconsistent certificate path,
    not evidence that the original epsilon subproblem was infeasible.
    """
    x, nodes, elapsed, status = solver.solve(c, upper=upper)
    statuses = solver._hmod.HighsModelStatus
    if status == statuses.kOptimal and x is not None:
        return x, nodes, elapsed, status
    if status == statuses.kInfeasible and x is None and completed_stages == 0:
        return x, nodes, elapsed, status
    raise SolverUnresolvedError(
        'Unresolved or inconsistent lexicographic stage '
        f'after {completed_stages} completed stages', model_status=status,
    )


def lexsolve(P,solver,combo,mode='standard'):
    p=P.p
    # combo has p-1 entries; each is None for dummy d^i, or a full objective tuple.
    upper=[None]*p
    for i in range(p-1):
        if combo[i] is not None:
            upper[i]=int(combo[i][i])-1  # strict epsilon for integer images
    calls=nodes=0; st=0.0; maxcoef=0.0
    if mode=='standard':
        x=None
        for idx in range(p-1,-1,-1):
            x,n,t,_=_certified_solve(solver,P.C[idx],upper,calls)
            calls+=1; nodes+=n; st+=t
            if x is None:
                return None,calls,nodes,st,maxcoef
            y=np.rint(P.C@x).astype(int)
            upper[idx]=int(y[idx]) if upper[idx] is None else min(int(upper[idx]),int(y[idx]))
        return tuple(map(int,np.rint(P.C@x))),calls,nodes,st,maxcoef
    elif mode=='block2':
        lb,ub=obj_bounds(P)
        x=None
        # optimize fp,...,f3 separately
        for idx in range(p-1,1,-1):
            x,n,t,_=_certified_solve(solver,P.C[idx],upper,calls)
            calls+=1; nodes+=n; st+=t
            if x is None:
                return None,calls,nodes,st,maxcoef
            y=np.rint(P.C@x).astype(int)
            upper[idx]=int(y[idx]) if upper[idx] is None else min(int(upper[idx]),int(y[idx]))
        # trailing pair (f2,f1)
        U1=ub[0] if upper[0] is None else min(int(ub[0]),int(upper[0]))
        R1=max(0,int(U1-lb[0])); W2=R1+1
        c=W2*P.C[1]+P.C[0]
        maxcoef=float(np.max(np.abs(c)))
        x,n,t,_=_certified_solve(solver,c,upper,calls)
        calls+=1; nodes+=n; st+=t
        if x is None:
            return None,calls,nodes,st,maxcoef
        return tuple(map(int,np.rint(P.C@x))),calls,nodes,st,maxcoef
    else:
        raise ValueError(mode)


def combo_key(combo):
    return tuple(('D',i) if y is None else tuple(map(int,y)) for i,y in enumerate(combo))


def generalized_pea(P,mode='standard',max_nodes=2_000_000):
    solver=dp.PersistentHighsMOIP(P)
    p=P.p
    root=tuple([None]*(p-1))
    stack=[root]
    visited=set()
    Y=[]; Yset=set()
    calls=nodes=0; st=0.0; maxcoef=0.0; scalarizations=0
    t0=perf_counter()
    while stack:
        combo=stack.pop()
        ck=combo_key(combo)
        if ck in visited:
            continue
        visited.add(ck)
        y,c,n,t,mc=lexsolve(P,solver,combo,mode)
        scalarizations+=1; calls+=c; nodes+=n; st+=t; maxcoef=max(maxcoef,mc)
        if y is None:
            continue
        # Store criterion from generalized PEA Alg. 1 line 5:
        # Here [i]={1,...,i}, so -[i] means coordinates i+1,...,p
        # (higher-priority coordinates), NOT all coordinates except i.
        store=True
        for i in range(p-1):
            yi=combo[i]
            if yi is None:
                continue
            for j in range(i+1,p):
                if int(yi[j])>int(y[j]):
                    store=False; break
            if not store: break
        if store and y not in Yset:
            Yset.add(y);Y.append(y)
        # Scions: y_j >= Y^i_j for all i != j.
        for j in range(p-1):
            ok=True
            for i in range(p-1):
                if i==j: continue
                yi=combo[i]
                ref=-math.inf if yi is None else int(yi[j])
                if int(y[j])<ref:
                    ok=False;break
            if ok:
                child=list(combo); child[j]=y; child=tuple(child)
                if combo_key(child) not in visited:
                    stack.append(child)
        if len(visited)>max_nodes:
            raise RuntimeError('Traversal safety limit exceeded')
    return {
        'points':sorted(Yset), 'pf_size':len(Yset), 'hash':fnv64(Yset),
        'scalarizations':scalarizations,'calls_total':calls,'nodes':nodes,
        'solver_time_s':st,'elapsed_s':perf_counter()-t0,'visited_combinations':len(visited),
        'max_abs_objcoef':maxcoef
    }


def brute_force_pf(P,d):
    n=P.n; W=np.asarray(d['weights'],dtype=int); cap=int(d['capacity'])
    ys=[]
    for mask in range(1<<n):
        x=np.fromiter(((mask>>j)&1 for j in range(n)),dtype=int,count=n)
        if int(W@x)<=cap:
            ys.append(tuple(map(int,np.rint(P.C@x))))
    # incremental nondominated archive, minimization
    nd=[]
    for y in ys:
        dominated=False; keep=[]
        for z in nd:
            if all(z[j]<=y[j] for j in range(P.p)) and any(z[j]<y[j] for j in range(P.p)):
                dominated=True;break
        if dominated: continue
        for z in nd:
            if all(y[j]<=z[j] for j in range(P.p)) and any(y[j]<z[j] for j in range(P.p)):
                continue
            keep.append(z)
        if y not in keep: keep.append(y)
        nd=keep
    nd=sorted(set(nd))
    return {'points':nd,'pf_size':len(nd),'hash':fnv64(nd)}


def run_case(p,n,inst):
    P,d=load_kp(p,n,inst)
    b=brute_force_pf(P,d) if n<=20 else None
    rows=[]; details={}
    for mode in ['standard','block2']:
        r=generalized_pea(P,mode)
        details[mode]=r
        rows.append({'p':p,'n':n,'instance':inst,'mode':mode,'pf_size':r['pf_size'],'hash':r['hash'],
                     'scalarizations':r['scalarizations'],'calls_total':r['calls_total'],'nodes':r['nodes'],
                     'solver_time_s':r['solver_time_s'],'elapsed_s':r['elapsed_s'],
                     'visited_combinations':r['visited_combinations'],'max_abs_objcoef':r['max_abs_objcoef'],
                     'matches_bruteforce':(r['hash']==b['hash']) if b else None})
    out=pd.DataFrame(rows)
    out.to_csv(BASE/f'Generalized_PEA_p{p}_n{n}_i{inst}_summary.csv',index=False)
    json.dump({'bruteforce':b,'standard':details['standard'],'block2':details['block2']},
              open(BASE/f'Generalized_PEA_p{p}_n{n}_i{inst}_details.json','w'),indent=2)
    print('BRUTE',None if b is None else (b['pf_size'],b['hash']))
    print(out.to_string(index=False))

if __name__=='__main__':
    run_case(int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3]))
