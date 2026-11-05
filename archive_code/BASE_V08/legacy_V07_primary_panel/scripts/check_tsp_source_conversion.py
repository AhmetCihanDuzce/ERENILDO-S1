#!/usr/bin/env python3
"""Reparse all 15 supplied source LPs; compare costs to frozen DFJ inputs. No solve."""
from pathlib import Path
import csv,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/frozen/independent'))
from source_parser import parse_lp
def main():
 b={r['instance']:r for r in csv.DictReader((ROOT/'metadata/BENCHMARK_MANIFEST_85.csv').open())}
 rows=list(csv.DictReader((ROOT/'metadata/TSP_NATIVE_LP_MANIFEST.csv').open()))
 for r in rows:
  spec=json.loads((ROOT/b[r['instance']]['input_path']).read_text())
  parsed=parse_lp((ROOT/r['path']).read_bytes(),Path(r['path']).name)
  if parsed['costs']!=spec['costs'] or parsed['p']!=spec['p'] or parsed['n']!=spec['n'] or parsed['input_sha256']!=spec['source_lp_sha256']:raise ValueError('Conversion mismatch '+r['instance'])
  if spec['formulation']!='dfj_dense' or not parsed['symmetric']:raise ValueError('Unexpected model metadata')
 print(json.dumps(dict(status='PASS',native_LP_files_reparsed=15,exact_integer_cost_matrix_matches=15,solver_formulation='dfj_dense',symmetric_source_costs=True,new_solver_runs=0),indent=2))
if __name__=='__main__':main()
