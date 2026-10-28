"""Descarga, normalización y caché reproducible de una red vial OSM de Cusco."""
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
from typing import Any, Callable, Dict, Hashable, Optional, Tuple

import networkx as nx

from src.io.graph_io import GraphInstance, InvalidInstanceError, build_instance, validate_graph

CUSCO_CENTER = (-13.5165, -71.9788)
DEFAULT_RADIUS_M = 1_500
SNAPSHOT_SCHEMA_VERSION = 1

# Supuestos explícitos para aristas sin maxspeed. No son mediciones de tráfico.
DEFAULT_SPEED_KMH = {
    "motorway": 60.0,
    "trunk": 50.0,
    "primary": 40.0,
    "secondary": 35.0,
    "tertiary": 30.0,
    "residential": 20.0,
    "unclassified": 20.0,
    "service": 15.0,
    "living_street": 10.0,
}


class OSMServiceError(RuntimeError):
    pass


def _plain_scalar(value: Any) -> Any:
    """Convierte escalares NumPy u objetos equivalentes a tipos JSON."""
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    return value


def _first(value: Any, default: Any = None) -> Any:
    if isinstance(value, (list, tuple)):
        return value[0] if value else default
    return default if value is None else value


def _parse_speed_kmh(raw: Any) -> Optional[float]:
    """Interpreta maxspeed de OSM; admite listas, km/h y mph."""
    raw = _first(raw)
    if raw is None:
        return None
    text = str(raw).strip().lower()
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return None
    speed = float(match.group(1))
    if "mph" in text:
        speed *= 1.609344
    return speed if speed > 0 else None


def _edge_speed_kmh(data: Dict[str, Any]) -> float:
    explicit = _parse_speed_kmh(data.get("maxspeed"))
    if explicit is not None:
        return explicit
    highway = str(_first(data.get("highway"), "unclassified"))
    return DEFAULT_SPEED_KMH.get(highway, DEFAULT_SPEED_KMH["unclassified"])


def _edge_record(u: Hashable, v: Hashable, data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        length_m = float(data["length"])
    except (KeyError, TypeError, ValueError):
        raise InvalidInstanceError(f"Arista OSM {u!r}->{v!r} sin longitud numérica.") from None
    if not math.isfinite(length_m) or length_m < 0:
        raise InvalidInstanceError(f"Arista OSM {u!r}->{v!r} con longitud inválida: {length_m!r}.")
    travel_time = data.get("travel_time")
    try:
        travel_time_s = float(travel_time) if travel_time is not None else length_m / (_edge_speed_kmh(data) / 3.6)
    except (TypeError, ValueError, ZeroDivisionError):
        raise InvalidInstanceError(f"Arista OSM {u!r}->{v!r} con tiempo inválido.") from None
    if not math.isfinite(travel_time_s) or travel_time_s < 0:
        raise InvalidInstanceError(f"Arista OSM {u!r}->{v!r} con tiempo inválido: {travel_time_s!r}.")
    return {
        "origin": _plain_scalar(u),
        "destination": _plain_scalar(v),
        "length_m": round(length_m, 3),
        "travel_time_sec": round(travel_time_s, 3),
        "highway": str(_first(data.get("highway"), "")),
        "street_name": str(_first(data.get("name"), "")),
        "maxspeed": str(_first(data.get("maxspeed"), "")),
    }


def graph_to_snapshot(
    graph: nx.MultiDiGraph,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Convierte un MultiDiGraph de OSMnx a un JSON independiente de OSMnx."""
    if not graph.is_directed():
        raise InvalidInstanceError("La red OSM debe ser dirigida.")
    nodes = []
    for node, data in sorted(graph.nodes(data=True), key=lambda item: str(item[0])):
        try:
            lon, lat = float(data["x"]), float(data["y"])
        except (KeyError, TypeError, ValueError):
            raise InvalidInstanceError(f"Nodo OSM {node!r} sin coordenadas x/y numéricas.") from None
        nodes.append({"id": _plain_scalar(node), "lon": lon, "lat": lat})

    # Se preservan aristas paralelas: la mejor puede depender de si se optimiza
    # tiempo o distancia. El orden se fija para que el snapshot sea estable.
    edges = []
    for u, v, _key, data in graph.edges(keys=True, data=True):
        edges.append(_edge_record(u, v, data))
    edges.sort(
        key=lambda edge: (
            str(edge["origin"]),
            str(edge["destination"]),
            edge["travel_time_sec"],
            edge["length_m"],
            edge["street_name"],
        )
    )
    if not nodes or not edges:
        raise InvalidInstanceError("La extracción OSM no contiene una red vial utilizable.")
    payload_metadata = {
        "provider": "OpenStreetMap",
        "attribution": "© OpenStreetMap contributors, ODbL 1.0",
        "coordinate_kind": "lon_lat_wgs84",
        "speed_policy": "maxspeed OSM; en ausencia, tabla explícita por highway",
        **(metadata or {}),
    }
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "name": "cusco_osm_drive",
        "directed": True,
        "nodes": nodes,
        "edges": edges,
        "metadata": payload_metadata,
    }


def snapshot_to_instance(payload: Dict[str, Any], metric: str = "time") -> GraphInstance:
    if metric not in ("time", "distance"):
        raise InvalidInstanceError("La métrica OSM debe ser 'time' o 'distance'.")
    if payload.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        raise InvalidInstanceError("Versión de snapshot OSM no soportada.")
    raw_nodes = payload.get("nodes")
    raw_edges = payload.get("edges")
    if not isinstance(raw_nodes, list) or not isinstance(raw_edges, list):
        raise InvalidInstanceError("Snapshot OSM sin listas 'nodes' y 'edges'.")

    nodes = []
    coords = {}
    for index, item in enumerate(raw_nodes, 1):
        if not isinstance(item, dict) or "id" not in item:
            raise InvalidInstanceError(f"Nodo OSM #{index} inválido.")
        try:
            coords[item["id"]] = (float(item["lon"]), float(item["lat"]))
        except (KeyError, TypeError, ValueError):
            raise InvalidInstanceError(f"Nodo OSM #{index} sin lon/lat numéricas.") from None
        nodes.append(item["id"])

    best_weights: Dict[Tuple[Hashable, Hashable], float] = {}
    for index, item in enumerate(raw_edges, 1):
        if not isinstance(item, dict):
            raise InvalidInstanceError(f"Arista OSM #{index} inválida.")
        field = "travel_time_sec" if metric == "time" else "length_m"
        try:
            pair = (item["origin"], item["destination"])
            weight = float(item[field])
            if pair not in best_weights or weight < best_weights[pair]:
                best_weights[pair] = weight
        except (KeyError, TypeError, ValueError):
            raise InvalidInstanceError(f"Arista OSM #{index} sin {field} numérico.") from None

    edge_tuples = [(u, v, weight) for (u, v), weight in best_weights.items()]
    metadata = dict(payload.get("metadata") or {})
    metadata["selected_metric"] = metric
    instance = build_instance(
        edge_tuples,
        declared_nodes=nodes,
        name=str(payload.get("name", "cusco_osm_drive")),
        default_source=nodes[0] if nodes else None,
        metric=metric,
        coords=coords,
        metadata=metadata,
    )
    validate_graph(instance.nodes, instance.adj, instance.default_source)
    return instance


def save_snapshot(path: str | Path, payload: Dict[str, Any]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return destination


def load_snapshot(path: str | Path, metric: str = "time") -> GraphInstance:
    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidInstanceError(f"No se pudo leer el snapshot OSM: {source}.") from exc
    return snapshot_to_instance(payload, metric=metric)


def download_cusco_network(
    snapshot_path: str | Path,
    metric: str = "time",
    center: Tuple[float, float] = CUSCO_CENTER,
    radius_m: int = DEFAULT_RADIUS_M,
    network_type: str = "drive",
) -> GraphInstance:
    """Descarga una vez mediante OSMnx y congela el resultado en JSON."""
    if radius_m <= 0:
        raise ValueError("radius_m debe ser positivo.")
    try:
        import osmnx as ox

        graph_from_point = getattr(ox, "graph_from_point", None)
        if graph_from_point is None:
            graph_from_point = ox.graph.graph_from_point
        graph = graph_from_point(
            center,
            dist=radius_m,
            network_type=network_type,
            simplify=True,
            retain_all=False,
        )
    except Exception as exc:
        raise OSMServiceError("No se pudo descargar la red vial de OpenStreetMap.") from exc

    payload = graph_to_snapshot(
        graph,
        metadata={
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "center_lat": center[0],
            "center_lon": center[1],
            "radius_m": radius_m,
            "network_type": network_type,
            "download_tool": f"OSMnx {getattr(ox, '__version__', 'desconocida')}",
        },
    )
    save_snapshot(snapshot_path, payload)
    return snapshot_to_instance(payload, metric=metric)


def load_or_download_cusco(
    snapshot_path: str | Path,
    metric: str = "time",
    refresh: bool = False,
    downloader: Callable[..., GraphInstance] = download_cusco_network,
    **download_kwargs: Any,
) -> GraphInstance:
    path = Path(snapshot_path)
    if path.exists() and not refresh:
        return load_snapshot(path, metric=metric)
    return downloader(path, metric=metric, **download_kwargs)
