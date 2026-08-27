import math
import unittest

import pandas as pd

from methods import COLUMNS, NumericalError, approximate_error, bisection, false_position, validate_interval
from problems import cloud_cost, cloud_equilibrium_function, cloud_exploration, local_cost, network_function


class MethodsTests(unittest.TestCase):
    cases = ((bisection, network_function, (9, 10)),
             (false_position, cloud_equilibrium_function, (3, 4)))

    def test_default_convergence(self):
        for solver, func, interval in self.cases:
            with self.subTest(method=solver.__name__):
                result, frame = solver(func, *interval)
                self.assertTrue(result.converged)
                self.assertLessEqual(result.error, 0.5)
                self.assertLess(abs(func(result.root)), 0.02)
                self.assertEqual(result.residual, func(result.root))
                self.assertEqual(result.iterations, len(frame))
                self.assertLess(validate_interval(func, *interval).product, 0)
        self.assertEqual(bisection(network_function, 9, 10)[0].root, 9.90625)
        self.assertAlmostEqual(false_position(cloud_equilibrium_function, 3, 4)[0].root, 3.7650110928903193)

    def test_all_rows_match_formula_and_unmodified_endpoints(self):
        for solver, func, interval in self.cases:
            result, frame = solver(func, *interval, tolerance=1e-8)
            self.assertEqual(list(frame.columns), COLUMNS)
            self.assertTrue(pd.isna(frame.iloc[0]["Error aproximado (%)"]))
            previous = None
            for i, row in frame.iterrows():
                a, b, xr, fa, fb = [row[k] for k in ("a", "b", "xr", "f(a)", "f(b)")]
                self.assertEqual(fa, func(a))
                self.assertEqual(fb, func(b))
                self.assertEqual(row["f(xr)"], func(xr))
                self.assertEqual(row["f(a)·f(xr)"], fa * func(xr))
                expected = (a + b) / 2 if solver is bisection else b - fb * (a - b) / (fa - fb)
                self.assertAlmostEqual(xr, expected, places=14)
                self.assertLess(fa * fb, 0)
                self.assertLessEqual(a, xr)
                self.assertLessEqual(xr, b)
                if previous is not None:
                    self.assertEqual(row["Error aproximado (%)"], abs((xr - previous) / xr) * 100)
                next_a, next_b = row["Nuevo intervalo"]
                self.assertLessEqual(func(next_a) * func(next_b), 0)
                if i + 1 < len(frame):
                    self.assertEqual((frame.iloc[i + 1]["a"], frame.iloc[i + 1]["b"]), (next_a, next_b))
                previous = xr
            self.assertLess(abs(result.residual), 1e-7)

    def test_iteration_limit_is_not_success(self):
        for solver, func, interval in self.cases:
            result, frame = solver(func, *interval, max_iterations=1)
            self.assertFalse(result.converged)
            self.assertEqual(result.reason, "max_iterations")
            self.assertEqual(len(frame), 1)
            self.assertIsNone(result.error)

    def test_exact_zero_and_relative_zero_denominator(self):
        for solver in (bisection, false_position):
            result, frame = solver(lambda x: x, -1, 1)
            self.assertTrue(result.converged)
            self.assertEqual(result.root, 0)
            self.assertIsNone(result.error)
            self.assertEqual(frame.iloc[0]["Nuevo intervalo"], (0, 0))
        result, frame = bisection(lambda x: x - 0.2, -1, 1)
        self.assertEqual(frame.iloc[0]["xr"], 0)
        self.assertTrue(result.converged)
        self.assertIsNone(approximate_error(0, 1))

    def test_invalid_intervals_and_settings(self):
        for solver in (bisection, false_position):
            for a, b in ((2, 1), (1, 1), (math.nan, 2), (1, math.inf), (2, 3), (0, 2)):
                with self.subTest(solver=solver.__name__, interval=(a, b)):
                    with self.assertRaises(NumericalError):
                        solver(lambda x: x, a, b)
            for tol in (0, -1, math.inf, math.nan):
                with self.assertRaises(NumericalError):
                    solver(lambda x: x, -1, 1, tolerance=tol)
            for maximum in (0, -1, 1.5, True):
                with self.assertRaises(NumericalError):
                    solver(lambda x: x, -1, 1, max_iterations=maximum)

    def test_invalid_function_values(self):
        for solver in (bisection, false_position):
            for func in (lambda x: math.nan, lambda x: math.inf, lambda x: 1 / 0):
                with self.assertRaises(NumericalError):
                    solver(func, -1, 1)
            with self.assertRaises(NumericalError):
                solver(network_function, 8.5, 10)
            with self.assertRaises(NumericalError):
                solver(cloud_equilibrium_function, 3, 1e6)

    def test_model_domains_and_overflow(self):
        for C in (8.5, 2, -1, math.inf, math.nan):
            with self.assertRaises(ValueError):
                network_function(C)
        for func in (local_cost, cloud_cost):
            for t in (-1, math.nan, math.inf, 1e308):
                with self.assertRaises(ValueError):
                    func(t)

    def test_roundoff_stagnation_is_not_convergence(self):
        a, b = 1.0, math.nextafter(1.0, 2.0)
        result, _ = bisection(lambda x: -1 if x == a else 1, a, b)
        self.assertFalse(result.converged)
        self.assertEqual(result.reason, "stagnation")

    def test_cost_exploration_and_equality(self):
        rows = cloud_exploration()
        self.assertEqual([r["t"] for r in rows], list(range(6)))
        self.assertGreater(rows[3]["f(t)"], 0)
        self.assertLess(rows[4]["f(t)"], 0)
        result, _ = false_position(cloud_equilibrium_function, 3, 4, tolerance=1e-9)
        self.assertAlmostEqual(local_cost(result.root), cloud_cost(result.root), places=7)
        self.assertGreater(cloud_equilibrium_function(result.root - 0.1), 0)
        self.assertLess(cloud_equilibrium_function(result.root + 0.1), 0)


if __name__ == "__main__":
    unittest.main()
