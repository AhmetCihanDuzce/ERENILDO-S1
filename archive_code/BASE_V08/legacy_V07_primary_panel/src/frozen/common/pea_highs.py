"""Minimal persistent, single-thread HiGHS MILP backend for PEA oracle comparison.
Verbatim model class extracted from existing frozen HiGHS helper; no DPA algorithms/results.
"""
from __future__ import annotations
from typing import Optional,Sequence
import numpy as np

class PersistentHighsMOIP:
    """Persistent single-thread HiGHS model using SciPy's bundled HiGHS bindings.

    The base MILP is loaded once. p additional rows represent objective upper bounds;
    each scalarized solve only changes row upper bounds and column costs.
    """
    def __init__(self,P):
        import scipy.sparse as sp
        from scipy.optimize._highspy import _core as _h
        self._hmod=_h; self.P=P
        n=P.n; rows=[]; lo=[]; up=[]
        if P.A_ub is not None:
            rows.append(np.asarray(P.A_ub,float));
            lo.extend([-np.inf]*P.A_ub.shape[0]); up.extend(map(float,P.b_ub))
        if P.A_eq is not None:
            rows.append(np.asarray(P.A_eq,float));
            lo.extend(map(float,P.b_eq)); up.extend(map(float,P.b_eq))
        self.base_rows=len(lo)
        rows.append(np.asarray(P.C,float))
        lo.extend([-np.inf]*P.p); up.extend([np.inf]*P.p)
        A=np.vstack(rows) if rows else np.zeros((P.p,n))
        A=sp.csc_matrix(A)

        lp=_h.HighsLp()
        lp.num_col_=n; lp.num_row_=A.shape[0]
        lp.a_matrix_.num_col_=n; lp.a_matrix_.num_row_=A.shape[0]
        lp.a_matrix_.format_=_h.MatrixFormat.kColwise
        lp.col_cost_=np.zeros(n,dtype=float)
        lp.col_lower_=np.zeros(n,dtype=float)
        lp.col_upper_=np.ones(n,dtype=float)
        lp.row_lower_=np.asarray(lo,dtype=float)
        lp.row_upper_=np.asarray(up,dtype=float)
        lp.a_matrix_.start_=A.indptr.astype(np.int32)
        lp.a_matrix_.index_=A.indices.astype(np.int32)
        lp.a_matrix_.value_=A.data.astype(float)
        lp.integrality_=[_h.HighsVarType.kInteger]*n

        # SciPy may have initialized HiGHS' global scheduler earlier with a
        # different thread count. Reset it before enforcing single-thread mode.
        _h._Highs.resetGlobalScheduler(True)
        H=_h._Highs()
        H.setOptionValue("output_flag",False)
        H.setOptionValue("threads",1)
        H.setOptionValue("mip_rel_gap",0.0)
        H.setOptionValue("mip_abs_gap",0.0)
        H.passModel(lp)
        self.H=H
        self._idx=np.arange(n,dtype=np.int32)
        self.last_x=None

    def set_objective_bounds(self,upper:Optional[Sequence[Optional[float]]]=None):
        if upper is None: upper=[None]*self.P.p
        for j,v in enumerate(upper):
            ub=np.inf if v is None else float(v)
            self.H.changeRowBounds(self.base_rows+j,-np.inf,ub)

    def solve(self,c,upper=None):
        from time import perf_counter
        _h=self._hmod
        self.set_objective_bounds(upper)
        vals=np.asarray(c,dtype=float)
        self.H.changeColsCost(self.P.n,self._idx,vals)
        # The previous incumbent/basis is retained by HiGHS across model modifications.
        t0=perf_counter(); status=self.H.run(); dt=perf_counter()-t0
        model_status=self.H.getModelStatus(); info=self.H.getInfo()
        nodes=int(getattr(info,"mip_node_count",0) or 0)
        if model_status==_h.HighsModelStatus.kInfeasible:
            return None,nodes,dt,model_status
        if model_status!=_h.HighsModelStatus.kOptimal:
            return None,nodes,dt,model_status
        sol=self.H.getSolution(); x=np.rint(np.asarray(sol.col_value,float)).astype(int)
        self.last_x=x
        return x,nodes,dt,model_status

