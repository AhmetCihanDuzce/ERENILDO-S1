from pathlib import Path
import json,os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import numpy as np
ROOT=Path(__file__).resolve().parent

def nd(points):
 values=np.array(sorted(points),dtype=np.int64);keep=[]
 for i in range(0,len(values),128):
  x=values[i:i+128];dom=(values[None,:,:]<=x[:,None,:]).all(axis=2)&(values[None,:,:]<x[:,None,:]).any(axis=2)
  keep.extend(map(tuple,x[~dom.any(axis=1)].tolist()))
 return set(keep)

def main():
 comparisons=[]
 for p in (3,4):
  for t in (300,600,900,1200):
   sets=[]
   for m in ['standard','block2']:
    cp=json.loads((ROOT/'runs'/f'AP_n30_p{p}_i1_{m}_w4.checkpoint_{t}.json').read_text());sets.append(set(map(tuple,cp['points_minimization'])))
   a,b=sets;raw=a|b;u=nd(raw);aa=a&u;bb=b&u
   assert len(u)==len(raw),'Dominated vector found in observed union'
   row={'objectives':p,'checkpoint_s':t,'standard_points':len(a),'block2_points':len(b),'nondominated_union':len(u),'shared':len(aa&bb),'standard_only':len(aa-bb),'block2_only':len(bb-aa),'standard_union_contribution':len(aa)/len(u) if u else None,'block2_union_contribution':len(bb)/len(u) if u else None}
   assert row['standard_only']+row['block2_only']+row['shared']==len(u)
   comparisons.append(row)
 (ROOT/'PAIR_COMPARISON.json').write_text(json.dumps(comparisons,indent=2)+'\n')
 import csv
 with (ROOT/'PAIR_COMPARISON.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(comparisons[0]));w.writeheader();w.writerows(comparisons)
 print(json.dumps([r for r in comparisons if r['checkpoint_s']==1200]))
if __name__=='__main__':main()
