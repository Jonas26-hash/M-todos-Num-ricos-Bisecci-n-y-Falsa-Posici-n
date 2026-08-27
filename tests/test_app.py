import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from problems import CLOUD, NETWORK

APP = str(Path(__file__).resolve().parents[1] / "app.py")


class AppTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(APP, default_timeout=30).run()
        self.assertFalse(self.app.exception)

    def execute(self):
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)

    def test_initial_state_does_not_execute(self):
        self.assertNotIn("result_network", self.app.session_state)
        self.assertEqual(len(self.app.tabs), 5)
        sidebar_text = "\n".join(element.value for element in
                                 [*self.app.sidebar.caption, *self.app.sidebar.markdown])
        for removed_text in ("Solo cambia la presentación", "Aprender haciendo",
                             "Inspecciona el intervalo, sigue las iteraciones",
                             "Python + Streamlit · Métodos Numéricos"):
            self.assertNotIn(removed_text, sidebar_text)

    def test_both_problems_execute_and_preserve_results(self):
        self.execute()
        network_result = self.app.session_state["result_network"][0]
        self.assertTrue(network_result.converged)
        self.assertEqual(network_result.iterations, 5)
        self.app.selectbox(key="problem_selector").select(CLOUD.navigation).run()
        self.assertNotIn("result_cloud", self.app.session_state)
        self.execute()
        self.assertEqual(self.app.session_state["result_cloud"][0].iterations, 3)
        self.assertFalse(self.app.exception)
        self.app.selectbox(key="problem_selector").select(NETWORK.navigation).run()
        self.assertEqual(self.app.session_state["result_network"][0], network_result)

    def test_changing_decimals_does_not_execute(self):
        self.execute()
        result = self.app.session_state["result_network"][0]
        with patch("methods.bisection", side_effect=AssertionError("No debe recalcular")):
            self.app.select_slider(key="decimals").set_value(10).run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.session_state["result_network"][0], result)

    def test_invalid_attempt_clears_stale_result(self):
        self.execute()
        self.app.number_input(key="a_network").set_value(10)
        self.app.number_input(key="b_network").set_value(11)
        self.execute()
        self.assertNotIn("result_network", self.app.session_state)
        self.assertTrue(any("mismo signo" in item.value for item in self.app.warning))

    def test_domain_validation(self):
        self.app.number_input(key="a_network").set_value(8)
        self.execute()
        self.assertNotIn("result_network", self.app.session_state)
        self.assertTrue(any("C > 8.5" in item.value for item in self.app.warning))

    def test_iteration_limit_has_no_final_recommendation(self):
        self.app.number_input(key="max_network").set_value(1)
        self.execute()
        self.assertFalse(self.app.session_state["result_network"][0].converged)
        self.assertTrue(any("número máximo" in item.value for item in self.app.warning))
        self.assertFalse(any(metric.label == "Capacidad práctica recomendada" for metric in self.app.metric))


if __name__ == "__main__":
    unittest.main()
