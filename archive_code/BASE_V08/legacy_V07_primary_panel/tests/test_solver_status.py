"""Focused status-contract regression tests; no optimization is performed."""
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

import numpy as np
from scipy.optimize._highspy import _core as highs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/validated/common'))
from pea_highs import PersistentHighsMOIP, SolverUnresolvedError
import generalized_pea_blocklex as pea

EXERCISED_CASES = []


def mocked_backend(model_status, run_status=highs.HighsStatus.kOk):
    solver = PersistentHighsMOIP.__new__(PersistentHighsMOIP)
    solver._hmod = highs
    solver.P = SimpleNamespace(n=1)
    solver._idx = np.array([0], dtype=np.int32)
    solver.last_x = np.array([9])
    solver.set_objective_bounds = lambda upper: None
    solver.H = SimpleNamespace(
        changeColsCost=lambda *args: None,
        run=lambda: run_status,
        getModelStatus=lambda: model_status,
        getInfo=lambda: SimpleNamespace(mip_node_count=4),
        getSolution=lambda: SimpleNamespace(col_value=[1.0]),
    )
    return solver


class ScriptedSolver:
    _hmod = highs

    def __init__(self, statuses):
        self.statuses = iter(statuses)
        self.calls = 0

    def solve(self, c, upper=None):
        self.calls += 1
        status = next(self.statuses)
        x = np.array([1]) if status == highs.HighsModelStatus.kOptimal else None
        return x, 0, 0.0, status


class StatusContractTests(unittest.TestCase):
    def test_optimal_has_solution(self):
        solver = mocked_backend(highs.HighsModelStatus.kOptimal)
        x, nodes, elapsed, status = solver.solve([1])
        self.assertEqual(x.tolist(), [1])
        self.assertEqual(nodes, 4)
        self.assertEqual(status, highs.HighsModelStatus.kOptimal)
        EXERCISED_CASES.append('backend_optimal')

    def test_only_proven_infeasibility_returns_none(self):
        solver = mocked_backend(highs.HighsModelStatus.kInfeasible)
        self.assertIsNone(solver.solve([1])[0])
        self.assertIsNone(solver.last_x)
        EXERCISED_CASES.append('backend_proven_infeasible')

    def test_every_other_model_status_raises(self):
        for name, status in highs.HighsModelStatus.__members__.items():
            if status in (highs.HighsModelStatus.kOptimal, highs.HighsModelStatus.kInfeasible):
                continue
            with self.subTest(status=name):
                solver = mocked_backend(status)
                with self.assertRaises(SolverUnresolvedError) as caught:
                    solver.solve([1])
                self.assertEqual(caught.exception.model_status, str(status))
                self.assertIsNone(solver.last_x)
                EXERCISED_CASES.append('backend_' + name)

    def test_run_warning_or_error_cannot_reuse_a_certificate(self):
        for run in [highs.HighsStatus.kWarning, highs.HighsStatus.kError]:
            for model in [highs.HighsModelStatus.kOptimal, highs.HighsModelStatus.kInfeasible]:
                with self.subTest(run=run, model=model):
                    with self.assertRaises(SolverUnresolvedError):
                        mocked_backend(model, run).solve([1])
                    EXERCISED_CASES.append(f'run_{run}_model_{model}')

    def test_successful_oracle_counts_and_image(self):
        for p in [3, 4, 5]:
            P = SimpleNamespace(p=p, C=-np.arange(1, p + 1).reshape(p, 1))
            for mode in ['standard', 'block2']:
                count = p if mode == 'standard' else p - 1
                solver = ScriptedSolver([highs.HighsModelStatus.kOptimal] * count)
                y, calls, *_ = pea.lexsolve(P, solver, (None,) * (p - 1), mode)
                self.assertEqual(y, tuple(range(-1, -p - 1, -1)))
                self.assertEqual(calls, count)
                self.assertEqual(solver.calls, count)
                EXERCISED_CASES.append(f'optimal_oracle_p{p}_{mode}')

    def test_proven_infeasible_root_costs_one_call(self):
        P = SimpleNamespace(p=3, C=np.ones((3, 1), dtype=int))
        for mode in ['standard', 'block2']:
            solver = ScriptedSolver([highs.HighsModelStatus.kInfeasible])
            y, calls, *_ = pea.lexsolve(P, solver, (None, None), mode)
            self.assertIsNone(y)
            self.assertEqual(calls, 1)
            EXERCISED_CASES.append('root_infeasible_' + mode)

    def test_uncertainty_at_any_stage_is_not_infeasibility(self):
        for p in [3, 4, 5]:
            P = SimpleNamespace(p=p, C=np.ones((p, 1), dtype=int))
            for mode in ['standard', 'block2']:
                count = p if mode == 'standard' else p - 1
                for failed_stage in range(count):
                    for failure in [highs.HighsModelStatus.kTimeLimit,
                                    highs.HighsModelStatus.kUnknown,
                                    highs.HighsModelStatus.kSolveError]:
                        with self.subTest(p=p, mode=mode, stage=failed_stage, status=failure):
                            seq = [highs.HighsModelStatus.kOptimal] * failed_stage + [failure]
                            solver = ScriptedSolver(seq)
                            with self.assertRaises(SolverUnresolvedError):
                                pea.lexsolve(P, solver, (None,) * (p - 1), mode)
                            self.assertEqual(solver.calls, failed_stage + 1)
                            EXERCISED_CASES.append(f'oracle_p{p}_{mode}_stage{failed_stage}_{failure}')

    def test_late_infeasibility_is_an_inconsistent_stage(self):
        for mode in ['standard', 'block2']:
            P = SimpleNamespace(p=3, C=np.ones((3, 1), dtype=int))
            solver = ScriptedSolver([highs.HighsModelStatus.kOptimal,
                                     highs.HighsModelStatus.kInfeasible])
            with self.assertRaises(SolverUnresolvedError):
                pea.lexsolve(P, solver, (None, None), mode)
            EXERCISED_CASES.append('late_infeasible_' + mode)

    def test_missing_optimal_solution_is_rejected(self):
        solver = SimpleNamespace(
            _hmod=highs,
            solve=lambda c, upper=None: (None, 0, 0.0, highs.HighsModelStatus.kOptimal),
        )
        with self.assertRaises(SolverUnresolvedError):
            pea._certified_solve(solver, [1], [None], 0)
        EXERCISED_CASES.append('optimal_without_solution')

    def test_traversal_propagates_failure(self):
        P = SimpleNamespace(p=3, C=np.ones((3, 1), dtype=int))
        for mode in ['standard', 'block2']:
            solver = ScriptedSolver([highs.HighsModelStatus.kTimeLimit])
            with patch.object(pea.dp, 'PersistentHighsMOIP', return_value=solver):
                with self.assertRaises(SolverUnresolvedError):
                    pea.generalized_pea(P, mode)
            EXERCISED_CASES.append('traversal_aborts_' + mode)


if __name__ == '__main__':
    unittest.main()
