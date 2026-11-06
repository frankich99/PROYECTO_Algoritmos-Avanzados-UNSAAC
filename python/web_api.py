"""API de demostración: adaptador HTTP del núcleo, sin alterar resultados históricos."""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import json
import math
import os
from pathlib import Path
import statistics
import time
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.algorithms.a_star import a_star_solver
from src.algorithms.dijkstra import dijkstra_solver
from src.benchmarks.applied_analysis import nearest_node
from src.generators.instance_generator import benchmark_network, grid_network, random_road_network
from src.io.graph_io import GraphInstance, InvalidInstanceError, parse_edge_list, parse_instance_json, validate_graph
from src.io.osm_loader import load_snapshot as load_osm_snapshot
from src.models.cusco_network import load_cusco_instance
from src.services.traffic import TomTomTrafficClient, calculate_traffic_multiplier, get_traffic_by_schedule
from src.services.provider_keys import provider_key
from src.services.weather import (OpenMeteoClient, OpenWeatherMapClient, WeatherObservation,
                                  WeatherServiceError, weather_contributions, weather_multiplier)
from src.utils.cost_model import CuscoCostModel, RoadSegment

DATA = Path(__file__).resolve().parent / "data" / "processed"
OSM = DATA / "cusco_osm_drive.json"
URBAN = DATA / "cusco_urbano_drive.json"
BENCHMARK = DATA / "benchmark_results.json"
PILOT = DATA / "pilot_benchmark_results.json"
WEATHER = DATA / "weather_cusco.json"
MAX_NODES, MAX_EDGES = 5000, 30000
QUEUES = ("binary_heap", "4ary_heap", "fibonacci_heap")
API_VERSION = "1.2.1"
WEB_DIST = Path(os.environ.get(
    "RUTAS_WEB_DIST", Path(__file__).resolve().parent.parent / "web" / "dist"
)).resolve()
app = FastAPI(title="Rutas mínimas en Cusco", version=API_VERSION)
_cors_origins = [origin.strip() for origin in os.environ.get("RUTAS_CORS_ORIGINS", "").split(",") if origin.strip()]
if _cors_origins:
    app.add_middleware(CORSMiddleware, allow_origins=_cors_origins, allow_methods=["*"], allow_headers=["*"])


def _urban_available() -> bool:
    if not URBAN.exists():
        return False
    try:
        inst = load_osm_snapshot(URBAN, metric="time")
        return (inst.metadata.get("coverage_reviewed") is True
                and inst.metadata.get("coordinate_kind") == "lon_lat_wgs84"
                and bool(inst.metadata.get("place_query"))
                and inst.num_nodes >= 10 and inst.num_edges >= 10
                and inst.num_nodes <= MAX_NODES and inst.num_edges <= MAX_EDGES
                and all(math.isfinite(x) and math.isfinite(y) and -180 <= x <= 180 and -90 <= y <= 90
                        for x, y in inst.coords.values()))
    except (InvalidInstanceError, ValueError, TypeError, KeyError, OSError):
        return False


class InstanceSpec(BaseModel):
    kind: Literal["example", "center", "urban", "custom", "text", "generated"] = "center"
    data: dict[str, Any] | None = None
    text: str | None = None
    generator: Literal["random", "grid", "sparse", "dense"] = "random"
    nodes: int = Field(default=30, ge=2, le=500)
    seed: int = 42
    rows: int = Field(default=5, ge=1, le=30)
    cols: int = Field(default=5, ge=1, le=30)


class Point(BaseModel):
    lat: float = Field(ge=-90, le=90, allow_inf_nan=False)
    lon: float = Field(ge=-180, le=180, allow_inf_nan=False)


class SessionWeather(BaseModel):
    observed_at: str = Field(min_length=1, max_length=80)
    source: str = Field(min_length=1, max_length=120)
    timezone: str = Field(min_length=1, max_length=60)
    grid_point: Point
    temperature_c: float = Field(ge=-100, le=65, allow_inf_nan=False)
    precipitation_mm: float = Field(ge=0, le=1000, allow_inf_nan=False)
    visibility_m: float = Field(ge=0, le=100000, allow_inf_nan=False)
    wind_gusts_kmh: float = Field(ge=0, le=400, allow_inf_nan=False)
    relative_humidity_pct: float = Field(ge=0, le=100, allow_inf_nan=False)
    weather_code: int = 0
    weather_description: str = Field(default="", max_length=120)
    surface_pressure_hpa: float | None = Field(default=None, ge=0, le=2000, allow_inf_nan=False)


class Scenario(BaseModel):
    weather: Literal["none", "historical", "snapshot", "live", "saved"] = "none"
    weather_provider: Literal["open-meteo", "openweathermap"] = "open-meteo"
    weather_key: str | None = Field(default=None, max_length=200)
    weather_observation: SessionWeather | None = None
    weather_request_point: Point | None = None
    traffic_hour: float | None = Field(default=None, ge=0, lt=24, allow_inf_nan=False)
    traffic_mode: Literal["simulated", "current"] | None = None
    traffic_live: bool = False
    traffic_live_key: str | None = Field(default=None, max_length=200)


class RouteRequest(BaseModel):
    instance: InstanceSpec
    metric: Literal["time", "distance"] = "time"
    source: str | int | None = None
    target: str | int | None = None
    source_point: Point | None = None
    target_point: Point | None = None
    algorithm: Literal["dijkstra", "astar"] = "dijkstra"
    queue: Literal["binary_heap", "4ary_heap", "fibonacci_heap"] = "binary_heap"
    compare: bool = True
    scenario: Scenario = Field(default_factory=Scenario)


class ExperimentRequest(BaseModel):
    profile: Literal["sparse", "dense"] = "sparse"
    sizes: list[int] = Field(default_factory=lambda: [30, 60, 100], min_length=1, max_length=4)
    seed: int = 42
    runs: int = Field(default=5, ge=2, le=10)


class ConditionRequest(BaseModel):
    point: Point = Field(default_factory=lambda: Point(lat=-13.5165, lon=-71.9788))
    provider: Literal["open-meteo", "openweathermap", "tomtom"] = "open-meteo"
    key: str | None = Field(default=None, max_length=200)


def _problem(exc: Exception) -> HTTPException:
    return HTTPException(status_code=422, detail=str(exc))


def _instance(spec: InstanceSpec, metric: str) -> GraphInstance:
    if spec.kind == "example":
        instance = load_cusco_instance(metric)
    elif spec.kind in ("center", "urban"):
        path = OSM if spec.kind == "center" else URBAN
        if not path.exists() or (spec.kind == "urban" and not _urban_available()):
            raise InvalidInstanceError("La red solicitada no está disponible o sus límites aún no fueron revisados. Use la cobertura del centro.")
        instance = load_osm_snapshot(path, metric=metric)
    elif spec.kind == "custom":
        if spec.data is None or len(json.dumps(spec.data, ensure_ascii=False)) > 2_000_000:
            raise InvalidInstanceError("Envíe una instancia JSON de hasta 2 MB.")
        raw_nodes, raw_edges = spec.data.get("nodes"), spec.data.get("edges")
        if isinstance(raw_nodes, list) and len(raw_nodes) > MAX_NODES:
            raise InvalidInstanceError("Máximo 5000 nodos por instancia.")
        if isinstance(raw_edges, list) and len(raw_edges) > MAX_EDGES:
            raise InvalidInstanceError("Máximo 30000 aristas por instancia.")
        instance = parse_instance_json(spec.data, metric)
        if not raw_edges or not all(isinstance(edge, dict) and "length_m" in edge for edge in raw_edges):
            instance.metric = "weight"
    elif spec.kind == "text":
        if not spec.text or len(spec.text) > 2_000_000:
            raise InvalidInstanceError("Envíe una lista de aristas de hasta 2 MB.")
        if spec.text.count("\n") > MAX_EDGES + MAX_NODES:
            raise InvalidInstanceError("La lista supera el límite de líneas de la interfaz.")
        lines = spec.text.splitlines()
        for index, line in enumerate(lines):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            fields = [part.strip().lower() for part in line.replace(",", " ").split()]
            if fields in (["origin", "destination", "weight"], ["origen", "destino", "peso"],
                          ["from", "to", "weight"], ["u", "v", "w"]):
                lines.pop(index)
            break
        instance = parse_edge_list("\n".join(lines))
    else:
        if spec.generator == "grid":
            instance = grid_network(spec.rows, spec.cols, weight_mode="random", seed=spec.seed)
        elif spec.generator in ("sparse", "dense"):
            instance = benchmark_network(spec.nodes, spec.generator, spec.seed)
        else:
            instance = random_road_network(spec.nodes, seed=spec.seed)
    if instance.num_nodes > MAX_NODES or instance.num_edges > MAX_EDGES:
        raise InvalidInstanceError("Instancia demasiado grande para la interfaz; máximo 5000 nodos y 30000 aristas.")
    validate_graph(instance.nodes, instance.adj, instance.default_source)
    return instance


def _resolve_node(instance: GraphInstance, identifier: str | int | None, point: Point | None):
    if point is not None:
        if instance.metadata.get("coordinate_kind") != "lon_lat_wgs84":
            raise InvalidInstanceError("Las coordenadas geográficas requieren una red OSM georreferenciada.")
        if instance.metadata.get("radius_m") is not None:
            center_lat = float(instance.metadata.get("center_lat", -13.5165))
            center_lon = float(instance.metadata.get("center_lon", -71.9788))
            radius = float(instance.metadata["radius_m"])
            span_m = math.hypot((point.lon - center_lon) * 108_000, (point.lat - center_lat) * 111_000)
            if span_m > radius + 600:
                raise InvalidInstanceError("El punto está fuera de la cobertura aproximada de esta red.")
        node = nearest_node(instance, point.lon, point.lat)
        coords = instance.coords[node]
        offset = math.hypot((point.lon - coords[0]) * 108_000, (point.lat - coords[1]) * 111_000)
        if offset > 250:
            raise InvalidInstanceError(f"No hay nodo vial cercano: el más próximo está a {offset:.0f} m.")
        return node, {"requested": point.model_dump(), "node": node,
                      "snapped": {"lon": coords[0], "lat": coords[1]}, "offset_m_approx": round(offset, 1)}
    if identifier is None:
        raise InvalidInstanceError("Seleccione nodo o coordenadas para origen y destino.")
    if identifier in instance.adj:
        return identifier, None
    matches = [node for node in instance.nodes if str(node) == str(identifier)]
    if len(matches) != 1:
        raise InvalidInstanceError(f"El nodo {identifier!r} no existe o es ambiguo.")
    return matches[0], None


def _records(spec: InstanceSpec) -> list[dict[str, Any]]:
    if spec.kind in ("center", "urban"):
        path = OSM if spec.kind == "center" else URBAN
        return json.loads(path.read_text(encoding="utf-8"))["edges"]
    if spec.kind == "custom" and spec.data is not None:
        records = []
        for item in spec.data.get("edges", []):
            if not isinstance(item, dict):
                continue
            record = dict(item)
            record["origin"] = item.get("origin", item.get("u", item.get("from")))
            record["destination"] = item.get("destination", item.get("v", item.get("to")))
            if "length_m" in record and "travel_time_sec" not in record:
                try:
                    segment = RoadSegment(record["origin"], record["destination"], float(record["length_m"]),
                                          record.get("street_type", "calle_centro"), float(record.get("gradient_pct", 0.0)),
                                          record.get("street_name", ""))
                    record["travel_time_sec"] = CuscoCostModel.calculate_cost(segment, metric="time")
                except (ValueError, TypeError, KeyError, ZeroDivisionError):
                    pass
            records.append(record)
            if spec.data.get("directed") is False:
                records.append({**record, "origin": record["destination"], "destination": record["origin"]})
        return records
    if spec.kind == "example":
        return json.loads((Path(__file__).resolve().parent / "data" / "instances" / "cusco_centro.json").read_text(encoding="utf-8"))["edges"]
    return []


def _route_edges(path: list[Any], records: list[dict[str, Any]], metric: str,
                 adj: dict, factor: float) -> tuple[list[dict[str, Any]], float | None, float | None, list[list[float]]]:
    if len(path) == 1:
        has_physical = any("length_m" in record for record in records)
        return [], 0.0 if has_physical else None, 0.0 if has_physical else None, []
    pairs = {(u, v) for u, v in zip(path, path[1:])}
    selected = {}
    cost_field = "travel_time_sec" if metric == "time" else "length_m"
    for edge in records:
        u, v = edge.get("origin"), edge.get("destination")
        if (u, v) not in pairs:
            continue
        try:
            cost = float(edge[cost_field])
        except (KeyError, ValueError, TypeError):
            continue
        if not math.isfinite(cost):
            continue
        if (u, v) not in selected or cost < selected[(u, v)][0]:
            selected[(u, v)] = (cost, edge)
    segments = []
    length, time_s = 0.0, 0.0
    has_length, has_time = True, True
    polyline: list[list[float]] = []
    has_geometry = True
    for u, v in zip(path, path[1:]):
        weight = min(w for neighbor, w in adj[u] if neighbor == v)
        record = selected.get((u, v), (0, {}))[1]
        shape = record.get("geometry_lonlat")
        if isinstance(shape, list) and len(shape) >= 2:
            if polyline:
                first, last = shape[0], shape[-1]
                if math.dist(polyline[-1], last) < math.dist(polyline[-1], first):
                    shape = list(reversed(shape))
                polyline.extend(shape[1:])
            else:
                polyline.extend(shape)
        else:
            has_geometry = False
        distance = None
        try:
            distance = float(record["length_m"])
            has_length &= math.isfinite(distance) and distance >= 0
            length += distance
        except (KeyError, TypeError, ValueError):
            has_length = False
        seconds = None
        try:
            seconds = float(record["travel_time_sec"]) * factor
            has_time &= math.isfinite(seconds) and seconds >= 0
            time_s += seconds
        except (KeyError, TypeError, ValueError):
            has_time = False
        segments.append({"from": u, "to": v, "cost": weight * factor,
                         "length_m": distance if distance is not None and math.isfinite(distance) and distance >= 0 else None,
                         "time_sec": seconds if seconds is not None and math.isfinite(seconds) and seconds >= 0 else None,
                         "street": record.get("street_name") or None})
    return (segments, round(length, 3) if has_length and segments else None,
            round(time_s, 3) if has_time and segments else None, polyline if has_geometry else [])


def _scenario(value: Scenario, metric: str, source_point: Point | None) -> tuple[float, dict[str, Any]]:
    if metric != "time":
        if value.weather != "none" or value.traffic_hour is not None or value.traffic_mode is not None or value.traffic_live or value.traffic_live_key:
            raise InvalidInstanceError("Clima y horario solo afectan la métrica tiempo.")
        return 1.0, {"kind": "nominal"}
    factor = 1.0
    detail: dict[str, Any] = {"kind": "nominal"}
    if value.weather != "none":
        requested: Point | None = None
        if value.weather in ("live", "saved") and value.weather_observation is not None:
            reading = value.weather_observation
            if not source_point or not value.weather_request_point or (
                abs(source_point.lat - value.weather_request_point.lat) > 0.00001 or
                abs(source_point.lon - value.weather_request_point.lon) > 0.00001
            ):
                raise InvalidInstanceError("La lectura meteorológica no corresponde al origen actual. Actualícela.")
            requested = value.weather_request_point
            obs = WeatherObservation(observed_at=reading.observed_at,
                latitude=reading.grid_point.lat, longitude=reading.grid_point.lon,
                temperature_c=reading.temperature_c, precipitation_mm=reading.precipitation_mm,
                visibility_m=reading.visibility_m, wind_speed_kmh=0,
                wind_gusts_kmh=reading.wind_gusts_kmh, weather_code=reading.weather_code,
                relative_humidity_pct=reading.relative_humidity_pct,
                surface_pressure_hpa=reading.surface_pressure_hpa,
                weather_description=reading.weather_description,
                source=f"Lectura aportada por el navegador ({reading.source})", cached=True)
            timezone_label = reading.timezone
        elif value.weather == "saved":
            raise InvalidInstanceError("No hay una lectura local válida para aplicar.")
        elif value.weather == "historical":
            payload = json.loads((DATA / "applied_results.json").read_text(encoding="utf-8"))
            obs = WeatherObservation.from_dict(payload["weather_sensitivity"]["observation"], cached=True)
            requested = Point(lat=-13.5165, lon=-71.9788)
        elif value.weather == "snapshot":
            if not WEATHER.exists():
                raise InvalidInstanceError("No existe el snapshot climático local.")
            from src.services.weather import load_snapshot
            obs = load_snapshot(WEATHER)
        else:
            coords = source_point or Point(lat=-13.5165, lon=-71.9788)
            requested = coords
            if value.weather_provider == "openweathermap":
                key = (value.weather_key or "").strip() or provider_key("openweathermap")
                if not key:
                    raise InvalidInstanceError("Se requiere una clave OpenWeatherMap para esta consulta.")
                obs = OpenWeatherMapClient(api_key=key).fetch_current(coords.lat, coords.lon)
            else:
                obs = OpenMeteoClient().fetch_current(coords.lat, coords.lon)
        if value.weather not in ("live", "saved") or value.weather_observation is None:
            timezone_label = "America/Lima" if "Open-Meteo" in obs.source else "UTC"
        weather_factor = weather_multiplier(obs)
        factor *= weather_factor
        detail = {"kind": "uniform_scenario", "weather_source": obs.source,
                  "weather_factor": weather_factor,
                  "weather_session_supplied": value.weather in ("live", "saved") and value.weather_observation is not None,
                  "weather_observed_at": obs.observed_at,
                  "weather_timezone": timezone_label,
                  "weather_cached": obs.cached,
                  "weather_contributions": weather_contributions(obs),
                  "weather_reading": {"temperature_c": obs.temperature_c,
                                      "relative_humidity_pct": obs.relative_humidity_pct,
                                      "precipitation_mm": obs.precipitation_mm,
                                      "visibility_m": obs.visibility_m,
                                      "wind_gusts_kmh": obs.wind_gusts_kmh,
                                      "weather_code": obs.weather_code,
                                      "surface_pressure_hpa": obs.surface_pressure_hpa},
                  "requested_point": requested.model_dump() if requested else None,
                  "weather_grid_point": {"lat": obs.latitude, "lon": obs.longitude}}
    if value.traffic_mode == "current":
        if value.traffic_hour is not None:
            raise InvalidInstanceError("La hora actual se obtiene del servidor; no envíe una hora simulada.")
        now = datetime.now(ZoneInfo("America/Lima"))
        hour = now.hour + now.minute / 60 + now.second / 3600
        traffic = get_traffic_by_schedule(hour)
        traffic_factor = calculate_traffic_multiplier(traffic)
        detail.update({"traffic_mode": "current", "traffic_observed_at": now.isoformat(),
                       "traffic_hour": round(hour, 4), "traffic_source": "Horario supuesto a la hora actual de Cusco",
                       "traffic_level": traffic.level, "traffic_description": traffic.description})
        if value.traffic_live or value.traffic_live_key:
            if source_point is None:
                raise InvalidInstanceError("TomTom requiere un origen geográfico para la lectura puntual.")
            key = (value.traffic_live_key or "").strip() or provider_key("tomtom")
            if not key:
                raise InvalidInstanceError("TomTom requiere una clave configurada para esta consulta.")
            flow = TomTomTrafficClient(api_key=key).fetch_flow(
                lat=source_point.lat, lon=source_point.lon)
            if flow is None:
                raise InvalidInstanceError("No se obtuvo tráfico puntual de TomTom. Revise la clave y la cobertura, o desactive esa opción.")
            if flow.get("road_closure"):
                raise InvalidInstanceError("TomTom indica cierre del segmento cercano. No se puede extrapolar ese cierre a toda la ruta.")
            traffic_factor = flow["multiplier"]
            detail.update({"traffic_source": "TomTom: segmento cercano al origen, no toda la ruta",
                           "traffic_flow": flow, "traffic_flow_fetched_at_utc": datetime.now(timezone.utc).isoformat(),
                           "traffic_point": source_point.model_dump()})
        factor *= traffic_factor
        detail.update({"kind": "uniform_scenario", "traffic_factor": traffic_factor})
    elif value.traffic_hour is not None:
        if value.traffic_live or value.traffic_live_key:
            raise InvalidInstanceError("TomTom solo se consulta en el modo de hora actual.")
        traffic = get_traffic_by_schedule(value.traffic_hour)
        traffic_factor = calculate_traffic_multiplier(traffic)
        factor *= traffic_factor
        detail.update({"kind": "uniform_scenario", "traffic_mode": "simulated",
                       "traffic_source": "Horario supuesto, no medido", "traffic_factor": traffic_factor,
                       "traffic_level": traffic.level, "traffic_description": traffic.description,
                       "traffic_hour": value.traffic_hour})
    elif value.traffic_mode == "simulated" or value.traffic_live or value.traffic_live_key:
        raise InvalidInstanceError("Seleccione la hora simulada o el modo de hora actual antes de aplicar tráfico.")
    return round(factor, 4), detail


@app.get("/api/v1/health")
def health():
    return {"ok": True}


@app.get("/api/v1/version")
def version():
    return {"name": "Rutas mínimas en Cusco", "version": API_VERSION,
            "web_build": (WEB_DIST / "index.html").is_file()}


@app.get("/api/v1/catalog")
def catalog():
    return {"networks": [{"kind": "center", "label": "Centro, snapshot OSM (radio 1,5 km)",
                           "available": OSM.exists()},
                          {"kind": "urban", "label": "Centro ampliado, snapshot OSM (radio 3 km)",
                           "available": _urban_available()}],
            "queues": list(QUEUES), "example": "Seis nodos ilustrativos, no vías medidas",
            "provider_keys": {name: bool(provider_key(name)) for name in ("openweathermap", "tomtom")}}


@app.post("/api/v1/instances/validate")
def instance_validate(spec: InstanceSpec, metric: Literal["time", "distance"] = "time"):
    try:
        inst = _instance(spec, metric)
        stride = max(1, math.ceil(inst.num_edges / 3000))
        display_edges = [[u, v] for index, (u, v) in enumerate(
            (u, v) for u in inst.nodes for v, _ in inst.adj.get(u, [])) if index % stride == 0]
        return {"valid": True, "name": inst.name, "nodes": inst.num_nodes, "edges": inst.num_edges,
                 "ids": inst.nodes, "coords": inst.coords, "metric": inst.metric,
                 "geographic": spec.kind in ("center", "urban") and inst.metadata.get("coordinate_kind") == "lon_lat_wgs84",
                 "display_edges": display_edges[:3000],
                "display_limited": inst.num_nodes > 1200 or inst.num_edges > 3000}
    except (InvalidInstanceError, ValueError, KeyError, OSError) as exc:
        raise _problem(exc) from exc


@app.post("/api/v1/routes/solve")
def route_solve(request: RouteRequest):
    try:
        inst = _instance(request.instance, request.metric)
        if inst.metric == "weight" and (request.scenario.weather != "none" or request.scenario.traffic_hour is not None
                                        or request.scenario.traffic_mode is not None or request.scenario.traffic_live
                                        or request.scenario.traffic_live_key):
            raise InvalidInstanceError("Los escenarios meteorológicos solo se aplican a instancias con tiempos viales.")
        if (request.scenario.traffic_live or request.scenario.traffic_live_key) and request.instance.kind not in ("center", "urban"):
            raise InvalidInstanceError("La lectura puntual de TomTom requiere una red OSM de Cusco.")
        if (request.source_point or request.target_point) and request.instance.kind not in ("center", "urban"):
            raise InvalidInstanceError("El ajuste por coordenadas geográficas solo admite snapshots OSM verificados.")
        source, start = _resolve_node(inst, request.source, request.source_point)
        target, end = _resolve_node(inst, request.target, request.target_point)
        query_point = request.source_point
        if query_point is None and inst.metadata.get("coordinate_kind") == "lon_lat_wgs84" and source in inst.coords:
            lon, lat = inst.coords[source]
            query_point = Point(lat=lat, lon=lon)
        factor, scenario = _scenario(request.scenario, request.metric, query_point)
        # Un factor global positivo no altera el orden de las rutas. Se resuelve
        # el grafo base para que redondear cada arista no rompa esa propiedad.
        network = inst
        records = _records(request.instance)

        def execute(algorithm: str, queue: str) -> dict[str, Any]:
            if algorithm == "dijkstra":
                result = dijkstra_solver(network.nodes, network.adj, source, queue_type=queue,
                                         target=target, build_paths=False)
                cost = result["distances"][target]
                path = []
                if math.isfinite(cost):
                    at = target
                    while at is not None:
                        path.append(at)
                        at = result["predecessors"][at]
                    path.reverse()
                stats = result["stats"]
                elapsed = result["elapsed_ms"]
                expanded = stats["visited_count"]
            else:
                result = a_star_solver(network.nodes, network.adj, source, target,
                                       coords=network.coords, queue_type=queue)
                cost, path, stats = result["target_distance"], result["path"], result["stats"]
                elapsed, expanded = result["elapsed_ms"], stats["expanded_nodes"]
            edges, length, nominal_time, geometry = _route_edges(path, records, request.metric,
                                                                  network.adj, factor)
            return {"algorithm": algorithm, "queue": queue, "cost": cost * factor if math.isfinite(cost) else None,
                    "path": path, "edges": edges, "length_m": length, "time_sec": nominal_time,
                    "path_geometry": geometry,
                    "expanded": expanded, "relaxations": stats["relax_attempts"],
                    "decrease_key": stats.get("decrease_key_ops", 0),
                    "elapsed_ms_single_run": round(elapsed, 4)}

        chosen = execute(request.algorithm, request.queue)
        comparisons = [execute("dijkstra", queue) for queue in QUEUES] if request.compare else []
        if request.compare:
            costs = [item["cost"] for item in comparisons]
            if any((a is None) != (costs[0] is None) or
                   (a is not None and not math.isclose(a, costs[0], abs_tol=1e-6, rel_tol=1e-9))
                   for a in costs[1:]):
                raise InvalidInstanceError("Las tres colas no produjeron el mismo costo.")
            astar = execute("astar", request.queue)
            if (astar["cost"] is None) != (costs[0] is None) or (astar["cost"] is not None and
                not math.isclose(astar["cost"], costs[0], abs_tol=1e-6, rel_tol=1e-9)):
                raise InvalidInstanceError("A* y Dijkstra no produjeron el mismo costo.")
            comparisons.append(astar)
        has_geometry = bool(chosen["path_geometry"])
        return {"network": inst.name, "coverage": request.instance.kind,
                "counts": {"nodes": inst.num_nodes, "edges": inst.num_edges},
                "metric": request.metric, "unit": "peso" if inst.metric == "weight" else "s" if request.metric == "time" else "m",
                "source": source, "target": target, "source_snap": start, "target_snap": end,
                "result": chosen, "comparisons": comparisons,
                "path_coords": [inst.coords[node] for node in chosen["path"]] if
                all(node in inst.coords for node in chosen["path"]) else [],
                "scenario": {**scenario, "factor": factor},
                "geometry_quality": "road_polyline" if has_geometry else "node_chords_only" if request.instance.kind in ("center", "urban") else "abstract",
                "warning": "La geometría vial no está guardada: el trazo une nodos, no sigue curvas de calles."
                           if request.instance.kind in ("center", "urban") and not has_geometry else
                           "Pesos abstractos: las unidades físicas no están acreditadas." if inst.metric == "weight" else None}
    except (InvalidInstanceError, ValueError, KeyError, OSError, WeatherServiceError) as exc:
        raise _problem(exc) from exc


@app.get("/api/v1/benchmarks/{profile}")
def benchmark(profile: Literal["sparse", "dense"]):
    if not BENCHMARK.exists():
        raise HTTPException(404, "No existe el benchmark canónico.")
    data = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    return {"generated_at_utc": data.get("generated_at_utc"), "protocol": data["protocol"],
            "environment": data.get("environment"), "profile": profile, "results": data["profiles"][profile]}


@app.get("/api/v1/benchmarks/pilot/summary")
def pilot():
    if not PILOT.exists():
        raise HTTPException(404, "No existe el piloto.")
    return json.loads(PILOT.read_text(encoding="utf-8"))


@app.post("/api/v1/experiments")
def experiment(request: ExperimentRequest):
    if len(set(request.sizes)) != len(request.sizes) or any(n < 5 or n > 200 for n in request.sizes):
        raise HTTPException(422, "Use hasta cuatro tamaños distintos entre 5 y 200.")
    rows = []
    for size in sorted(request.sizes):
        samples = {queue: [] for queue in QUEUES}
        seeds = [request.seed + size * 31 + i for i in range(2)]
        edges = None
        for seed in seeds:
            instance = benchmark_network(size, request.profile, seed)
            edges = instance.num_edges
            answers = [dijkstra_solver(instance.nodes, instance.adj, instance.nodes[0], queue_type=q,
                                       build_paths=False) for q in QUEUES]
            for node in instance.nodes:
                values = [answer["distances"][node] for answer in answers]
                if any(not math.isclose(values[0], value, abs_tol=1e-6) for value in values[1:]):
                    raise HTTPException(500, "El experimento detectó costos distintos.")
            for queue in QUEUES:
                for _ in range(2):
                    dijkstra_solver(instance.nodes, instance.adj, instance.nodes[0], queue_type=queue,
                                    validate=False, build_paths=False)
                for _ in range(request.runs):
                    started = time.perf_counter_ns()
                    dijkstra_solver(instance.nodes, instance.adj, instance.nodes[0], queue_type=queue,
                                    validate=False, build_paths=False)
                    samples[queue].append((time.perf_counter_ns() - started) / 1000)
        for queue in QUEUES:
            ordered = sorted(samples[queue])
            rows.append({"nodes": size, "edges": edges, "queue": queue, "median_us": statistics.median(ordered),
                         "q1_us": ordered[len(ordered) // 4], "q3_us": ordered[3 * len(ordered) // 4],
                         "samples_us": ordered, "instance_seeds": seeds})
    return {"kind": "session_experiment_not_canonical", "profile": request.profile,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "protocol": {"runs_per_instance": request.runs, "instances_per_size": 2,
                         "warmup": 2, "clock": "perf_counter_ns", "gc": "normal",
                         "timing_scope": "solo solver, sin validación ni reconstrucción de caminos"}, "rows": rows}


@app.post("/api/v1/conditions")
def conditions(request: ConditionRequest):
    lat, lon, provider = request.point.lat, request.point.lon, request.provider
    key = (request.key or "").strip() or (provider_key(provider) if provider != "open-meteo" else None)
    try:
        if provider == "tomtom":
            if not key:
                raise InvalidInstanceError("TomTom requiere clave para la consulta puntual.")
            flow = TomTomTrafficClient(api_key=key).fetch_flow(lat=lat, lon=lon)
            if not flow:
                raise WeatherServiceError("No se obtuvo una lectura de tráfico puntual.")
            return {"kind": "point_traffic_not_network", "requested": {"lat": lat, "lon": lon},
                    "fetched_at_utc": datetime.now(timezone.utc).isoformat(), "flow": flow}
        if provider == "openweathermap" and not key:
            raise InvalidInstanceError("OpenWeatherMap requiere clave para esta consulta.")
        obs = (OpenMeteoClient().fetch_current(lat, lon) if provider == "open-meteo" else
               OpenWeatherMapClient(api_key=key).fetch_current(lat, lon))
        return {"kind": "model_weather_not_station", "requested": {"lat": lat, "lon": lon},
                "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
                 "multiplier": weather_multiplier(obs), "contributions": weather_contributions(obs),
                 "observation": {"temperature_c": obs.temperature_c, "relative_humidity_pct": obs.relative_humidity_pct,
                                 "precipitation_mm": obs.precipitation_mm, "visibility_m": obs.visibility_m,
                                 "wind_gusts_kmh": obs.wind_gusts_kmh, "observed_at": obs.observed_at,
                                 "timezone": "America/Lima" if provider == "open-meteo" else "UTC",
                                 "grid_point": {"lat": obs.latitude, "lon": obs.longitude}, "source": obs.source,
                                 "weather_code": obs.weather_code, "weather_description": obs.weather_description,
                                 "surface_pressure_hpa": obs.surface_pressure_hpa}}
    except (InvalidInstanceError, WeatherServiceError, ValueError) as exc:
        raise _problem(exc) from exc


if (WEB_DIST / "index.html").is_file() and (WEB_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="web-assets")

    @app.get("/", include_in_schema=False)
    def web_index():
        return FileResponse(WEB_DIST / "index.html")

    @app.get("/{path:path}", include_in_schema=False)
    def web_spa(path: str):
        candidate = (WEB_DIST / path).resolve()
        if candidate.is_file() and candidate.is_relative_to(WEB_DIST):
            return FileResponse(candidate)
        return FileResponse(WEB_DIST / "index.html")
