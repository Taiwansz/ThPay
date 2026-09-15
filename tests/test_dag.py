import unittest
from decimal import Decimal
from thpay.engine.dag import PayrollDAG, CyclicDependencyError

class TestPayrollDAG(unittest.TestCase):
    def test_topological_execution_order(self):
        dag = PayrollDAG()
        dag.add_node("c", lambda s: s["b"] * 2, depends_on=["b"])
        dag.add_node("a", lambda s: Decimal("10.00"))
        dag.add_node("b", lambda s: s["a"] + 5, depends_on=["a"])

        order = dag.get_evaluation_order()
        self.assertEqual(order, ["a", "b", "c"])

        state = dag.execute()
        self.assertEqual(state["a"], Decimal("10.00"))
        self.assertEqual(state["b"], Decimal("15.00"))
        self.assertEqual(state["c"], Decimal("30.00"))

    def test_cycle_detection(self):
        dag = PayrollDAG()
        dag.add_node("node1", lambda s: s["node2"], depends_on=["node2"])
        dag.add_node("node2", lambda s: s["node1"], depends_on=["node1"])

        with self.assertRaises(CyclicDependencyError):
            dag.get_evaluation_order()

if __name__ == "__main__":
    unittest.main()
