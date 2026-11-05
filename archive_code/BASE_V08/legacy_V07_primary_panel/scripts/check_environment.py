#!/usr/bin/env python3
"""Import/API preflight only: no optimizer model or solver execution."""
import sys,platform,json,importlib.metadata,os
def main():
 from scipy.optimize._highspy import _core
 import numpy,pandas
 result=dict(python=platform.python_version(),numpy=numpy.__version__,scipy=importlib.metadata.version('scipy'),pandas=pandas.__version__,private_highs_binding=hasattr(_core,'_Highs'),linux_cpu_affinity=hasattr(os,'sched_getaffinity'),allowed_CPUs=len(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None,new_solver_runs=0)
 print(json.dumps(result,indent=2))
 if result['numpy']!='2.3.5' or result['scipy']!='1.17.0' or not result['private_highs_binding']:raise SystemExit(1)
if __name__=='__main__':main()
