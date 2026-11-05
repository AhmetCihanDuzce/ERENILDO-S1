"""Legacy import-compatible narrow bridge for the frozen PEA oracle source.
Exposes ONLY the PEA model, persistent HiGHS and objective hash utilities.
No alternative exact algorithms, SOTA timing tables, or comparative baselines.
"""
from types import SimpleNamespace
from pea_model import BinaryMOIP
from pea_highs import PersistentHighsMOIP
core=SimpleNamespace(BinaryMOIP=BinaryMOIP)
dp=SimpleNamespace(PersistentHighsMOIP=PersistentHighsMOIP)
def canonical(points):
    return sorted(tuple(map(int,p)) for p in points)
def fnv64(points):
    pts=canonical(points);h=1469598103934665603
    for p in pts:
        s=','.join(map(str,p))+';'
        for ch in s:
            h^=ord(ch);h=(h*1099511628211)&((1<<64)-1)
    return f'{h:016x}'
