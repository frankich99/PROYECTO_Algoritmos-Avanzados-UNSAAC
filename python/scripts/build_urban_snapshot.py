"""Construye y revisa un snapshot OSM ampliado; no altera el caso canónico.

Flujo recomendado en dos pasos:

1. Construir el pendiente (sin publicar)::

       python scripts/build_urban_snapshot.py --xml cusco_3000_drive.osm

2. Revisar el informe y, si todo cuadra, publicarlo::

       python scripts/build_urban_snapshot.py --publish --reviewed

El segundo paso vuelve a validar el pendiente y solo entonces escribe
``coverage_reviewed: true`` en el archivo final. El radio es una consulta
alrededor de un centro, no la cobertura administrativa de todo Cusco.
"""
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import sys

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.algorithms.dijkstra import dijkstra_solver
from src.io.osm_loader import graph_to_snapshot, snapshot_to_instance, save_snapshot

CENTER_LAT = -13.5165
CENTER_LON = -71.9788
MAX_NODES, MAX_EDGES = 5000, 30000
MIN_SCC_FRACTION = 0.80


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def _nearest_node(graph: nx.MultiDiGraph, lat: float, lon: float):
    """Nodo más cercano al centro en coordenadas geográficas; evita scikit-learn/scipy."""
    return min(graph.nodes, key=lambda n: (graph.nodes[n]["x"] - lon) ** 2
               + ((graph.nodes[n]["y"] - lat) * math.cos(math.radians(lat))) ** 2)


def _osm_base(xml_path: Path) -> str | None:
    try:
        head = xml_path.read_text(encoding="utf-8", errors="replace")[:4096]
    except OSError:
        return None
    match = re.search(r'osm_base="([^"]+)"', head)
    return match.group(1) if match else None


def _truncate_to_radius(graph: nx.MultiDiGraph, lat: float, lon: float, radius_m: int):
    import osmnx as ox
    center = _nearest_node(graph, lat, lon)
    projected = ox.project_graph(graph)
    truncated = ox.truncate.truncate_graph_dist(projected, center, dist=radius_m, weight="length")
    return ox.project_graph(truncated, to_crs="epsg:4326")


def _review(data: dict, radius_m: int, center: tuple[float, float]) -> list[str]:
    """Comprueba el snapshot y devuelve la lista de problemas encontrados."""
    instance = snapshot_to_instance(data, metric="time")
    problems: list[str] = []
    if not (10 <= instance.num_nodes <= MAX_NODES):
        problems.append(f"Nodos fuera del rango permitido: {instance.num_nodes}.")
    if not (10 <= instance.num_edges <= MAX_EDGES):
        problems.append(f"Aristas fuera del rango permitido: {instance.num_edges}.")

    lat0, lon0 = center
    distances = [_haversine_m(lat0, lon0, lat, lon) for lon, lat in instance.coords.values()]
    max_distance = max(distances) if distances else float("inf")
    tolerance = 150.0
    if max_distance > radius_m + tolerance:
        problems.append(f"Hay nodos a {max_distance:.0f} m del centro; el límite es "
                        f"{radius_m} m (+{tolerance:.0f} m de tolerancia).")

    for edge in data.get("edges", []):
        if not (math.isfinite(edge["length_m"]) and edge["length_m"] >= 0
                and math.isfinite(edge["travel_time_sec"]) and edge["travel_time_sec"] >= 0):
            problems.append("Hay aristas con longitud o tiempo inválido.")
            break

    graph = nx.DiGraph()
    graph.add_nodes_from(instance.nodes)
    for origin, neighbours in instance.adj.items():
        graph.add_edges_from((origin, destination) for destination, _ in neighbours)
    largest_scc = max((len(component) for component in nx.strongly_connected_components(graph)),
                      default=0) / max(instance.num_nodes, 1)
    largest_wcc = max((len(component) for component in nx.weakly_connected_components(graph)),
                      default=0) / max(instance.num_nodes, 1)
    if largest_scc < MIN_SCC_FRACTION:
        problems.append(f"La mayor componente fuertemente conexa solo cubre "
                        f"{largest_scc:.1%} de los nodos.")
    if largest_wcc < 0.95:
        problems.append(f"La mayor componente débil solo cubre {largest_wcc:.1%} de los nodos.")

    route_costs = []
    if largest_scc:
        strong = max(nx.strongly_connected_components(graph), key=len)
        ordered = sorted(strong, key=str)
        indices = [0, len(ordered) // 4, len(ordered) // 2, 3 * len(ordered) // 4, len(ordered) - 1]
        for source, target in zip(indices, indices[1:]):
            result = dijkstra_solver(instance.nodes, instance.adj, ordered[source],
                                     target=ordered[target], build_paths=False)
            cost = result["distances"][ordered[target]]
            if not math.isfinite(cost):
                problems.append(f"Sin ruta entre nodos de la componente principal: "
                                f"{ordered[source]!r} -> {ordered[target]!r}.")
                break
            route_costs.append(cost)

    geometry = sum(bool(edge.get("geometry_lonlat")) for edge in data.get("edges", []))
    print(f"  nodos: {instance.num_nodes}; aristas: {instance.num_edges}")
    print(f"  aristas con geometría: {geometry} "
          f"({geometry / max(instance.num_edges, 1):.1%})")
    print(f"  distancia máxima al centro: {max_distance:.0f} m")
    print(f"  componente fuertemente conexa mayor: {largest_scc:.1%}")
    print(f"  componente débil mayor: {largest_wcc:.1%}")
    if route_costs:
        print(f"  rutas de muestra: {len(route_costs)}; costo "
              f"{min(route_costs):.1f}–{max(route_costs):.1f} s")
    return problems


def _build_pending(args) -> None:
    try:
        import osmnx as ox
        if args.xml:
            graph = ox.graph_from_xml(Path(args.xml), simplify=True, retain_all=False)
            source = f"XML local: {Path(args.xml).name}"
            download_tool = f"OSMnx {ox.__version__} (graph_from_xml)"
            osm_base = _osm_base(Path(args.xml))
        else:
            if args.overpass_url:
                ox.settings.overpass_url = args.overpass_url
            if args.place:
                graph = ox.graph.graph_from_place(
                    args.place, network_type="drive", simplify=True, retain_all=False)
                source = "OSMnx graph_from_place"
                download_tool = f"OSMnx {ox.__version__}"
            else:
                graph = ox.graph.graph_from_point(
                    (args.center_lat, args.center_lon), dist=args.radius_m,
                    network_type="drive", simplify=True, retain_all=False)
                source = "OSMnx graph_from_point"
                download_tool = f"OSMnx {ox.__version__}"
            osm_base = None

        if args.place:
            scope = (f"Polígono devuelto por OSM para {args.place!r}; comprobar límites "
                     "antes de anunciar cobertura urbana.")
            place_query = args.place
            center = (args.center_lat, args.center_lon)
            extra = {}
            truncated = False
        else:
            center = (args.center_lat, args.center_lon)
            if not args.no_truncate:
                graph = _truncate_to_radius(graph, center[0], center[1], args.radius_m)
                truncated = True
            else:
                truncated = False
            scope = (f"Consulta radial de {args.radius_m} m alrededor de {center[0]}, "
                     f"{center[1]}; recortada por distancia de red. No es todo Cusco ni una "
                     "cobertura administrativa completa.")
            place_query = f"Cusco centro ampliado (consulta radial {args.radius_m} m)"
            extra = {"center_lat": center[0], "center_lon": center[1],
                     "radius_m": args.radius_m}

        data = graph_to_snapshot(graph, metadata={
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "place_query": place_query,
            "network_type": "drive",
            "source": source,
            "download_tool": download_tool,
            "osm_base_utc": osm_base,
            "coverage_reviewed": False,
            "scope_note": scope,
            "truncated_to_radius": truncated,
            **extra,
        })
        data["name"] = "cusco_urbano_drive"

        pending = args.output.with_suffix(".pending.json")
        if pending.exists():
            parser_error = (f"Ya existe {pending}; revíselo o elimínelo antes de repetir.")
            raise SystemExit(parser_error)

        print("Revisión previa del snapshot pendiente:")
        problems = _review(data, args.radius_m, center)
        if problems:
            raise SystemExit("No se guardó el pendiente:\n- " + "\n- ".join(problems))
        save_snapshot(pending, data)
        print(f"Snapshot pendiente: {pending}")
        print(f"Alcance: {scope}")
        print("Si el informe es correcto, publique con --publish --reviewed.")
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(f"No se creó el snapshot: {exc}") from exc


def _publish(args) -> None:
    pending = args.output.with_suffix(".pending.json")
    if not pending.exists():
        raise SystemExit(f"No existe {pending}; construya y revise el pendiente primero.")
    try:
        data = json.loads(pending.read_text(encoding="utf-8"))
        metadata = data.setdefault("metadata", {})
        center = (float(metadata.get("center_lat", args.center_lat)),
                  float(metadata.get("center_lon", args.center_lon)))
        radius_m = int(metadata.get("radius_m", args.radius_m))
        print("Revisión final antes de publicar:")
        problems = _review(data, radius_m, center)
        if problems:
            raise SystemExit("No se publicó:\n- " + "\n- ".join(problems))
        metadata["coverage_reviewed"] = True
        metadata["reviewed_at_utc"] = datetime.now(timezone.utc).isoformat()
        save_snapshot(args.output, data)
        pending.unlink()
        print(f"Publicado: {args.output}")
        print("coverage_reviewed = true; la API puede habilitar la cobertura urbana.")
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(f"No se publicó el snapshot: {exc}") from exc


def main() -> None:
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("--xml", type=Path, default=None,
                        help="XML de Overpass ya descargado; evita que OSMnx consulte Overpass.")
    parser.add_argument("--place", default=None,
                        help="Lugar geocodificable con polígono OSM. Si se omite, usa centro y radio.")
    parser.add_argument("--center-lat", type=float, default=CENTER_LAT)
    parser.add_argument("--center-lon", type=float, default=CENTER_LON)
    parser.add_argument("--radius-m", type=int, default=3000,
                        help="Radio alrededor del centro; no representa todo Cusco.")
    parser.add_argument("--overpass-url", default=None,
                        help="Espejo Overpass para la descarga directa con OSMnx.")
    parser.add_argument("--no-truncate", action="store_true",
                        help="Conserva las vías completas que cruzan el radio de consulta.")
    parser.add_argument("--publish", action="store_true",
                        help="Publica el pendiente ya revisado como archivo final.")
    parser.add_argument("--reviewed", action="store_true",
                        help="Confirma la revisión; obligatorio junto con --publish.")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).resolve().parents[1] / "data/processed/cusco_urbano_drive.json")
    args = parser.parse_args()

    if args.radius_m < 500 or args.radius_m > 10000:
        parser.error("El radio debe estar entre 500 y 10000 m.")
    if args.publish:
        if not args.reviewed:
            parser.error("--publish exige --reviewed: revise antes el archivo pendiente.")
        _publish(args)
    else:
        if args.output.exists():
            parser.error("El destino ya existe; guarde otro nombre y revise antes de reemplazarlo.")
        _build_pending(args)


if __name__ == "__main__":
    main()
