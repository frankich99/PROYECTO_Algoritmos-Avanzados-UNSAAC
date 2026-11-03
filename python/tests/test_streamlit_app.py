import json
from pathlib import Path
from copy import deepcopy

import pytest
import plotly.graph_objects as go
from streamlit.testing.v1 import AppTest

from app import (benchmark_frame, benchmark_figure, compare_route, route_figure,
                 solve_route, validate_benchmark_upload)
from src.benchmarks.applied_analysis import uniformly_scaled
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
    assert isinstance(figure.data[0], go.Scattergl)
    assert isinstance(route_figure(instance, path, basemap=True).data[0], go.Scattermap)


def test_comparison_ratio_uses_same_scale_binary_median():
    data = json.loads((DATA_DIR / "benchmark_results.json").read_text(encoding="utf-8"))
    frame = benchmark_frame(data, "sparse")
    binary = frame.loc[(frame["cola"] == "binary_heap") & (frame["vertices"] == 100)].iloc[0]
    other = frame.loc[(frame["cola"] == "4ary_heap") & (frame["vertices"] == 100)].iloc[0]
    assert binary["ratio_vs_binary"] == pytest.approx(1.0)
    assert other["ratio_vs_binary"] == pytest.approx(binary["mediana_us"] / other["mediana_us"])


def test_interactive_queues_and_astar_agree_on_canonical_cost():
    instance = load_snapshot(DATA_DIR / "cusco_osm_drive.json", metric="time")
    applied = json.loads((DATA_DIR / "applied_results.json").read_text(encoding="utf-8"))
    source, target = applied["query"]["source"], applied["query"]["target"]
    comparison = compare_route(instance, source, target)
    assert len(comparison) == 3
    assert all(row["costo"] == pytest.approx(387.197) for row in comparison)
    astar = solve_route(instance, source, target, "astar", "binary_heap")
    assert astar["costo"] == pytest.approx(comparison[0]["costo"])


def test_uniform_scenario_keeps_route_on_canonical_query():
    instance = load_snapshot(DATA_DIR / "cusco_osm_drive.json", metric="time")
    applied = json.loads((DATA_DIR / "applied_results.json").read_text(encoding="utf-8"))
    source, target = applied["query"]["source"], applied["query"]["target"]
    base = solve_route(instance, source, target, "dijkstra", "binary_heap")
    modified = solve_route(uniformly_scaled(instance, 1.2), source, target, "dijkstra", "binary_heap")
    assert modified["ruta"] == base["ruta"]
    assert modified["costo"] == pytest.approx(1.2 * base["costo"])


def test_uploaded_benchmark_must_have_valid_shared_scales():
    original = json.loads((DATA_DIR / "benchmark_results.json").read_text(encoding="utf-8"))
    assert validate_benchmark_upload(json.dumps(original).encode("utf-8"))["profiles"]
    broken = deepcopy(original)
    broken["profiles"]["sparse"]["data"]["binary_heap"][0]["median_us"] = float("nan")
    with pytest.raises(ValueError, match="Cuartiles"):
        validate_benchmark_upload(json.dumps(broken).encode("utf-8"))
    broken = deepcopy(original)
    broken["profiles"]["sparse"]["data"]["binary_heap"].pop()
    with pytest.raises(ValueError, match="escalas"):
        validate_benchmark_upload(json.dumps(broken).encode("utf-8"))
    broken = deepcopy(original)
    broken["profiles"]["sparse"]["data"]["4ary_heap"][0]["edges"] += 1
    with pytest.raises(ValueError, match="aristas"):
        validate_benchmark_upload(json.dumps(broken).encode("utf-8"))


def test_main_app_route_and_benchmark_without_external_services():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=40).run()
    assert not app.exception
    assert "Calcular ruta" in [button.label for button in app.button]
    app.button[0].click().run()
    assert not app.exception and not app.error
    assert app.metric[0].value == "387.20 s"
    app.radio[0].set_value("Comparación").run()
    assert not app.exception and not app.error
    assert app.dataframe


def test_web_does_not_use_environment_key_for_optional_weather(monkeypatch):
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "clave-no-usar")

    def reject_network(*_args, **_kwargs):
        raise AssertionError("La web no debe usar una clave implícita.")

    monkeypatch.setattr("requests.sessions.Session.get", reject_network)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=40).run()
    app.radio[0].set_value("Clima y tráfico").run()
    next(radio for radio in app.radio if radio.label == "Proveedor opcional").set_value("OpenWeatherMap").run()
    next(button for button in app.button if button.label == "Consultar condiciones ahora").click().run()
    assert not app.exception
    assert any("Introduzca una clave nueva" in error.value for error in app.error)
    assert not any("Consulta temporal" in success.value for success in app.success)


def test_all_five_sections_are_accessible_without_network(monkeypatch):
    def reject_network(*_args, **_kwargs):
        raise AssertionError("Las vistas locales no deben consultar APIs.")

    monkeypatch.setattr("requests.sessions.Session.get", reject_network)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=40).run()
    assert app.metric[0].value == "387.20 s"
    for section in ("Comparación", "Clima y tráfico", "Traza manual", "Datos y método", "Ruta"):
        app.radio[0].set_value(section).run()
        assert not app.exception and not app.error, section
        if section == "Traza manual":
            assert next(slider for slider in app.slider if slider.label == "Paso de la traza")
            assert len(app.dataframe) >= 2
        if section == "Clima y tráfico":
            assert next(slider for slider in app.slider if slider.label == "Hora simulada para explorar el supuesto")


def test_route_contrasts_three_queues_and_astar_without_timing_claims():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=40).run()
    next(item for item in app.checkbox if "Contrastar tres colas" in item.label).set_value(True).run()
    next(button for button in app.button if button.label == "Calcular ruta").click().run()
    assert not app.exception and not app.error
    assert app.metric[0].value == "387.20 s"
    assert any("cuatro ejecuciones" in item.value.lower() for item in app.subheader)


def test_historical_weather_scenario_uses_report_observation_not_local_snapshot():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=40).run()
    next(item for item in app.selectbox if item.label == "Fuente del escenario meteorológico").set_value(
        "Observación histórica del informe"
    ).run()
    next(button for button in app.button if button.label == "Calcular ruta").click().run()
    assert not app.exception and not app.error
    assert app.metric[0].value == "413.95 s"
    assert any("1.0691" in warning.value for warning in app.warning)
