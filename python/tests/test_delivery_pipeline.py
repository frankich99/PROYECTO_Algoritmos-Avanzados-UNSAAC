"""Segunda entrega: referencia exhaustiva, semillas, modelo y flujo HTTP sin red."""
import itertools
import math
import random

from fastapi.testclient import TestClient
import pytest

from src.algorithms.a_star import a_star_solver
from src.algorithms.dijkstra import dijkstra_solver
from src.datastructures.registry import available_queues
from src.utils.cost_model import CuscoCostModel, RoadSegment
from web_api import app


def exhaustive_cost(nodes, adj, source, target):
    if source == target:
        return 0.0
    weights = {(u, v): w for u, edges in adj.items() for v, w in edges}
    middle = [node for node in nodes if node not in (source, target)]
    best = math.inf
    for length in range(len(middle) + 1):
        for permutation in itertools.permutations(middle, length):
            path = (source, *permutation, target)
            best = min(best, sum(weights.get(pair, math.inf) for pair in zip(path, path[1:])))
    return best


@pytest.mark.parametrize("seed", [0, 1, 7, 42, 12345])
@pytest.mark.parametrize("queue", available_queues())
def test_small_seeded_graphs_match_exhaustive_reference(seed, queue):
    rng = random.Random(seed)
    nodes = list(range(6))
    adj = {u: [(v, float(rng.randrange(5))) for v in nodes if u != v and rng.random() < 0.3] for u in nodes}
    original = {u: list(edges) for u, edges in adj.items()}
    expected = exhaustive_cost(nodes, adj, 0, 5)
    dijkstra = dijkstra_solver(nodes, adj, 0, queue_type=queue)
    astar = a_star_solver(nodes, adj, 0, 5, queue_type=queue)
    assert dijkstra["distances"][5] == expected
    assert astar["target_distance"] == expected
    assert adj == original


@pytest.mark.parametrize("seed", [0, 42, 12345])
@pytest.mark.parametrize("profile", ["random", "grid", "sparse", "dense"])
def test_http_generate_validate_solve_verify_and_export(seed, profile):
    client = TestClient(app)
    spec = {"kind": "generated", "generator": profile, "seed": seed, "nodes": 9, "rows": 3, "cols": 3}
    first = client.post("/api/v1/instances/validate", json=spec)
    assert first.status_code == 200
    preview = first.json()
    assert preview == client.post("/api/v1/instances/validate", json=spec).json()
    response = client.post("/api/v1/routes/solve", json={
        "instance": spec, "source": preview["ids"][0], "target": preview["ids"][-1], "compare": True,
    })
    assert response.status_code == 200
    result = response.json()
    assert len(result["comparisons"]) == 4
    assert all(row["cost"] == result["result"]["cost"] for row in result["comparisons"])
    assert result["result"]["path"][0] == preview["ids"][0]
    assert result["result"]["path"][-1] == preview["ids"][-1]
    assert sum(edge["cost"] for edge in result["result"]["edges"]) == pytest.approx(result["result"]["cost"])
    assert result["result"]["elapsed_ms_single_run"] >= 0


@pytest.mark.parametrize("field", ["length_m", "gradient_pct", "weather_multiplier", "traffic_multiplier"])
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf"), True, "4"])
def test_cost_model_rejects_nonfinite_or_non_numeric_input(field, bad):
    segment = RoadSegment("A", "B", 100, "avenida", 2, "Ejemplo sintético")
    kwargs = {}
    if field in ("length_m", "gradient_pct"):
        setattr(segment, field, bad)
    else:
        kwargs[field] = bad
    with pytest.raises(ValueError, match="finitos"):
        CuscoCostModel.calculate_cost(segment, **kwargs)


def test_cost_model_known_result_and_uniform_scaling():
    segment = RoadSegment("A", "B", 100, "calle_centro", 10, "Ejemplo sintético")
    assert CuscoCostModel.calculate_cost(segment) == 30
    assert CuscoCostModel.calculate_cost(segment, weather_multiplier=1.2, traffic_multiplier=2) == 72
    assert CuscoCostModel.calculate_cost(segment, metric="distance") == 100
