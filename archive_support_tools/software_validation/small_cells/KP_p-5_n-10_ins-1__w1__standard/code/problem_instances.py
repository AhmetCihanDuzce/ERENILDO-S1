"""Deterministic, self-contained multiobjective KP/AP/ATSP data generation and exact binary MILP formulations."""
import hashlib,itertools,json,math
from pathlib import Path
import numpy as np
from sota_python_common import core

def stable_json(obj):
    return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False)

def instance_sha256(spec):
    return hashlib.sha256(stable_json(spec).encode('utf-8')).hexdigest()

def generate(problem,n,p,seed):
    problem=problem.upper()
    if not(3<=p<=5):raise ValueError('3<=p<=5 for this frozen experiment')
    if n<3:raise ValueError('n>=3')
    rng=np.random.default_rng(int(seed))
    spec={'schema':'EREN-ILDO/1','problem':problem,'n':int(n),'p':int(p),'seed':int(seed)}
    if problem=='KP':
        if n>400:raise ValueError('KP n>400 not supported by this model adapter')
        W=rng.integers(1,21,size=n,dtype=np.int64)
        spec.update(profits=rng.integers(1,51,size=(p,n),dtype=np.int64).tolist(),weights=W.tolist(),capacity=int(np.sum(W)//2))
    elif problem=='AP':
        if n>50:raise ValueError('AP n>50 not supported by this model adapter')
        spec.update(costs=rng.integers(1,51,size=(p,n,n),dtype=np.int64).tolist())
    elif problem=='TSP':
        if n>45:raise ValueError('TSP n>45 not supported by this dense binary-MTZ research backend')
        C=rng.integers(1,51,size=(p,n,n),dtype=np.int64)
        for k in range(p):np.fill_diagonal(C[k],0)
        spec.update(costs=C.tolist(),directed=True,formulation='mtz_binary')
    else:raise ValueError('problem must be KP, AP, or TSP')
    return spec

def _integer_array(a,name,shape):
    v=np.asarray(a,dtype=float)
    if v.shape!=shape or not np.all(np.isfinite(v)) or not np.all(v==np.rint(v)):
        raise ValueError(f'{name} must be finite integer array of shape {shape}')
    if np.max(np.abs(v),initial=0)>1_000_000:
        raise ValueError(f'{name} out of declared coefficient range +/-1e6')
    return v

def build_model(spec):
    if spec.get('schema')!='EREN-ILDO/1':raise ValueError('Unsupported schema')
    fam=spec['problem'].upper();p=int(spec['p']);n=int(spec['n'])
    if not(3<=p<=5 and n>=3):raise ValueError('Require 3<=p<=5 and n>=3')
    if fam=='KP':
        if n>400:raise ValueError('KP limit n<=400')
        profits=_integer_array(spec['profits'],'profits',(p,n))
        w=_integer_array(spec['weights'],'weights',(n,))
        cap=float(spec['capacity'])
        if cap<0 or cap!=int(cap) or np.any(w<0):raise ValueError('Invalid capacity or weights')
        return core.BinaryMOIP(C=-profits,A_ub=w.reshape(1,n),b_ub=np.array([cap]))
    if fam=='AP':
        if n>50:raise ValueError('AP limit n<=50')
        costs=_integer_array(spec['costs'],'costs',(p,n,n))
        C=costs.reshape(p,n*n)
        A=np.zeros((2*n,n*n),dtype=float)
        for i in range(n):
            for j in range(n):
                A[i,i*n+j]=1
                A[n+j,i*n+j]=1
        return core.BinaryMOIP(C=C,A_eq=A,b_eq=np.ones(2*n))
    if fam=='TSP':
        if n>45:raise ValueError('TSP limit n<=45')
        if spec.get('directed') is not True:raise ValueError('TSP model requires directed:true')
        costs=_integer_array(spec['costs'],'costs',(p,n,n))
        if np.any(np.diagonal(costs,axis1=1,axis2=2)!=0):
            raise ValueError('TSP diagonal must be 0 (self-arcs excluded)')
        form=spec.get('formulation','mtz_binary')
        arcs=[(i,j) for i in range(n) for j in range(n) if i!=j]
        na=len(arcs)
        if form=='dfj_dense':
            if n>10:raise ValueError('Exponential DFJ formulation restricted to n<=10')
            C=np.asarray([[costs[k,i,j] for i,j in arcs] for k in range(p)],float)
            E=np.zeros((2*n,na),float)
            for a,(i,j) in enumerate(arcs):E[i,a]=1;E[n+j,a]=1
            subsets=[s for k in range(2,n) for s in itertools.combinations(range(1,n),k)]
            # A subtour not containing vertex zero necessarily exists in any multi-cycle assignment.
            A=np.zeros((len(subsets),na),float)
            for row,sub in enumerate(subsets):
                inside=set(sub)
                for a,(i,j) in enumerate(arcs):
                    if i in inside and j not in inside:A[row,a]=-1
            return core.BinaryMOIP(C=C,A_eq=E,b_eq=np.ones(2*n),A_ub=A,b_ub=-np.ones(len(A)))
        if form!='mtz_binary':raise ValueError('Formulation must be mtz_binary or dfj_dense')
        # All-binary Miller–Tucker–Zemlin order encoding: u_i = sum(2^b z_i,b).
        # For i>=1: 1 <= u_i <= n-1; for arcs (i,j) with i,j>=1:
        # u_i-u_j+n*x_ij <= n-1. Degree equalities force one Hamiltonian cycle.
        nbits=max(1,(n-1).bit_length())
        nz=(n-1)*nbits
        total=na+nz
        C=np.zeros((p,total),float)
        for a,(i,j) in enumerate(arcs):C[:,a]=costs[:,i,j]
        E=np.zeros((2*n,total),float)
        for a,(i,j) in enumerate(arcs):E[i,a]=1;E[n+j,a]=1
        z={ (i,b):na+(i-1)*nbits+b for i in range(1,n) for b in range(nbits)}
        A=[];bs=[]
        for i in range(1,n):
            row=np.zeros(total,float)
            for b in range(nbits):row[z[i,b]]=2**b
            A.append(row);bs.append(n-1)
            A.append(-row);bs.append(-1)
        for a,(i,j) in enumerate(arcs):
            if i and j:
                row=np.zeros(total,float)
                row[a]=n
                for b in range(nbits):
                    row[z[i,b]]+=2**b;row[z[j,b]]-=2**b
                A.append(row);bs.append(n-1)
        return core.BinaryMOIP(C=C,A_eq=E,b_eq=np.ones(2*n),A_ub=np.asarray(A),b_ub=np.asarray(bs,dtype=float))
    raise ValueError('problem must be KP, AP or TSP')

def _pareto_archive(images):
    nd=[]
    for y in images:
        if y in nd:continue
        if any(all(a<=b for a,b in zip(z,y)) for z in nd):continue
        nd=[z for z in nd if not all(a<=b for a,b in zip(y,z))]
        nd.append(y)
    return sorted(nd)

def enumerate_exact(spec):
    """Independent full feasible solution enumeration; refuses exorbitant sizes."""
    fam=spec['problem'].upper();n=int(spec['n']);p=int(spec['p'])
    limit={'KP':20,'AP':8,'TSP':9}[fam]
    if n>limit:
        raise ValueError(f'Complete enumeration of {fam} n={n} disabled above n={limit}; use separately justified HPC protocol')
    vals=[]
    if fam=='KP':
        C=np.asarray(spec['profits'],int);w=np.asarray(spec['weights'],int);cap=int(spec['capacity'])
        for mask in range(1<<n):
            x=np.fromiter(((mask>>j)&1 for j in range(n)),dtype=np.int64,count=n)
            if np.dot(w,x)<=cap:vals.append(tuple(map(int,-C@x)))
        total=2**n
    elif fam=='AP':
        C=np.asarray(spec['costs'],int)
        for perm in itertools.permutations(range(n)):
            vals.append(tuple(int(sum(C[k,i,perm[i]] for i in range(n))) for k in range(p)))
        total=math.factorial(n)
    else:
        C=np.asarray(spec['costs'],int)
        for perm in itertools.permutations(range(1,n)):
            tour=(0,)+perm+(0,)
            vals.append(tuple(int(sum(C[k,tour[i],tour[i+1]] for i in range(n))) for k in range(p)))
        total=math.factorial(n-1)
    return dict(points=_pareto_archive(vals),total_candidates=total,feasible_images=len(set(vals)),algorithm='independent_complete_enumeration')
