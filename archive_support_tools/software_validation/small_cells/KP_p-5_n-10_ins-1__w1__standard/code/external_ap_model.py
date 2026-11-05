"""Kirlik–Sayin MOOLibrary AP DAT parser: p, n, and p n*n cost arrays. Original costs preserved, minimization."""
from pathlib import Path
import ast,hashlib
import numpy as np
from pea_model import BinaryMOIP

def load_model(path):
 path=Path(path);raw=path.read_bytes()
 lines=raw.decode('utf-8-sig').strip().splitlines()
 p,n=map(int,lines[:2])
 costs=np.asarray(ast.literal_eval('\n'.join(lines[2:])),dtype=int)
 if costs.shape!=(p,n,n):raise ValueError(('bad AP costs',costs.shape,(p,n,n)))
 if p!=3 or n<2:raise ValueError('unexpected AP metadata')
 N=n*n
 A=np.zeros((2*n,N),dtype=float)
 for i in range(n):
  for j in range(n): A[i,i*n+j]=1;A[n+j,i*n+j]=1
 P=BinaryMOIP(C=costs.reshape(p,N).astype(float),A_eq=A,b_eq=np.ones(2*n))
 spec={'family':'AP','p':p,'n':n,'sha256':hashlib.sha256(raw).hexdigest(),'raw_costs':costs.tolist()}
 return P,spec
