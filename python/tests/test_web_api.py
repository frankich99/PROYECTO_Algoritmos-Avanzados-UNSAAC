"""Contratos de la web: entradas arbitrarias, equivalencia y fuentes separadas."""
import json
import math
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from web_api import app


client = TestClient(app)
DATA = Path(__file__).resolve().parents[1] / "data" / "processed"


def test_catalog_and_openapi():
    assert client.get("/api/v1/health").json() == {"ok": True}
    catalog = client.get("/api/v1/catalog").json()
    assert catalog["networks"][0]["available"] is True
    assert set(catalog["queues"]) == {"binary_heap", "4ary_heap", "fibonacci_heap"}
    assert "/api/v1/routes/solve" in client.get("/openapi.json").json()["paths"]


def test_version_endpoint():
    payload = client.get("/api/v1/version").json()
    assert payload["name"] == "Rutas mínimas en Cusco"
    assert payload["version"] == "1.2.1"


def test_web_build_served_when_available():
    index = Path(__file__).resolve().parents[2] / "web" / "dist" / "index.html"
    if not index.is_file():
        pytest.skip("Build web no generado.")
    assert "Rutas mínimas en Cusco" in client.get("/").text
    assert '<div id="root"></div>' in client.get("/cualquier-ruta").text


def test_manual_example_all_queues_and_edges():
    response = client.post("/api/v1/routes/solve", json={
        "instance": {"kind": "example"}, "source": "A", "target": "E", "metric": "distance",
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["result"]["cost"] == 650
    assert data["result"]["length_m"] == 650
    assert len(data["comparisons"]) == 4
    assert all(row["cost"] == 650 for row in data["comparisons"])
    assert [edge["cost"] for edge in data["result"]["edges"]] == [180, 220, 250]


def test_osm_canonical_pair_keeps_distance_and_time_distinct():
    applied = json.loads((DATA / "applied_results.json").read_text(encoding="utf-8"))
    query = applied["query"]
    response = client.post("/api/v1/routes/solve", json={"instance": {"kind": "center"},
        "source": query["source"], "target": query["target"], "metric": "time"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["result"]["cost"] == pytest.approx(387.197)
    assert result["result"]["length_m"] == pytest.approx(2810.609)
    assert result["result"]["time_sec"] == pytest.approx(387.197)
    assert sum(edge["length_m"] for edge in result["result"]["edges"]) == pytest.approx(2810.609)
    assert sum(edge["time_sec"] for edge in result["result"]["edges"]) == pytest.approx(387.197)
    assert result["geometry_quality"] == "node_chords_only"
    assert result["counts"] == {"nodes": 891, "edges": 2139}


def test_arbitrary_new_instance_and_no_path():
    spec = {"kind": "custom", "data": {"nodes": ["X", "Y", "Z", "W"],
        "edges": [{"origin": "X", "destination": "Y", "weight": 1},
                  {"origin": "Y", "destination": "Z", "weight": 1},
                  {"origin": "X", "destination": "Z", "weight": 51}]}}
    assert client.post("/api/v1/instances/validate", json=spec).json()["nodes"] == 4
    response = client.post("/api/v1/routes/solve", json={"instance": spec, "source": "X", "target": "Z"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["unit"] == "peso" and data["result"]["cost"] == 2
    assert all(row["cost"] == 2 for row in data["comparisons"])
    assert data["result"]["length_m"] is None
    unreachable = client.post("/api/v1/routes/solve", json={"instance": spec, "source": "W", "target": "Z"}).json()
    assert unreachable["result"]["cost"] is None and unreachable["result"]["path"] == []
    assert all(row["cost"] is None for row in unreachable["comparisons"])


def test_custom_road_cost_units_and_parallel_edges():
    spec = {"kind": "custom", "data": {"directed": True, "nodes": ["A", "B", "C"],
        "edges": [{"origin": "A", "destination": "B", "length_m": 50, "street_type": "avenida", "gradient_pct": 0},
                  {"origin": "A", "destination": "B", "length_m": 200, "street_type": "avenida", "gradient_pct": 0},
                  {"origin": "B", "destination": "C", "length_m": 50, "street_type": "avenida", "gradient_pct": 0}]}}
    for metric in ("time", "distance"):
        response = client.post("/api/v1/routes/solve", json={"instance": spec, "source": "A", "target": "C", "metric": metric})
        assert response.status_code == 200, response.text
        result = response.json()["result"]
        assert result["length_m"] == pytest.approx(100)
        assert result["cost"] == pytest.approx(result["time_sec"] if metric == "time" else result["length_m"])
    spec["data"]["directed"] = False
    reversed_route = client.post("/api/v1/routes/solve", json={"instance": spec, "source": "C", "target": "A", "metric": "distance"})
    assert reversed_route.status_code == 200 and reversed_route.json()["result"]["length_m"] == 100


def test_zero_length_route_and_bad_custom_ids():
    zero = client.post("/api/v1/routes/solve", json={"instance": {"kind": "example"}, "source": "A", "target": "A"})
    assert zero.status_code == 200
    assert zero.json()["result"]["cost"] == 0
    assert zero.json()["result"]["time_sec"] == 0
    bad = {"kind": "custom", "data": {"nodes": [{"id": ["list"]}], "edges": []}}
    assert client.post("/api/v1/instances/validate", json=bad).status_code == 422
    assert client.post("/api/v1/routes/solve", json={"instance": bad, "source": "A", "target": "A"}).status_code == 422


def test_csv_import_with_header():
    spec = {"kind": "text", "text": "origen,destino,peso\nA,B,2\nB,C,3\nA,C,10"}
    validated = client.post("/api/v1/instances/validate", json=spec)
    assert validated.status_code == 200 and validated.json()["edges"] == 3
    result = client.post("/api/v1/routes/solve", json={"instance": spec, "source": "A", "target": "C"})
    assert result.status_code == 200 and result.json()["result"]["cost"] == 5


def test_claimed_metric_does_not_turn_generic_weights_into_measured_time():
    spec = {"kind": "custom", "data": {"metric": "time", "nodes": ["A", "B"],
        "edges": [{"origin": "A", "destination": "B", "weight": 3}]}}
    route = {"instance": spec, "source": "A", "target": "B", "metric": "time"}
    response = client.post("/api/v1/routes/solve", json=route)
    assert response.status_code == 200 and response.json()["unit"] == "peso"
    assert client.post("/api/v1/routes/solve", json={**route, "scenario": {"traffic_hour": 8}}).status_code == 422


def test_unverified_urban_snapshot_remains_hidden(tmp_path, monkeypatch):
    data = json.loads((DATA / "cusco_osm_drive.json").read_text(encoding="utf-8"))
    data["metadata"]["place_query"] = "Cusco, Cusco, Perú"
    data["metadata"]["coverage_reviewed"] = False
    urban = tmp_path / "urban.json"
    urban.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr("web_api.URBAN", urban)
    assert client.get("/api/v1/catalog").json()["networks"][1]["available"] is False
    assert client.post("/api/v1/instances/validate", json={"kind": "urban"}).status_code == 422
    data["metadata"]["coverage_reviewed"] = True
    urban.write_text(json.dumps(data), encoding="utf-8")
    assert client.get("/api/v1/catalog").json()["networks"][1]["available"] is True
    assert client.post("/api/v1/instances/validate", json={"kind": "urban"}).status_code == 200


def test_new_osm_snapshot_preserves_road_geometry(tmp_path, monkeypatch):
    import networkx as nx
    from shapely.geometry import LineString
    from src.io.osm_loader import graph_to_snapshot
    graph = nx.MultiDiGraph()
    graph.add_node(1, x=-71.98, y=-13.52)
    graph.add_node(2, x=-71.979, y=-13.52)
    graph.add_edge(1, 2, length=120, travel_time=12,
                   geometry=LineString([(-71.98, -13.52), (-71.9795, -13.5202), (-71.979, -13.52)]))
    payload = graph_to_snapshot(graph, metadata={"center_lat": -13.52, "center_lon": -71.98, "radius_m": 1500})
    path = tmp_path / "osm.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr("web_api.OSM", path)
    response = client.post("/api/v1/routes/solve", json={"instance": {"kind": "center"},
        "source": 1, "target": 2, "metric": "time"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["geometry_quality"] == "road_polyline"
    assert result["result"]["path_geometry"] == [[-71.98, -13.52], [-71.9795, -13.5202], [-71.979, -13.52]]
    assert result["result"]["length_m"] == 120
    assert result["result"]["time_sec"] == 12


def test_custom_metadata_cannot_impersonate_osm():
    spec = {"kind": "custom", "data": {"nodes": [{"id": "A", "lon": -71.98, "lat": -13.52}],
        "edges": [], "metadata": {"coordinate_kind": "lon_lat_wgs84"}}}
    response = client.post("/api/v1/routes/solve", json={"instance": spec,
        "source_point": {"lat": -13.52, "lon": -71.98}, "target": "A"})
    assert response.status_code == 422
    assert client.post("/api/v1/instances/validate", json=spec).json()["geographic"] is False


@pytest.mark.parametrize("payload", [
    {"nodes": ["A", "B"], "edges": [{"origin": "A", "destination": "B", "weight": -2}]},
    {"nodes": ["A", "B"], "edges": [{"origin": "A", "destination": "B", "weight": "NaN"}]},
    {"nodes": ["A", "A"], "edges": []},
    {"nodes": ["A"], "edges": [{"origin": "A", "destination": "B", "weight": 3}]},
])
def test_invalid_graph_rejected(payload):
    response = client.post("/api/v1/instances/validate", json={"kind": "custom", "data": payload})
    assert response.status_code == 422


def test_coordinates_snap_and_outside_rejected():
    applied = json.loads((DATA / "applied_results.json").read_text(encoding="utf-8"))
    lon, lat = applied["query"]["target_coords"]
    payload = {"instance": {"kind": "center"}, "source_point": {"lat": -13.5165, "lon": -71.9788},
               "target_point": {"lat": lat, "lon": lon}}
    response = client.post("/api/v1/routes/solve", json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["source_snap"]["offset_m_approx"] >= 0
    payload["source_point"] = {"lat": -12.0, "lon": -71.9788}
    assert client.post("/api/v1/routes/solve", json=payload).status_code == 422


def test_uniform_scenario_does_not_claim_new_path():
    base = {"instance": {"kind": "example"}, "source": "A", "target": "E", "metric": "time"}
    raw = client.post("/api/v1/routes/solve", json=base).json()
    changed = client.post("/api/v1/routes/solve", json={**base,
        "scenario": {"weather": "historical", "traffic_hour": None}}).json()
    assert changed["scenario"]["factor"] > 1
    assert changed["scenario"]["weather_timezone"] == "America/Lima"
    assert changed["result"]["path"] == raw["result"]["path"]
    assert changed["result"]["cost"] > raw["result"]["cost"]


def test_session_weather_reuses_exact_reading_without_second_provider_request(monkeypatch):
    from src.services.weather import WeatherObservation

    calls = []
    def fake_fetch(_self, lat, lon):
        calls.append((lat, lon))
        return WeatherObservation("2026-11-06T08:00", lat + .01, lon, 9, 2, 3000, 3, 15, 0,
                                  relative_humidity_pct=72)

    monkeypatch.setattr("web_api.OpenMeteoClient.fetch_current", fake_fetch)
    applied = json.loads((DATA / "applied_results.json").read_text(encoding="utf-8"))
    request = {"instance": {"kind": "center"}, "source": applied["query"]["source"],
               "target": applied["query"]["target"], "metric": "time"}
    # El punto consultado en el panel debe ser el mismo nodo de origen utilizado en la ruta.
    preview = client.post("/api/v1/instances/validate", json=request["instance"]).json()
    lon, lat = preview["coords"][str(request["source"])]
    origin = {"lat": lat, "lon": lon}
    reading = client.post("/api/v1/conditions", json={"point": origin}).json()
    assert reading["multiplier"] > 1
    assert reading["contributions"]["lluvia"] > 0
    assert reading["observation"]["temperature_c"] == 9
    scenario = {"weather": "live", "weather_observation": reading["observation"],
                "weather_request_point": origin}
    response = client.post("/api/v1/routes/solve", json={**request, "scenario": scenario})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["scenario"]["factor"] == reading["multiplier"]
    assert result["scenario"]["weather_contributions"] == reading["contributions"]
    assert result["scenario"]["weather_observed_at"] == reading["observation"]["observed_at"]
    assert calls == [(lat, lon)]  # La ruta no vuelve a consultar al proveedor.
    assert len({row["cost"] for row in result["comparisons"]}) == 1

    saved = client.post("/api/v1/routes/solve", json={**request, "scenario": {**scenario, "weather": "saved"}})
    assert saved.status_code == 200 and saved.json()["scenario"]["factor"] == reading["multiplier"]
    assert calls == [(lat, lon)]
    wrong_point = {**scenario, "weather_request_point": {"lat": origin["lat"] + .01, "lon": origin["lon"]}}
    assert client.post("/api/v1/routes/solve", json={**request, "scenario": wrong_point}).status_code == 422
    bad_humidity = {**scenario, "weather_observation": {**reading["observation"], "relative_humidity_pct": 120}}
    assert client.post("/api/v1/routes/solve", json={**request, "scenario": bad_humidity}).status_code == 422
    assert client.post("/api/v1/routes/solve", json={**request, "scenario": {"weather": "saved"}}).status_code == 422


def test_preview_large_network_keeps_bounded_edges():
    response = client.post("/api/v1/instances/validate", json={"kind": "urban"})
    if response.status_code == 422:
        pytest.skip("No hay snapshot urbano revisado en este entorno")
    preview = response.json()
    assert preview["nodes"] > 1200
    assert 0 < len(preview["display_edges"]) <= 3000
    assert preview["display_limited"] is True


def test_uniform_factor_cannot_flip_near_tied_route_through_edge_rounding():
    spec = {"kind": "custom", "data": {"nodes": ["A", "B", "C"], "edges": [
        {"origin": "A", "destination": "B", "length_m": 1, "travel_time_sec": 0.00000049},
        {"origin": "B", "destination": "C", "length_m": 1, "travel_time_sec": 0.00000049},
        {"origin": "A", "destination": "C", "length_m": 3, "travel_time_sec": 0.000001},
    ]}}
    request = {"instance": spec, "source": "A", "target": "C"}
    nominal = client.post("/api/v1/routes/solve", json=request).json()
    adjusted = client.post("/api/v1/routes/solve", json={**request,
        "scenario": {"weather": "historical"}}).json()
    assert nominal["result"]["path"] == ["A", "B", "C"]
    assert adjusted["result"]["path"] == nominal["result"]["path"]
    assert adjusted["result"]["cost"] == pytest.approx(nominal["result"]["cost"] * adjusted["scenario"]["factor"])
    assert adjusted["result"]["cost"] == pytest.approx(sum(edge["cost"] for edge in adjusted["result"]["edges"]))


def test_live_condition_mock_without_network(monkeypatch):
    from src.services.weather import WeatherObservation
    def fake_fetch(_self, lat, lon):
        return WeatherObservation("2026-11-05T12:00", lat + .01, lon, 12, 0, 10000, 3, 5, 0,
                                  relative_humidity_pct=66)
    monkeypatch.setattr("web_api.OpenMeteoClient.fetch_current", fake_fetch)
    response = client.post("/api/v1/conditions", json={"point": {"lat": -13.52, "lon": -71.98}})
    assert response.status_code == 200
    assert response.json()["observation"]["grid_point"]["lat"] != response.json()["requested"]["lat"]
    assert response.json()["observation"]["timezone"] == "America/Lima"
    assert client.post("/api/v1/conditions", json={"provider": "openweathermap"}).status_code == 422
    assert client.post("/api/v1/conditions", json={"provider": "tomtom"}).status_code == 422


def test_benchmark_read_only_and_new_experiment():
    before = (DATA / "benchmark_results.json").read_bytes()
    response = client.get("/api/v1/benchmarks/sparse")
    assert response.status_code == 200 and len(response.json()["results"]["scales"]) == 5
    experiment = client.post("/api/v1/experiments", json={"profile": "sparse", "sizes": [10], "runs": 2})
    assert experiment.status_code == 200, experiment.text
    assert len(experiment.json()["rows"]) == 3
    assert all(len(r["samples_us"]) == 4 for r in experiment.json()["rows"])
    assert before == (DATA / "benchmark_results.json").read_bytes()
