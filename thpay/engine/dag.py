from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Callable, Dict, List, Set

class CyclicDependencyError(Exception):
    """Lancado quando um ciclo de dependencia e detectado no grafo de calculo."""
    pass

@dataclass
class CalculationNode:
    name: str
    func: Callable[[Dict[str, Any]], Any]
    depends_on: List[str] = field(default_factory=list)

class PayrollDAG:
    """
    Motor de Grafo Aciclico Dirigido (DAG) para resolucao deterministica
    de dependencias em calculos de folha de pagamento.
    """
    def __init__(self):
        self.nodes: Dict[str, CalculationNode] = {}

    def add_node(self, name: str, func: Callable[[Dict[str, Any]], Any], depends_on: List[str] = None):
        if depends_on is None:
            depends_on = []
        self.nodes[name] = CalculationNode(name=name, func=func, depends_on=depends_on)

    def get_evaluation_order(self) -> List[str]:
        """
        Ordenacao Topologica via Algoritmo de Kahn com deteccao estatica de ciclos.
        """
        in_degree: Dict[str, int] = {node_name: 0 for node_name in self.nodes}
        graph: Dict[str, List[str]] = {node_name: [] for node_name in self.nodes}

        for node_name, node in self.nodes.items():
            for dep in node.depends_on:
                if dep not in self.nodes:
                    raise KeyError(f"Dependencia '{dep}' exigida pelo no '{node_name}' nao esta cadastrada no DAG.")
                graph[dep].append(node_name)
                in_degree[node_name] += 1

        queue = [name for name, deg in in_degree.items() if deg == 0]
        order = []

        while queue:
            current = queue.pop(0)
            order.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(self.nodes):
            unresolved = [name for name, deg in in_degree.items() if deg > 0]
            raise CyclicDependencyError(f"Ciclo de dependencia detectado nos seguintes nos: {unresolved}")

        return order

    def execute(self, initial_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executa todos os nos na ordem topologica estrita.
        """
        state: Dict[str, Any] = {}
        if initial_state:
            state.update(initial_state)

        evaluation_order = self.get_evaluation_order()
        for node_name in evaluation_order:
            node = self.nodes[node_name]
            result = node.func(state)
            state[node_name] = result

        return state
