import json
from pathlib import Path

from app import benchmark_frame, benchmark_figure, route_figure
from src.io.osm_loader import load_snapshot

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"


def test_benchmark_view_uses_canonical_results():
    data = json.loads((DATA_DIR / "benchmark_results.json").read_text(encoding="utf-8"))
    frame = benchmark_frame(data, "sparse")
    assert not frame.empty
    assert set(frame["cola"]) == {"binary_heap", "4ary_heap", "fibonacci_heap"}
    figure = benchmark_figure(frame, "sparse")
    assert len(figure.data) == 3


def test_route_figure_contains_network_route_and_extremes():
    instance = load_snapshot(DATA_DIR / "cusco_osm_drive.json", metric="time")
    path = [instance.nodes[0], instance.adj[instance.nodes[0]][0][0]]
    figure = route_figure(instance, path)
    assert len(figure.data) == 3
    assert figure.data[1].name == "Ruta mínima"
