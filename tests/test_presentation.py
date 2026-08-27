import io
import unittest

import pandas as pd

from charts import costs_figure, function_figure
from methods import COLUMNS, bisection, false_position
from presentation import cost_comparison, csv_bytes, display_iterations
from problems import CLOUD, NETWORK, cloud_cost, local_cost


class PresentationTests(unittest.TestCase):
    def test_formatting_does_not_modify_calculations(self):
        result, frame = false_position(CLOUD.function, 3, 4)
        original = frame.copy(deep=True)
        for decimals in (4, 6, 8, 10):
            shown = display_iterations(frame, decimals)
            self.assertEqual(shown.iloc[0]["Error aproximado (%)"], "—")
            self.assertEqual(list(shown.columns), COLUMNS)
        pd.testing.assert_frame_equal(frame, original)
        self.assertEqual(result.root, frame.iloc[-1]["xr"])

    def test_csv_contains_complete_unrounded_rows(self):
        _, frame = false_position(CLOUD.function, 3, 4)
        exported = pd.read_csv(io.BytesIO(csv_bytes(frame)), float_precision="round_trip")
        self.assertEqual(list(exported.columns), COLUMNS)
        self.assertEqual(len(exported), len(frame))
        self.assertTrue(pd.isna(exported.iloc[0]["Error aproximado (%)"]))
        self.assertEqual(exported.iloc[0]["xr"], frame.iloc[0]["xr"])

    def test_graphs_match_every_sample_and_root(self):
        for problem, solver in ((NETWORK, bisection), (CLOUD, false_position)):
            result, _ = solver(problem.function, *problem.default_interval)
            figure = function_figure(problem, problem.default_interval, result)
            curve = figure.data[0]
            for x, y in zip(curve.x, curve.y):
                self.assertEqual(y, problem.function(x))
            marker = figure.data[-1]
            self.assertEqual(marker.x[0], result.root)
            self.assertEqual(marker.y[0], result.residual)
            self.assertTrue(any(shape.y0 == 0 and shape.y1 == 0 for shape in figure.layout.shapes))
        figure = costs_figure((3, 4), result)
        for trace, func in zip(figure.data[:2], (local_cost, cloud_cost)):
            for x, y in zip(trace.x, trace.y):
                self.assertEqual(y, func(x))
        self.assertEqual(figure.data[2].y[0], local_cost(result.root))
        self.assertEqual(figure.data[3].y[0], cloud_cost(result.root))

    def test_interpretation_uses_actual_costs(self):
        result, _ = false_position(CLOUD.function, 3, 4)
        frame, _ = cost_comparison(result.root)
        self.assertEqual(frame.iloc[0]["Alternativa de menor costo"], "Cloud")
        self.assertEqual(frame.iloc[2]["Alternativa de menor costo"], "Local")
        for _, row in frame.iterrows():
            self.assertEqual(row["Costo local"], local_cost(row["t (años)"]))
            self.assertEqual(row["Costo cloud"], cloud_cost(row["t (años)"]))


if __name__ == "__main__":
    unittest.main()
