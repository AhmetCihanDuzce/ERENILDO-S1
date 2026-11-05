#!/usr/bin/env python3
"""Recompute V04 tables and optionally Figure 1, without solving any instance."""
from pathlib import Path
import argparse,json,shutil,subprocess,sys,hashlib
ROOT=Path(__file__).resolve().parents[1]
TABLES=['ALL_255_PAIRS.csv','ALL_510_TERMINAL_OBSERVATIONS.csv','CALL_SUMMARY.csv','TIMING_STRATIFIED.csv','ABSOLUTE_TIMES_STRATIFIED.csv','BENCHMARK_CLUSTER_SUMMARY.csv','SCALING_DESCRIPTIVE.csv','TSP_N10_ORDER_SENSITIVITY.csv','ANALYSIS_QA.json']
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--out',required=True,type=Path);a.add_argument('--figures',action='store_true');v=a.parse_args();out=v.out.resolve()
 if out.exists() and any(out.iterdir()):raise SystemExit('Output directory must be absent or empty.')
 out.mkdir(parents=True,exist_ok=True)
 for p in (ROOT/'data/analysis_inputs').glob('*.csv'):shutil.copyfile(p,out/p.name)
 for name in ['analyze.py','plot_results.py']:shutil.copyfile(ROOT/'src/analysis'/name,out/name)
 result=subprocess.run([sys.executable,str(out/'analyze.py')],cwd=out,text=True,capture_output=True)
 (out/'ANALYSIS_EXECUTION.log').write_text(result.stdout+result.stderr)
 if result.returncode:raise SystemExit('Analysis failed; see ANALYSIS_EXECUTION.log')
 checks={name:(out/name).read_bytes()==(ROOT/'expected'/name).read_bytes() for name in TABLES}
 if v.figures:
  fig=subprocess.run([sys.executable,str(out/'plot_results.py')],cwd=out,text=True,capture_output=True)
  (out/'FIGURE_EXECUTION.log').write_text(fig.stdout+fig.stderr)
  if fig.returncode:raise SystemExit('Figure failed; see FIGURE_EXECUTION.log')
  for name in ['Figure_1_Time_Ratios.png','Figure_1_Time_Ratios.pdf']:
   if not (out/name).is_file():raise SystemExit('Missing figure '+name)
 report=dict(status='PASS' if all(checks.values()) else 'FAIL',byte_identical_tables_and_analysis_QA=checks,bootstrap_seed=20261016,resamples=50000,new_solver_runs=0,figures_generated=v.figures,figure_note='Numeric source table is compared exactly; image/PDF byte identity is not required because renderer metadata may differ.')
 (out/'REPRODUCTION_CHECK.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
 if not all(checks.values()):raise SystemExit(1)
if __name__=='__main__':main()
