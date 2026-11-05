"""Strict parser for byte-identical Kirlik-Sayin KP DAT (maximize profits)."""
import pathlib,ast,hashlib
import numpy as np
from pea_model import BinaryMOIP

def load_model(path):
    p=pathlib.Path(path)
    lines=p.read_text().strip().splitlines()
    obj=int(lines[0]);n=int(lines[1]);cap=int(lines[2]);profits=ast.literal_eval(''.join(lines[3:-1]));weights=ast.literal_eval(lines[-1])
    assert n==20 and obj in (4,5) and len(profits)==obj and all(len(q)==n for q in profits) and len(weights)==n
    assert all(isinstance(z,int) for row in profits for z in row)
    assert all(isinstance(z,int) and z>=0 for z in weights) and isinstance(cap,int) and cap>0
    P=BinaryMOIP(C=-np.asarray(profits,dtype=float),A_ub=np.asarray([weights],dtype=float),b_ub=np.asarray([cap],dtype=float))
    return P,{'p':obj,'n':n,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'capacity':cap}
