"""
Pruebas Unitarias Automatizadas bajo formato Arrange-Act-Assert (AAA).
Cubre casos básicos, límites, adversos y de escala para colas y Dijkstra.
Cumple con la Instrucción 8 y Rúbrica de la Guía Docente (Algoritmos Avanzados - UNSAAC).
Grupo 5
"""
import unittest
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models.cusco_network import get_cusco_adjacency, ROAD_SEGMENTS
from src.datastructures.indexed_min_heap import IndexedMinHeap
from src.datastructures.d_ary_heap import DAryHeap
from src.datastructures.fibonacci_heap import FibonacciHeap
from src.algorithms.dijkstra import dijkstra_solver
from src.utils.cost_model import CuscoCostModel, RoadSegment


class TestBasicCases(unittest.TestCase):
    """Casos Básicos de verificación funcional de montículos y Dijkstra."""

    def test_indexed_min_heap_operations(self):
        # Arrange
        heap = IndexedMinHeap()
        
        # Act
        heap.insert("B", 180.0)
        heap.insert("C", 450.0)
        heap.insert("D", 400.0)
        heap.decrease_key("C", 150.0)
        min_dist, min_node = heap.extract_min()

        # Assert
        self.assertEqual(min_node, "C")
        self.assertEqual(min_dist, 150.0)
        self.assertEqual(len(heap), 2)

    def test_d_ary_heap_operations(self):
        # Arrange
        heap = DAryHeap(d=4)

        # Act
        heap.insert("A", 10.0)
        heap.insert("B", 50.0)
        heap.insert("C", 30.0)
        heap.insert("D", 5.0)
        heap.decrease_key("B", 2.0)
        min_dist, min_node = heap.extract_min()

        # Assert
        self.assertEqual(min_node, "B")
        self.assertEqual(min_dist, 2.0)

    def test_fibonacci_heap_operations(self):
        # Arrange
        heap = FibonacciHeap()

        # Act
        heap.insert("X", 100.0)
        heap.insert("Y", 20.0)
        heap.insert("Z", 80.0)
        heap.decrease_key("X", 10.0)
        min_dist, min_node = heap.extract_min()

        # Assert
        self.assertEqual(min_node, "X")
        self.assertEqual(min_dist, 10.0)

    def test_dijkstra_cusco_exact_distances(self):
        # Arrange
        nodes, adj = get_cusco_adjacency(metric="distance")
        source = "A"
        expected = {
            "A": 0.0,
            "B": 180.0,
            "C": 450.0,
            "D": 400.0,
            "E": 650.0,
            "F": 800.0
        }

        # Act
        res_bin = dijkstra_solver(nodes, adj, source=source, queue_type="binary_heap")
        res_4ary = dijkstra_solver(nodes, adj, source=source, queue_type="4ary_heap")
        res_fib = dijkstra_solver(nodes, adj, source=source, queue_type="fibonacci_heap")

        # Assert
        self.assertEqual(res_bin["distances"], expected)
        self.assertEqual(res_4ary["distances"], expected)
        self.assertEqual(res_fib["distances"], expected)
        self.assertEqual(res_bin["paths"]["F"], ["A", "C", "F"])
        self.assertEqual(res_bin["paths"]["E"], ["A", "B", "D", "E"])


class TestBoundaryCases(unittest.TestCase):
    """Casos Límite: grafos triviales, nodos disconexos y vaciado de colas."""

    def test_single_node_graph(self):
        # Arrange
        nodes = ["A"]
        adj = {"A": []}
        source = "A"

        # Act
        res = dijkstra_solver(nodes, adj, source=source, queue_type="binary_heap")

        # Assert
        self.assertEqual(res["distances"]["A"], 0.0)
        self.assertEqual(res["paths"]["A"], ["A"])

    def test_disconnected_graph_unreachable_node(self):
        # Arrange
        nodes = ["A", "B", "C_ISOLATED"]
        adj = {
            "A": [("B", 10.0)],
            "B": [],
            "C_ISOLATED": []
        }
        source = "A"

        # Act
        res = dijkstra_solver(nodes, adj, source=source, queue_type="binary_heap")

        # Assert
        self.assertEqual(res["distances"]["A"], 0.0)
        self.assertEqual(res["distances"]["B"], 10.0)
        self.assertEqual(res["distances"]["C_ISOLATED"], float("inf"))
        self.assertEqual(res["paths"]["C_ISOLATED"], [])

    def test_heap_empty_extraction(self):
        # Arrange
        heap = IndexedMinHeap()

        # Act & Assert
        self.assertTrue(heap.is_empty())
        with self.assertRaises(IndexError):
            heap.extract_min()

    def test_decrease_key_with_greater_value_ignored(self):
        # Arrange
        heap = IndexedMinHeap()
        heap.insert("A", 50.0)

        # Act (attempt to increase key)
        heap.decrease_key("A", 100.0)
        d, n = heap.extract_min()

        # Assert (original key remains unchanged)
        self.assertEqual(d, 50.0)
        self.assertEqual(n, "A")


class TestAdverseCases(unittest.TestCase):
    """Casos Adversos: pendientes negativas, aristas de coste cero y topografías extremas."""

    def test_downhill_negative_slope_capping(self):
        # Arrange: Calle de bajada (-15% pendiente)
        seg_down = RoadSegment("X", "Y", 100.0, "calle_centro", -15.0, "Bajada Santa Ana")
        seg_flat = RoadSegment("X", "Z", 100.0, "calle_centro", 0.0, "Calle Plana")

        # Act: Impedancia no debe volverse negativa ni menor a la velocidad libre base
        cost_down = CuscoCostModel.calculate_cost(seg_down, metric="time")
        cost_flat = CuscoCostModel.calculate_cost(seg_flat, metric="time")

        # Assert
        self.assertEqual(cost_down, cost_flat)
        self.assertEqual(cost_down, 24.0)

    def test_zero_weight_edges(self):
        # Arrange: Grafo con aristas de peso 0 (paso peatonal inmediato)
        nodes = ["U", "V", "W"]
        adj = {
            "U": [("V", 0.0)],
            "V": [("W", 5.0)],
            "W": []
        }
        source = "U"

        # Act
        res = dijkstra_solver(nodes, adj, source=source, queue_type="binary_heap")

        # Assert
        self.assertEqual(res["distances"]["V"], 0.0)
        self.assertEqual(res["distances"]["W"], 5.0)
        self.assertEqual(res["paths"]["W"], ["U", "V", "W"])


class TestScaleAndEquivalence(unittest.TestCase):
    """Caso de Escala y Equivalencia Cruzada entre las tres Colas de Prioridad."""

    def test_cross_validation_random_synthetic_graph(self):
        # Arrange: Grafo aleatorio de 50 nodos y 200 aristas con semilla fija
        random.seed(42)
        n = 50
        nodes = [f"V_{i}" for i in range(n)]
        adj = {v: [] for v in nodes}
        for _ in range(200):
            u = random.choice(nodes)
            v = random.choice(nodes)
            if u != v:
                w = round(random.uniform(5.0, 50.0), 2)
                adj[u].append((v, w))
        source = "V_0"

        # Act
        res_bin = dijkstra_solver(nodes, adj, source=source, queue_type="binary_heap")
        res_4ary = dijkstra_solver(nodes, adj, source=source, queue_type="4ary_heap")
        res_fib = dijkstra_solver(nodes, adj, source=source, queue_type="fibonacci_heap")

        # Assert: Las distancias calculadas por las 3 estructuras deben ser exactamente idénticas
        for v in nodes:
            d_bin = res_bin["distances"][v]
            d_4ary = res_4ary["distances"][v]
            d_fib = res_fib["distances"][v]
            self.assertAlmostEqual(d_bin, d_4ary, places=5)
            self.assertAlmostEqual(d_bin, d_fib, places=5)


if __name__ == "__main__":
    unittest.main()
