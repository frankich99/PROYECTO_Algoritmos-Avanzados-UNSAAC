"""Corrección de A* y de su heurística escalada por la instancia."""
import math

import pytest

from src.algorithms.a_star import (
    a_star_solver,
    make_consistent_heuristic,
    validate_heuristic_consistency,
)
from src.algorithms.dijkstra import dijkstra_solver
from src.io.graph_io import InvalidInstanceError
from src.models.cusco_network import load_cusco_instance
from tests.conftest import QUEUES


@pytest.mark.parametrize("queue", QUEUES)
def test_astar_matches_dijkstra_on_manual_cusco(queue):
    inst = load_cusco_instance("time")
    expected = dijkstra_solver(inst.nodes, inst.adj, "A", queue_type=queue, target="F")
    actual = a_star_solver(inst.nodes, inst.adj, "A", "F", inst.coords, queue_type=queue)
    assert actual["target_distance"] == pytest.approx(expected["distances"]["F"])
    assert actual["path"] == expected["paths"]["F"]


def test_regression_non_admissible_default_coordinates_counterexample():
    nodes = list("AECF")
    adj = {
        "A": [("E", 1.0), ("C", 1.0)],
        "E": [("F", 1.0)],
        "C": [("F", 50.0)],
        "F": [],
    }
    coords = {
        "A": (0.0, 0.0),
        "E": (-480.0, -320.0),
        "C": (180.0, -250.0),
        "F": (350.0, -420.0),
    }
    result = a_star_solver(nodes, adj, "A", "F", coords)
    assert result["target_distance"] == pytest.approx(2.0)
    assert result["path"] == ["A", "E", "F"]


def test_missing_coordinates_falls_back_to_zero_heuristic():
    nodes = ["A", "B", "C"]
    adj = {"A": [("B", 1.0), ("C", 5.0)], "B": [("C", 1.0)], "C": []}
    result = a_star_solver(nodes, adj, "A", "C", coords={"A": (0.0, 0.0)})
    assert result["heuristic"] == "zero"
    assert result["target_distance"] == pytest.approx(2.0)


def test_scaled_heuristic_is_consistent():
    inst = load_cusco_instance("distance")
    heuristic, scale = make_consistent_heuristic(inst.nodes, inst.adj, inst.coords, "F")
    assert scale > 0
    validate_heuristic_consistency(inst.nodes, inst.adj, "F", heuristic)
    assert heuristic("F") == 0.0


def test_inconsistent_custom_heuristic_is_rejected():
    nodes = ["A", "B"]
    adj = {"A": [("B", 1.0)], "B": []}
    with pytest.raises(InvalidInstanceError, match="inconsistente"):
        a_star_solver(nodes, adj, "A", "B", custom_heuristic=lambda n: 10.0 if n == "A" else 0.0)


def test_point_to_point_dijkstra_keeps_optimal_cost():
    inst = load_cusco_instance("distance")
    full = dijkstra_solver(inst.nodes, inst.adj, "A")
    targeted = dijkstra_solver(inst.nodes, inst.adj, "A", target="E")
    assert targeted["distances"]["E"] == full["distances"]["E"]
    assert targeted["stats"]["visited_count"] <= full["stats"]["visited_count"]
    assert math.isfinite(targeted["distances"]["E"])
