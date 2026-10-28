import json

import networkx as nx
import pytest

from src.io.graph_io import InvalidInstanceError
from src.io.osm_loader import (
    graph_to_snapshot,
    load_or_download_cusco,
    load_snapshot,
    save_snapshot,
    snapshot_to_instance,
)


def tiny_osm_graph():
    graph = nx.MultiDiGraph()
    graph.add_node(10, x=-71.98, y=-13.52)
    graph.add_node(20, x=-71.97, y=-13.51)
    graph.add_node(30, x=-71.96, y=-13.50)
    graph.add_edge(10, 20, length=100.0, highway="residential", name="Calle A")
    graph.add_edge(10, 20, length=120.0, travel_time=10.0, highway="primary", name="Calle B")
    graph.add_edge(20, 30, length=50.0, maxspeed="25 mph", highway="secondary")
    return graph


def test_graph_conversion_is_deterministic_and_preserves_parallel_edges():
    payload = graph_to_snapshot(tiny_osm_graph(), {"test": True})
    assert len(payload["edges"]) == 3
    parallel = [edge for edge in payload["edges"] if edge["origin"] == 10]
    assert [edge["travel_time_sec"] for edge in parallel] == sorted(
        edge["travel_time_sec"] for edge in parallel
    )
    assert payload["metadata"]["attribution"].startswith("© OpenStreetMap")


def test_snapshot_supports_time_and_distance_metrics(tmp_path):
    path = save_snapshot(tmp_path / "osm.json", graph_to_snapshot(tiny_osm_graph()))
    by_time = load_snapshot(path, metric="time")
    by_distance = load_snapshot(path, metric="distance")
    assert by_time.adj[10][0][1] == pytest.approx(10.0)
    assert by_distance.adj[10][0][1] == pytest.approx(100.0)
    assert by_time.coords[20] == pytest.approx((-71.97, -13.51))
    assert by_time.metadata["selected_metric"] == "time"


def test_cache_prevents_download(tmp_path):
    path = save_snapshot(tmp_path / "osm.json", graph_to_snapshot(tiny_osm_graph()))

    def forbidden(*_args, **_kwargs):
        raise AssertionError("No debe descargar si existe el snapshot")

    result = load_or_download_cusco(path, downloader=forbidden)
    assert result.num_edges == 2


def test_invalid_snapshot_and_graph_are_rejected(tmp_path):
    invalid = {"schema_version": 99, "nodes": [], "edges": []}
    with pytest.raises(InvalidInstanceError, match="Versión"):
        snapshot_to_instance(invalid)

    graph = nx.MultiDiGraph()
    graph.add_node(1, x=-71.0, y=-13.0)
    graph.add_node(2, x=-71.1, y=-13.1)
    graph.add_edge(1, 2, highway="residential")
    with pytest.raises(InvalidInstanceError, match="longitud"):
        graph_to_snapshot(graph)

    malformed = tmp_path / "bad.json"
    malformed.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
    with pytest.raises(InvalidInstanceError, match="listas"):
        load_snapshot(malformed)
