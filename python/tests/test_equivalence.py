"""
Equivalencia entre alternativas (Avance 5) y contra implementaciones de referencia.

Propiedad esperada: con pesos no negativos, las tres colas producen
EXACTAMENTE las mismas distancias que Bellman-Ford. Las rutas pueden diferir
solo si existen varios caminos óptimos (empates); en ese caso ambas rutas
deben ser válidas y tener el mismo costo.
"""
import random

import pytest

from src.algorithms.dijkstra import dijkstra_solver
from src.algorithms.reference import bellman_ford, dijkstra_array
from src.generators.instance_generator import grid_network, random_road_network, road_grid_network
from src.io.graph_io import load_instance
from src.verification.certificate import compare_results, path_cost, verify_shortest_paths
from tests.conftest import QUEUES


def _random_graph(n, m, seed, integer=False, zero_prob=0.0):
    rng = random.Random(seed)
    nodes = [f"V{i}" for i in range(n)]
    adj = {v: [] for v in nodes}
    for _ in range(m):
        u, v = rng.choice(nodes), rng.choice(nodes)
        if rng.random() < zero_prob:
            w = 0.0
        else:
            w = float(rng.randint(1, 5)) if integer else round(rng.uniform(0.5, 50.0), 3)
        adj[u].append((v, w))
    return nodes, adj


@pytest.mark.parametrize("seed", range(40))
def test_all_queues_match_bellman_ford_on_random_graphs(seed):
    n = 5 + seed * 3
    nodes, adj = _random_graph(n, n * 4, seed, integer=(seed % 2 == 0), zero_prob=0.1 if seed % 5 == 0 else 0.0)
    src = nodes[0]
    ref = bellman_ford(nodes, adj, src)
    results = {q: dijkstra_solver(nodes, adj, src, queue_type=q) for q in QUEUES}
    results["bellman_ford"] = ref
    cmp = compare_results(adj, nodes, results, reference="bellman_ford")
    assert cmp["distances_equal"], cmp["distance_mismatches"]
    for q, r in results.items():
        assert verify_shortest_paths(nodes, adj, src, r)["ok"], q


def test_matches_unsorted_array_dijkstra():
    inst = random_road_network(300, seed=99)
    arr = dijkstra_array(inst.nodes, inst.adj, inst.nodes[0])
    for q in QUEUES:
        assert dijkstra_solver(inst.nodes, inst.adj, inst.nodes[0], queue_type=q)["distances"] == arr["distances"]


def test_matches_networkx_if_available():
    nx = pytest.importorskip("networkx")
    inst = road_grid_network(8, 8, seed=3)
    g = nx.DiGraph()
    g.add_nodes_from(inst.nodes)
    for u in inst.nodes:
        for v, w in inst.adj[u]:
            g.add_edge(u, v, weight=w)
    expected = nx.single_source_dijkstra_path_length(g, inst.nodes[0])
    for q in QUEUES:
        got = dijkstra_solver(inst.nodes, inst.adj, inst.nodes[0], queue_type=q)["distances"]
        for v in inst.nodes:
            assert got[v] == pytest.approx(expected[v])


def test_ties_produce_alternative_paths_with_equal_cost():
    inst = grid_network(4, 4, weight_mode="unit")
    src = inst.nodes[0]
    results = {q: dijkstra_solver(inst.nodes, inst.adj, src, queue_type=q) for q in QUEUES}
    results["bellman_ford"] = bellman_ford(inst.nodes, inst.adj, src)
    cmp = compare_results(inst.adj, inst.nodes, results, reference="bellman_ford")
    assert cmp["distances_equal"]
    # En una cuadrícula de pesos unitarios hay muchos caminos óptimos: alguna estructura desempata distinto.
    assert cmp["alternative_optimal_paths"], "se esperaban rutas alternativas por empates"
    for t in cmp["alternative_optimal_paths"]:
        for key, path in t.items():
            if isinstance(path, list):
                assert path_cost(inst.adj, path) == pytest.approx(t["cost"])


def test_no_alternative_paths_when_optimum_is_unique(instances_dir):
    inst = load_instance(str(instances_dir / "clrs_24_6.txt"))
    results = {q: dijkstra_solver(inst.nodes, inst.adj, "s", queue_type=q) for q in QUEUES}
    cmp = compare_results(inst.adj, inst.nodes, results)
    assert cmp["distances_equal"] and not cmp["alternative_optimal_paths"]


def test_compare_flags_real_distance_errors():
    nodes, adj = _random_graph(10, 30, 5)
    good = dijkstra_solver(nodes, adj, nodes[0])
    broken = {**good, "distances": {**good["distances"]}}
    victim = next(v for v in nodes if v != nodes[0] and good["distances"][v] != float("inf"))
    broken["distances"][victim] += 1.0
    cmp = compare_results(adj, nodes, {"ok": good, "roto": broken})
    assert not cmp["distances_equal"] and cmp["verdict"].startswith("DIFERENCIA")


def test_dary_heap_any_arity_gives_same_distances():
    from src.algorithms import dijkstra as dj
    from src.datastructures import registry
    from src.datastructures.d_ary_heap import DAryHeap
    inst = random_road_network(200, seed=5)
    base = dj.dijkstra_solver(inst.nodes, inst.adj, inst.nodes[0])["distances"]
    for d in (2, 3, 5, 16):
        registry.QUEUE_FACTORIES["tmp"] = lambda d=d: DAryHeap(d)
        try:
            assert dj.dijkstra_solver(inst.nodes, inst.adj, inst.nodes[0], queue_type="tmp")["distances"] == base
        finally:
            del registry.QUEUE_FACTORIES["tmp"]


@pytest.mark.parametrize("n", [1000, 3000])
def test_scale_equivalence(n):
    inst = random_road_network(n, seed=n)
    outs = {q: dijkstra_solver(inst.nodes, inst.adj, inst.nodes[0], queue_type=q) for q in QUEUES}
    assert compare_results(inst.adj, inst.nodes, outs)["distances_equal"]
    assert verify_shortest_paths(inst.nodes, inst.adj, inst.nodes[0], outs["fibonacci_heap"])["ok"]
