"""
Validación con instancias pequeñas resueltas a mano (Avance 4).

Los valores esperados se derivan manualmente y se escriben como aritmética
explícita, no copiando la salida del programa.
"""
import math

import pytest

from src.algorithms.dijkstra import dijkstra_solver
from src.io.graph_io import load_instance
from src.models.cusco_network import get_cusco_adjacency
from src.verification.certificate import verify_shortest_paths
from tests.conftest import QUEUES

INF = float("inf")


def _run(nodes, adj, source, q, **kw):
    res = dijkstra_solver(nodes, adj, source, queue_type=q, **kw)
    cert = verify_shortest_paths(nodes, adj, source, res)
    assert cert["ok"], cert["violations"]
    return res


# ---------------------------------------------------------------- red del Cusco
@pytest.mark.parametrize("q", QUEUES)
def test_cusco_distance_hand_solved(q):
    # A-B 180, A-C 450, B-D 220, B-C 400, C-F 350, C-E 600, D-E 250, D-C 500, E-F 700
    expected = {
        "A": 0.0,
        "B": 180.0,                         # A-B
        "D": 180.0 + 220.0,                 # A-B-D = 400
        "C": min(450.0, 180.0 + 400.0),     # A-C = 450 (< A-B-C = 580)
        "E": min(400.0 + 250.0, 450.0 + 600.0),   # A-B-D-E = 650 (< A-C-E = 1050)
        "F": min(450.0 + 350.0, 650.0 + 700.0),   # A-C-F = 800 (< ...-E-F = 1350)
    }
    nodes, adj = get_cusco_adjacency("distance")
    res = _run(nodes, adj, "A", q)
    assert res["distances"] == expected
    assert res["paths"]["E"] == ["A", "B", "D", "E"]
    assert res["paths"]["F"] == ["A", "C", "F"]


@pytest.mark.parametrize("q", QUEUES)
def test_cusco_time_hand_solved(q):
    # t = L / v * (1 + 2.5 * max(0, p/100)); calle_centro 15 km/h, avenida 35 km/h
    v_centro, v_av = 15 / 3.6, 35 / 3.6
    t = lambda L, v, p: round(L / v * (1 + 2.5 * max(0.0, p / 100)), 2)
    AB, AC, BD = t(180, v_centro, 1.5), t(450, v_centro, -2.0), t(220, v_centro, 3.0)
    CF, DE = t(350, v_av, 0.5), t(250, v_centro, 2.5)
    nodes, adj = get_cusco_adjacency("time")
    res = _run(nodes, adj, "A", q)
    d = res["distances"]
    assert d["B"] == pytest.approx(AB)                 # 44.82 s
    assert d["C"] == pytest.approx(AC)                 # 108.00 s (bajada: sin penalización)
    assert d["D"] == pytest.approx(AB + BD)            # 101.58 s
    assert d["E"] == pytest.approx(AB + BD + DE)       # 165.33 s
    assert d["F"] == pytest.approx(AC + CF)            # 144.45 s


@pytest.mark.parametrize("q", QUEUES)
def test_cusco_operation_counts_match_manual_trace(q):
    nodes, adj = get_cusco_adjacency("distance")
    res = _run(nodes, adj, "A", q, record_trace=True)
    st = res["stats"]
    assert (st["insert_ops"], st["extract_min_ops"], st["decrease_key_ops"], st["relax_attempts"]) == (6, 6, 5, 9)
    assert [s["extracted"] for s in res["history"]] == ["A", "B", "D", "C", "E", "F"]


# ---------------------------------------------------------------- CLRS 24.6
@pytest.mark.parametrize("q", QUEUES)
def test_clrs_figure_24_6(q, instances_dir):
    inst = load_instance(str(instances_dir / "clrs_24_6.txt"))
    res = _run(inst.nodes, inst.adj, "s", q, record_trace=True)
    assert res["distances"] == {"s": 0.0, "t": 8.0, "x": 9.0, "y": 5.0, "z": 7.0}
    assert res["paths"]["x"] == ["s", "y", "t", "x"]
    assert [h["extracted"] for h in res["history"]] == ["s", "y", "z", "t", "x"]


# ---------------------------------------------------------------- límites
@pytest.mark.parametrize("q", QUEUES)
def test_single_node(q):
    res = _run(["A"], {"A": []}, "A", q)
    assert res["distances"] == {"A": 0.0} and res["paths"]["A"] == ["A"]


@pytest.mark.parametrize("q", QUEUES)
def test_unreachable_nodes(q, instances_dir):
    inst = load_instance(str(instances_dir / "desconectado.txt"))
    res = _run(inst.nodes, inst.adj, "A", q)
    assert res["distances"]["C"] == 5.0                     # A-B-C (2+3) < A-C (7)
    for v in ("G", "H", "Z"):
        assert res["distances"][v] == INF and res["paths"][v] == []
    assert res["stats"]["visited_count"] == 3


@pytest.mark.parametrize("q", QUEUES)
def test_source_without_outgoing_edges(q):
    res = _run(["A", "B"], {"A": [], "B": [("A", 1.0)]}, "A", q)
    assert res["distances"] == {"A": 0.0, "B": INF}


@pytest.mark.parametrize("q", QUEUES)
def test_zero_weight_edges_and_cycle(q):
    adj = {"U": [("V", 0.0)], "V": [("W", 5.0), ("U", 0.0)], "W": [("U", 0.0)]}
    res = _run(["U", "V", "W"], adj, "U", q)
    assert res["distances"] == {"U": 0.0, "V": 0.0, "W": 5.0}


@pytest.mark.parametrize("q", QUEUES)
def test_self_loops_and_parallel_edges(q):
    adj = {"A": [("A", 3.0), ("B", 9.0), ("B", 4.0)], "B": [("B", 0.0)]}
    res = _run(["A", "B"], adj, "A", q)
    assert res["distances"] == {"A": 0.0, "B": 4.0}          # usa la arista paralela barata


@pytest.mark.parametrize("q", QUEUES)
def test_large_and_tiny_weights(q):
    adj = {"A": [("B", 1e12), ("C", 1e-9)], "C": [("B", 1e-9)], "B": []}
    res = _run(["A", "B", "C"], adj, "A", q)
    assert math.isclose(res["distances"]["B"], 2e-9)


@pytest.mark.parametrize("q", QUEUES)
def test_integer_node_ids(q):
    adj = {0: [(1, 2.0)], 1: [(2, 2.0)], 2: []}
    res = _run([0, 1, 2], adj, 0, q)
    assert res["paths"][2] == [0, 1, 2]


@pytest.mark.parametrize("q", QUEUES)
def test_long_chain_no_recursion_issue(q):
    n = 3000
    nodes = list(range(n))
    adj = {i: [(i + 1, 1.0)] if i + 1 < n else [] for i in nodes}
    res = _run(nodes, adj, 0, q)
    assert res["distances"][n - 1] == n - 1
