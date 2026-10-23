"""
Casos adversos: manejo de entradas inválidas (lectura y validación).
"""
import json

import pytest

from src.algorithms.dijkstra import dijkstra_solver
from src.algorithms.reference import NegativeCycleError, bellman_ford
from src.algorithms.registry import solve
from src.io.graph_io import (InvalidInstanceError, load_instance, parse_inline, resolve_source,
                             validate_graph)
from src.verification.certificate import verify_shortest_paths


# ---------------------------------------------------------------- validación del grafo
@pytest.mark.parametrize("nodes, adj, source, fragment", [
    ([], {}, None, "no tiene vértices"),
    (["A", "A"], {"A": []}, None, "repetidos"),
    (["A"], {"A": [("X", 1.0)]}, "A", "no existe"),
    (["A", "B"], {"A": [("B", -1.0)], "B": []}, "A", "peso negativo"),
    (["A", "B"], {"A": [("B", float("nan"))], "B": []}, "A", "finito"),
    (["A", "B"], {"A": [("B", float("inf"))], "B": []}, "A", "finito"),
    (["A", "B"], {"A": [("B", "diez")], "B": []}, "A", "no es numérico"),
    (["A", "B"], {"A": [("B",)], "B": []}, "A", "mal formada"),
    (["A"], {"A": [], "Q": []}, "A", "no declarado"),
    (["A"], {"A": []}, "Z", "origen"),
])
def test_validate_graph_rejects(nodes, adj, source, fragment):
    with pytest.raises(InvalidInstanceError, match=fragment):
        validate_graph(nodes, adj, source)


def test_dijkstra_refuses_negative_weights_for_every_queue():
    adj = {"A": [("B", 4.0), ("C", 2.0)], "C": [("B", -3.0)], "B": []}
    for q in ("binary_heap", "4ary_heap", "fibonacci_heap"):
        with pytest.raises(InvalidInstanceError):
            dijkstra_solver(["A", "B", "C"], adj, "A", queue_type=q)


def test_bellman_ford_handles_negative_weight_and_detects_negative_cycle(instances_dir):
    inst = load_instance(str(instances_dir / "invalidas" / "peso_negativo.txt"))
    res = solve(inst, "A", "bellman_ford")
    assert res["distances"] == {"A": 0.0, "B": -1.0, "C": 2.0}
    inst2 = load_instance(str(instances_dir / "invalidas" / "ciclo_negativo.txt"))
    with pytest.raises(NegativeCycleError):
        bellman_ford(inst2.nodes, inst2.adj, "A")


def test_unknown_queue_type():
    with pytest.raises(ValueError):
        dijkstra_solver(["A"], {"A": []}, "A", queue_type="cola_inexistente")


# ---------------------------------------------------------------- lectura de archivos
@pytest.mark.parametrize("fname, fragment", [
    ("peso_no_numerico.txt", "no es numérico"),
    ("campos_incompletos.txt", "3 campos"),
    ("nodo_inexistente.json", "no fue declarado"),
    ("json_mal_formado.json", "JSON mal formado"),
    ("nodos_duplicados.json", "repetidos"),
])
def test_invalid_files(instances_dir, fname, fragment):
    with pytest.raises(InvalidInstanceError, match=fragment):
        load_instance(str(instances_dir / "invalidas" / fname))


def test_missing_file_and_bad_extension(tmp_path):
    with pytest.raises(InvalidInstanceError, match="No existe"):
        load_instance(str(tmp_path / "no_existe.json"))
    bad = tmp_path / "grafo.xlsx"
    bad.write_text("x")
    with pytest.raises(InvalidInstanceError, match="Extensión"):
        load_instance(str(bad))
    with pytest.raises(InvalidInstanceError, match="directorio"):
        load_instance(str(tmp_path))


def test_invalid_metric(instances_dir):
    with pytest.raises(InvalidInstanceError, match="Métrica"):
        load_instance(str(instances_dir / "cusco_centro.json"), metric="velocidad")


@pytest.mark.parametrize("payload, fragment", [
    ([1, 2, 3], "objeto"),
    ({"nodes": ["A"]}, "edges"),
    ({"edges": "A-B"}, "lista"),
    ({"edges": [["A", "B"]]}, "origen, destino, peso"),
    ({"edges": [{"origin": "A"}]}, "destination"),
    ({"edges": [{"origin": "A", "destination": "B"}]}, "weight"),
    ({"nodes": [{"name": "sin id"}], "edges": []}, "id"),
    ({"edges": [{"origin": "A", "destination": "B", "length_m": -5}]}, "longitud negativa"),
    ({"edges": [["A", "B", 1]], "source": "Q"}, "origen por defecto"),
])
def test_invalid_json_structures(tmp_path, payload, fragment):
    f = tmp_path / "inst.json"
    f.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(InvalidInstanceError, match=fragment):
        load_instance(str(f))


def test_non_utf8_file(tmp_path):
    f = tmp_path / "bin.txt"
    f.write_bytes(b"\xff\xfe\x00A B 1")
    with pytest.raises(InvalidInstanceError, match="UTF-8"):
        load_instance(str(f))


@pytest.mark.parametrize("spec", ["", "   ", "A B", "A B 1 2", "A B x"])
def test_invalid_inline(spec):
    with pytest.raises(InvalidInstanceError):
        parse_inline(spec)


# ---------------------------------------------------------------- lectura válida
def test_cusco_json_matches_builtin_model(instances_dir):
    from src.models.cusco_network import get_cusco_adjacency
    for metric in ("time", "distance"):
        inst = load_instance(str(instances_dir / "cusco_centro.json"), metric=metric)
        _, adj = get_cusco_adjacency(metric)
        assert inst.adj == adj
        assert inst.names["A"] == "Plaza Mayor del Cusco"


def test_inline_and_undirected():
    inst = parse_inline("undirected; A B 4; B C 2")
    assert ("A", 4.0) in inst.adj["B"] and ("B", 2.0) in inst.adj["C"]
    assert inst.num_edges == 4


def test_json_generic_formats_roundtrip(tmp_path):
    f = tmp_path / "g.json"
    f.write_text(json.dumps({"directed": False, "source": 1, "nodes": [1, 2, 3],
                             "edges": [[1, 2, 5], {"u": 2, "v": 3, "weight": 1.5}]}))
    inst = load_instance(str(f))
    assert inst.default_source == 1 and inst.num_edges == 4
    out = inst.save_json(str(tmp_path / "copia.json"))
    again = load_instance(str(out))
    assert again.adj == inst.adj


def test_resolve_source_by_string_for_numeric_ids(tmp_path):
    f = tmp_path / "g.json"
    f.write_text(json.dumps({"edges": [[1, 2, 5]]}))
    inst = load_instance(str(f))
    assert resolve_source(inst, "2") == 2
    with pytest.raises(InvalidInstanceError):
        resolve_source(inst, "99")


# ---------------------------------------------------------------- verificador detecta salidas incorrectas
def test_certificate_detects_wrong_outputs():
    nodes = ["A", "B", "C"]
    adj = {"A": [("B", 1.0), ("C", 5.0)], "B": [("C", 1.0)], "C": []}
    good = dijkstra_solver(nodes, adj, "A")
    assert verify_shortest_paths(nodes, adj, "A", good)["ok"]

    too_long = {**good, "distances": {**good["distances"], "C": 5.0}}
    assert not verify_shortest_paths(nodes, adj, "A", too_long)["ok"]          # (b) relajación pendiente

    too_short = {**good, "distances": {**good["distances"], "C": 1.0}}
    assert not verify_shortest_paths(nodes, adj, "A", too_short)["ok"]         # (c) cota no alcanzable

    bad_path = {**good, "paths": {**good["paths"], "C": ["A", "C"]}}
    assert not verify_shortest_paths(nodes, adj, "A", bad_path)["ok"]          # (d) costo de ruta != d

    bad_source = {**good, "distances": {**good["distances"], "A": 1.0}}
    assert not verify_shortest_paths(nodes, adj, "A", bad_source)["ok"]        # (a)
