#!/usr/bin/env python3
"""V05 software validation; validation outputs are excluded from primary timing analysis.

Runs status-contract tests by default. --smoke additionally executes eight small
end-to-end cells and two injected worker-failure checks. It never updates the
historical 510-terminal panel, the expected analysis, or archived references.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit('Validation output must be absent or empty.')
    out.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location('status_regression', ROOT / 'tests/test_solver_status.py')
    tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tests)
    with (out / 'UNIT_TESTS.log').open('w') as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromModule(tests))
    if not result.wasSuccessful():
        raise RuntimeError('Status contract tests failed; see UNIT_TESTS.log.')
    report = dict(
        status='PASS', unit_test_methods=result.testsRun,
        status_contract_cases=len(tests.EXERCISED_CASES),
        exercised_cases=tests.EXERCISED_CASES,
        python=platform.python_version(),
        small_validation_cells=[], injected_worker_failures=[],
        primary_performance_experiments_added=0, historical_terminals_modified=0,
        reference_fronts_regenerated=0,
        source_hashes={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in sorted((ROOT / 'src/validated/common').glob('*.py'))},
    )
    import numpy, scipy
    report.update(numpy=numpy.__version__, scipy=scipy.__version__)
    manifest = list(csv.DictReader((ROOT / 'metadata/EXPERIMENT_MANIFEST_510.csv').open()))
    env = os.environ.copy()
    for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
                 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS']:
        env[name] = '1'

    def stage(instance, workers, method, work):
        cmd = [sys.executable, str(ROOT / 'scripts/prepare_validated_run.py'),
               '--instance', instance, '--workers', str(workers), '--method', method,
               '--out', str(work), '--label', 'V05_SOFTWARE_VALIDATION_ONLY', '--stage-only']
        p = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
        if p.returncode:
            raise RuntimeError('Staging failed: ' + p.stdout + p.stderr)
        plan = json.loads((work / 'REPRODUCTION_PLAN.json').read_text())
        return plan

    def execute(plan, work):
        p = subprocess.run(plan['command'], cwd=work, env=env,
                           capture_output=True, text=True, timeout=90)
        (work / 'EXECUTION.log').write_text(p.stdout + p.stderr)
        terminal = json.loads((work / 'result.json').read_text())
        return p.returncode, terminal

    if args.smoke:
        if sys.platform != 'linux' or len(os.sched_getaffinity(0)) < 3:
            raise RuntimeError('Smoke validation requires Linux and at least three allowed CPUs.')
        cases = [('AP_p-3_n-5_ins-1', 1), ('KP_p-5_n-10_ins-1', 1),
                 ('TSP4-06-1', 1), ('TSP4-06-1', 2)]
        for instance, workers in cases:
            for method in ['standard', 'block2']:
                work = out / 'small_cells' / f'{instance}__w{workers}__{method}'
                plan = stage(instance, workers, method, work)
                rc, d = execute(plan, work)
                archived = next(r for r in manifest if
                                (r['instance'], int(r['workers']), r['method']) ==
                                (instance, workers, method))
                old = json.loads((ROOT / archived['terminal_path']).read_text())
                reference = json.loads((ROOT / archived['oracle_path']).read_text())
                points = reference.get('pareto_points', reference.get('objective_vectors'))
                check = lambda x: {tuple(v) for v in x}
                assert rc == 0 and d['status'] == 'EXACT_QA_PASS', (instance, method, d)
                assert check(d['observed_pareto_vectors']) == check(points)
                assert d['in_flight_or_queued_at_exit'] == 0
                for name in ['feasible', 'infeasible', 'scalarizations', 'milp_calls']:
                    assert d['counters'][name] == old['counters'][name], (instance, method, name)
                report['small_validation_cells'].append(dict(
                    instance=instance, workers=workers, method=method,
                    status='PASS', full_reference_match=True,
                    counters_match_archived=True,
                    pareto_size=len(check(points)),
                    milp_calls=d['counters']['milp_calls'],
                    output=str(work.relative_to(out)),
                    timing_admitted_to_primary_analysis=False,
                ))
        # Inject an unresolved status at the oracle boundary inside a real worker.
        # The controller must receive ERROR, never a successful infeasibility DONE.
        for method in ['standard', 'block2']:
            work = out / 'injected_failures' / method
            plan = stage('TSP4-06-1', 1, method, work)
            bridge = work / 'code/sota_python_common.py'
            bridge.write_text(bridge.read_text() + '\n'
                'def _validation_injected_unresolved(self,c,upper=None):\n'
                '    return None,0,0.0,self._hmod.HighsModelStatus.kTimeLimit\n'
                'PersistentHighsMOIP.solve=_validation_injected_unresolved\n')
            (work / 'FAULT_INJECTION.json').write_text(json.dumps(dict(
                validation_only=True, injected_model_status='kTimeLimit',
                injection_sha256=hashlib.sha256(bridge.read_bytes()).hexdigest(),
                actual_optimization_calls=0), indent=2) + '\n')
            rc, d = execute(plan, work)
            assert rc != 0 and d['status'] == 'FAILED_WORKER', d
            assert d['exact_reference_match'] is False
            assert d['counters']['infeasible'] == 0
            assert d['counters']['scalarizations'] == 0
            assert 'SolverUnresolvedError' in json.dumps(d['error'])
            report['injected_worker_failures'].append(dict(
                method=method, status='PASS', terminal_status=d['status'],
                unresolved_not_counted_as_infeasible=True,
                exact_acceptance_rejected=True, actual_optimization_calls=0))
    report['small_end_to_end_validation_runs'] = len(report['small_validation_cells'])
    report['worker_failure_injection_runs'] = len(report['injected_worker_failures'])
    report['scope'] = ('Status-contract software validation and limited small-instance regressions. '
                       'No new performance observations were admitted to the 85-instance panel; '
                       'historical per-MILP statuses cannot be reconstructed from aggregate terminals.')
    (out / 'SOFTWARE_VALIDATION_QA.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in
                      ['exercised_cases', 'source_hashes', 'small_validation_cells']}, indent=2))


if __name__ == '__main__':
    main()
