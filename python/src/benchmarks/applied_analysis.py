"""Caso aplicado sobre el snapshot OSM y sensibilidad meteorológica."""
from dataclasses import asdict
import json
import math
from pathlib import Path
from typing import Any, Dict, Hashable, Optional, Tuple

from src.algorithms.a_star import a_star_solver
from src.algorithms.dijkstra import dijkstra_solver
from src.datastructures.registry import available_queues
from src.io.graph_io import GraphInstance
from src.io.osm_loader import CUSCO_CENTER, load_snapshot as load_osm_snapshot
from src.services.weather import (
    OpenMeteoClient,
    WeatherImpactCoefficients,
    WeatherObservation,
    load_snapshot as load_weather_snapshot,
    weather_multiplier,
)
from src.utils.measurement import measure
from src.verification.certificate import compare_results, verify_shortest_paths


def nearest_node(instance: GraphInstance, lon: float, lat: float) -> Hashable:
    if not instance.coords:
        raise ValueError("La instancia no contiene coordenadas.")
    return min(
        instance.coords,
        key=lambda node: (instance.coords[node][0] - lon) ** 2 + (instance.coords[node][1] - lat) ** 2,
    )


def uniformly_scaled(instance: GraphInstance, multiplier: float) -> GraphInstance:
    if multiplier < 1.0:
        raise ValueError("El multiplicador debe ser >= 1.")
    return GraphInstance(
        nodes=list(instance.nodes),
        adj={
            u: [(v, round(weight * multiplier, 6)) for v, weight in instance.adj.get(u, [])]
            for u in instance.nodes
        },
        name=f"{instance.name}_weather_x{multiplier}",
        names=dict(instance.names),
        default_source=instance.default_source,
        metric=instance.metric,
        coords=dict(instance.coords),
        metadata={**instance.metadata, "weather_multiplier": multiplier},
    )


def _representative_query(instance: GraphInstance) -> Tuple[Hashable, Hashable, Dict[str, Any]]:
    source = nearest_node(instance, lon=CUSCO_CENTER[1], lat=CUSCO_CENTER[0])
    result = dijkstra_solver(instance.nodes, instance.adj, source, queue_type="binary_heap")
    reachable = {
        node: distance
        for node, distance in result["distances"].items()
        if node != source and math.isfinite(distance)
    }
    if not reachable:
        raise ValueError("La red OSM no tiene otro nodo alcanzable desde el origen.")
    target = max(reachable, key=reachable.get)
    return source, target, result


def run_applied_analysis(
    osm_snapshot_path: str | Path,
    weather_snapshot_path: str | Path,
    runs: int = 30,
    observation: Optional[WeatherObservation] = None,
) -> Dict[str, Any]:
    instance = load_osm_snapshot(osm_snapshot_path, metric="time")
    source, target, binary_full = _representative_query(instance)
    queues = available_queues()
    outputs = {
        "binary_heap": binary_full,
        **{
            queue: dijkstra_solver(instance.nodes, instance.adj, source, queue_type=queue)
            for queue in queues
            if queue != "binary_heap"
        },
    }
    comparison = compare_results(instance.adj, instance.nodes, outputs)
    certificates = {
        queue: verify_shortest_paths(instance.nodes, instance.adj, source, result)["ok"]
        for queue, result in outputs.items()
    }
    if not comparison["distances_equal"] or not all(certificates.values()):
        raise AssertionError("Las colas no produjeron resultados equivalentes en la red OSM.")

    timings = {}
    for queue in queues:
        timings[queue] = measure(
            lambda queue=queue: dijkstra_solver(
                instance.nodes,
                instance.adj,
                source,
                queue_type=queue,
                validate=False,
                build_paths=False,
            ),
            runs=runs,
            warmup=3,
            disable_gc=True,
            keep_samples=True,
        )
    winner = min(queues, key=lambda queue: timings[queue]["median_us"])

    dijkstra_target = dijkstra_solver(
        instance.nodes, instance.adj, source, queue_type="binary_heap", target=target
    )
    astar = a_star_solver(
        instance.nodes,
        instance.adj,
        source,
        target,
        coords=instance.coords,
        queue_type="binary_heap",
    )
    if not math.isclose(
        dijkstra_target["distances"][target], astar["target_distance"], rel_tol=1e-9, abs_tol=1e-9
    ):
        raise AssertionError("A* y Dijkstra difieren en el caso OSM.")

    if observation is None:
        weather_path = Path(weather_snapshot_path)
        observation = (
            load_weather_snapshot(weather_path)
            if weather_path.exists()
            else OpenMeteoClient().fetch_current(snapshot_path=weather_path)
        )
    coefficients = WeatherImpactCoefficients()
    multiplier = weather_multiplier(observation, coefficients)
    adjusted = uniformly_scaled(instance, multiplier)
    weather_result = dijkstra_solver(
        adjusted.nodes, adjusted.adj, source, queue_type="binary_heap", target=target
    )

    base_path = dijkstra_target["paths"][target]
    adjusted_path = weather_result["paths"][target]
    return {
        "schema_version": 1,
        "network": {
            "name": instance.name,
            "nodes": instance.num_nodes,
            "edges": instance.num_edges,
            "metric": instance.metric,
            "metadata": instance.metadata,
        },
        "query": {
            "selection": "origen más próximo al centro de extracción; destino alcanzable de mayor tiempo base",
            "source": source,
            "target": target,
            "source_coords": instance.coords[source],
            "target_coords": instance.coords[target],
            "path": base_path,
            "base_time_sec": dijkstra_target["distances"][target],
        },
        "queues": {
            "timings": timings,
            "winner_by_median": winner,
            "distances_equal": comparison["distances_equal"],
            "certificates_ok": certificates,
        },
        "astar_extension": {
            "heuristic": astar["heuristic"],
            "heuristic_scale": astar["heuristic_scale"],
            "cost_equal": True,
            "dijkstra_expanded": dijkstra_target["stats"]["visited_count"],
            "astar_expanded": astar["stats"]["expanded_nodes"],
        },
        "weather_sensitivity": {
            "observation": asdict(observation),
            "coefficients": asdict(coefficients),
            "multiplier": multiplier,
            "adjusted_time_sec": weather_result["distances"][target],
            "path_unchanged": adjusted_path == base_path,
            "scope": "factor uniforme de escenario; no es un modelo de tráfico calibrado",
        },
    }


def save_applied_analysis(result: Dict[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def export_applied_latex(result: Dict[str, Any], output_path: str | Path) -> Path:
    timings = result["queues"]["timings"]
    winner = result["queues"]["winner_by_median"]
    labels = {
        "binary_heap": "Binary Heap",
        "4ary_heap": "4-ary Heap",
        "fibonacci_heap": "Fibonacci Heap",
    }
    lines = [
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Caso OSM: tiempo de Dijkstra por cola, mediana e IQR.}",
        r"\label{tab:benchmark_osm}",
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"Cola & Mediana ($\mu$s) & Q1 ($\mu$s) & Q3 ($\mu$s) \\",
        r"\midrule",
    ]
    for queue in ("binary_heap", "4ary_heap", "fibonacci_heap"):
        row = timings[queue]
        label = rf"\textbf{{{labels[queue]}}}" if queue == winner else labels[queue]
        lines.append(f"{label} & {row['median_us']:.1f} & {row['q1_us']:.1f} & {row['q3_us']:.1f} " + r"\\")
    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Sensibilidad meteorológica uniforme en la consulta OSM.}",
        r"\label{tab:sensibilidad_clima}",
        r"\begin{tabular}{lrr}",
        r"\toprule",
        r"Escenario & Tiempo (s) & Cambio (\%) \\",
        r"\midrule",
    ])
    base = float(result["query"]["base_time_sec"])
    adjusted = float(result["weather_sensitivity"]["adjusted_time_sec"])
    change = 100.0 * (adjusted / base - 1.0)
    lines.extend([
        f"Base & {base:.2f} & 0.00 " + r"\\",
        f"Snapshot meteorológico & {adjusted:.2f} & {change:.2f} " + r"\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
