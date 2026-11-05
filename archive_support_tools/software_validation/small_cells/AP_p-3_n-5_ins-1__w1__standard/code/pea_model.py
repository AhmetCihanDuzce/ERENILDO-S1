"""Minimal neutral BinaryMOIP model class for parallel PEA oracle evaluation.
Verbatim class extracted from WP55 frozen helper code; SOTA algorithms excluded.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import numpy as np
Array=np.ndarray

@dataclass(frozen=True)
class BinaryMOIP:
    """min C x  s.t. A_ub x <= b_ub, A_eq x = b_eq, x in {0,1}^n."""
    C: Array
    A_ub: Optional[Array] = None
    b_ub: Optional[Array] = None
    A_eq: Optional[Array] = None
    b_eq: Optional[Array] = None

    def __post_init__(self):
        C = np.asarray(self.C, dtype=float)
        if C.ndim != 2:
            raise ValueError("C must be a p x n matrix.")
        object.__setattr__(self, "C", C)

        n = C.shape[1]
        if self.A_ub is not None:
            A = np.asarray(self.A_ub, dtype=float)
            b = np.asarray(self.b_ub, dtype=float)
            if A.shape[1] != n or A.shape[0] != len(b):
                raise ValueError("A_ub/b_ub dimension mismatch.")
            object.__setattr__(self, "A_ub", A)
            object.__setattr__(self, "b_ub", b)

        if self.A_eq is not None:
            A = np.asarray(self.A_eq, dtype=float)
            b = np.asarray(self.b_eq, dtype=float)
            if A.shape[1] != n or A.shape[0] != len(b):
                raise ValueError("A_eq/b_eq dimension mismatch.")
            object.__setattr__(self, "A_eq", A)
            object.__setattr__(self, "b_eq", b)

    @property
    def p(self) -> int:
        return self.C.shape[0]

    @property
    def n(self) -> int:
        return self.C.shape[1]

