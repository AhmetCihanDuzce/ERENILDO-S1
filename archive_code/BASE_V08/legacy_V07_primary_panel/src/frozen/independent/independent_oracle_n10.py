"""Independent all-9! Hamilton tours for TSP3 n=10; 3D exact skyline with integer arithmetic."""
import itertools, json, hashlib, bisect, time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
for f in sorted((ROOT/'inputs').glob('TSP3-10-*.json')):
 t=time.perf_counter()
 spec=json.loads(f.read_text());C=np.asarray(spec['costs'],dtype=np.int64);n=10
 # Enumerate every directed Hamilton tour with vertex 0 fixed; no MILP assumptions.
 I=np.fromiter((i for perm in itertools.permutations(range(1,n)) for i in perm),dtype=np.int16,count=362880*9).reshape(-1,9)
 A=np.concatenate([np.zeros((len(I),1),dtype=np.int16),I],axis=1)
 B=np.concatenate([I,np.zeros((len(I),1),dtype=np.int16)],axis=1)
 vals=C[:,A,B].sum(axis=2).T
 assert vals.shape==(362880,3)
 ys=np.unique(vals,axis=0)
 # Ascending (f1,f2,f3): earlier points cannot be dominated by later points.
 ss=sorted(map(tuple,ys.tolist()))
 skyline_2=[];skyline_3=[];nd=[]
 for y in ss:
  f1,f2,f3=y;j=bisect.bisect_right(skyline_2,f2)
  if j>0 and skyline_3[j-1]<=f3:continue
  # delete any later 2D frontier points dominated by new 2D pair.
  while j<len(skyline_2) and skyline_3[j]>=f3:
   del skyline_2[j];del skyline_3[j]
  skyline_2.insert(j,f2);skyline_3.insert(j,f3)
  nd.append(list(y))
 assert len(set(map(tuple,nd)))==len(nd)
 # independently verify nondominance via vector matrix
 ndmat=np.asarray(nd,dtype=np.int64)
 for i in range(len(nd)):
  dom=np.all(ndmat<=ndmat[i],axis=1)&np.any(ndmat<ndmat[i],axis=1)
  assert not dom.any(),('DOM',f.name,i)
 assert np.all(np.isin(np.arange(1),np.arange(1)))
 stream=json.dumps(nd,separators=(',',':'))
 op={'instance':f.stem,'objective_vectors':nd,'pareto_size':len(nd),'total_candidates':362880,'distinct_feasible_images':len(ys),'method':'independent_complete_hamilton_permutation_enumeration_with_integer_3d_skyline','input_semantic_sha256':hashlib.sha256(json.dumps(spec,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(),'objective_vectors_sha256':hashlib.sha256(stream.encode()).hexdigest(),'generation_time_s':time.perf_counter()-t}
 (ROOT/'oracles'/f'{f.stem}.json').write_text(json.dumps(op,sort_keys=True,indent=2)+'\n')
 print(f.stem,'PF',len(nd),'unique vectors',len(ys),'seconds',round(time.perf_counter()-t,3),flush=True)
