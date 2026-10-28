"""Benchmark canónico de Dijkstra con Binary, 4-ary y Fibonacci Heap."""
from datetime import datetime, timezone
import json
import math
import platform
from pathlib import Path
import random
import statistics
import sys
from typing import Any, Dict, List, Optional

import networkx as nx

from src.algorithms.dijkstra import dijkstra_solver
from src.datastructures.registry import available_queues
from src.generators.instance_generator import benchmark_network, generate_synthetic_road_network
from src.io.graph_io import GraphInstance
from src.utils.measurement import measure, summarize_samples
from src.verification.certificate import compare_results, verify_shortest_paths

QUEUE_LABELS = {
    "binary_heap": "Binary Heap",
    "4ary_heap": "4-ary Heap",
    "fibonacci_heap": "Fibonacci Heap",
}


def _networkx_oracle(instance: GraphInstance, source: Any) -> Dict[Any, float]:
    graph = nx.DiGraph()
    graph.add_nodes_from(instance.nodes)
    for u in instance.nodes:
        for v, weight in instance.adj.get(u, []):
            if not graph.has_edge(u, v) or weight < graph[u][v]["weight"]:
                graph.add_edge(u, v, weight=weight)
    found = nx.single_source_dijkstra_path_length(graph, source, weight="weight")
    return {node: float(found.get(node, math.inf)) for node in instance.nodes}


def _verify_instance(instance: GraphInstance, queue_types: List[str]) -> Dict[str, Dict[str, Any]]:
    source = instance.default_source if instance.default_source is not None else instance.nodes[0]
    outputs = {
        queue: dijkstra_solver(instance.nodes, instance.adj, source, queue_type=queue)
        for queue in queue_types
    }
    comparison = compare_results(instance.adj, instance.nodes, outputs)
    certificate = verify_shortest_paths(instance.nodes, instance.adj, source, outputs[queue_types[0]])
    oracle = _networkx_oracle(instance, source)
    oracle_ok = all(
        (math.isinf(oracle[node]) and math.isinf(outputs[queue_types[0]]["distances"][node]))
        or math.isclose(oracle[node], outputs[queue_types[0]]["distances"][node], rel_tol=1e-9, abs_tol=1e-9)
        for node in instance.nodes
    )
    if not comparison["distances_equal"] or not certificate["ok"] or not oracle_ok:
        raise AssertionError(
            f"Fallo de corrección en {instance.name}: "
            f"{comparison['distance_mismatches'][:3]} {certificate['violations'][:3]} oracle={oracle_ok}"
        )
    return outputs


def _average_operations(stats: List[Dict[str, Any]]) -> Dict[str, float]:
    keys = ["insert_ops", "extract_min_ops", "decrease_key_ops", "relax_attempts", "comparisons"]
    return {
        key: round(statistics.fmean(float(item.get(key, 0)) for item in stats), 3)
        for key in keys
    }


def _run_profile(
    profile: str,
    scales: List[int],
    runs: int,
    instances_per_size: int,
    seed: int,
    queue_types: List[str],
    verbose: bool,
) -> Dict[str, Any]:
    data = {queue: [] for queue in queue_types}
    winners = {queue: 0 for queue in queue_types}
    for n in scales:
        samples = {queue: [] for queue in queue_types}
        operations = {queue: [] for queue in queue_types}
        edge_counts = []
        instance_seeds = []
        for index in range(instances_per_size):
            instance_seed = seed + (10_000 if profile == "dense" else 0) + n * 31 + index
            instance_seeds.append(instance_seed)
            instance = benchmark_network(n, profile=profile, seed=instance_seed)
            edge_counts.append(instance.num_edges)
            outputs = _verify_instance(instance, queue_types)
            for queue in queue_types:
                operations[queue].append(outputs[queue]["stats"])

            order = list(queue_types)
            random.Random(instance_seed).shuffle(order)
            for queue in order:
                timing = measure(
                    lambda queue=queue: dijkstra_solver(
                        instance.nodes,
                        instance.adj,
                        instance.default_source,
                        queue_type=queue,
                        validate=False,
                        build_paths=False,
                    ),
                    runs=runs,
                    warmup=2,
                    disable_gc=True,
                    keep_samples=True,
                )
                samples[queue].extend(timing["samples_us"])

        median_edges = int(statistics.median(edge_counts))
        rows = {}
        for queue in queue_types:
            row = {
                "nodes": n,
                "edges": median_edges,
                "instance_count": instances_per_size,
                "runs_per_instance": runs,
                "instance_seeds": instance_seeds,
                **summarize_samples(samples[queue]),
                "samples_us": samples[queue],
                "operations_mean": _average_operations(operations[queue]),
            }
            data[queue].append(row)
            rows[queue] = row
        baseline = rows["binary_heap"]["median_us"]
        for queue in queue_types:
            rows[queue]["speedup_vs_binary"] = round(baseline / rows[queue]["median_us"], 4)
        winner = min(queue_types, key=lambda queue: rows[queue]["median_us"])
        winners[winner] += 1
        if verbose:
            times = ", ".join(f"{queue}={rows[queue]['median_us']:.1f} us" for queue in queue_types)
            print(f"[{profile}] V={n}, E={median_edges}: {times}; mejor={winner}")
    return {
        "description": (
            "E=4V" if profile == "sparse" else "E=0.08 V(V-1)"
        ),
        "scales": scales,
        "data": data,
        "winner_counts": winners,
    }


def run_canonical_benchmark(
    sparse_scales: Optional[List[int]] = None,
    dense_scales: Optional[List[int]] = None,
    runs: int = 15,
    instances_per_size: int = 3,
    seed: int = 12345,
    queue_types: Optional[List[str]] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    if runs < 1 or instances_per_size < 1:
        raise ValueError("runs e instances_per_size deben ser >= 1.")
    sparse_scales = sparse_scales if sparse_scales is not None else [100, 500, 1_000, 2_500, 5_000]
    dense_scales = dense_scales if dense_scales is not None else [50, 100, 200, 400, 800]
    queue_types = queue_types or available_queues()
    profiles = {}
    if sparse_scales:
        profiles["sparse"] = _run_profile(
            "sparse", sparse_scales, runs, instances_per_size, seed, queue_types, verbose
        )
    if dense_scales:
        profiles["dense"] = _run_profile(
            "dense", dense_scales, runs, instances_per_size, seed, queue_types, verbose
        )
    return {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": {
            "clock": "time.perf_counter_ns",
            "gc": "desactivado durante cada muestra",
            "warmup": 2,
            "runs_per_instance": runs,
            "instances_per_size": instances_per_size,
            "seed": seed,
            "oracle": "NetworkX single_source_dijkstra_path_length + certificado O(V+E)",
            "primary_statistic": "mediana; dispersión IQR",
        },
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "processor": platform.processor() or "no reportado",
        },
        "queue_types": queue_types,
        "profiles": profiles,
    }


def run_scalability_experiment(
    scales: Optional[List[int]] = None,
    num_runs: int = 20,
    seed: int = 12345,
    avg_degree: float = 3.5,
    queue_types: Optional[List[str]] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    """Compatibilidad CLI: ejecuta ambos perfiles sobre las escalas indicadas."""
    del avg_degree
    selected = scales if scales is not None else [100, 500, 1_000]
    return run_canonical_benchmark(
        sparse_scales=selected,
        dense_scales=selected,
        runs=num_runs,
        instances_per_size=1,
        seed=seed,
        queue_types=queue_types,
        verbose=verbose,
    )


def save_benchmark(results: Dict[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


PROFILE_LABELS = {"sparse": "disperso", "dense": "denso"}
PROFILE_DESCRIPTIONS = {
    "sparse": r"$|E|=4|V|$",
    "dense": r"$|E|=0.08|V|(|V|-1)$",
}
QUEUE_SHORT_LABELS = {
    "binary_heap": "Binary",
    "4ary_heap": "4-ary",
    "fibonacci_heap": "Fibonacci",
}


def _iqr_overlap(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    """Dos intervalos [Q1, Q3] se solapan si comparten al menos un punto."""
    return max(left["q1_us"], right["q1_us"]) <= min(left["q3_us"], right["q3_us"])


def _median_ratio(numerator: Dict[str, Any], denominator: Dict[str, Any]) -> float:
    return float(numerator["median_us"]) / float(denominator["median_us"])


def export_benchmark_latex_table(results: Dict[str, Any], output_path: str) -> None:
    """Escribe una tabla compacta con mediana e IQR apilados."""
    lines = []
    for profile, profile_data in results["profiles"].items():
        label = PROFILE_LABELS.get(profile, profile)
        lines.extend([
            r"\begin{table}[H]",
            r"\centering",
            r"\fontsize{9}{10.5}\selectfont",
            r"\renewcommand{\arraystretch}{1.12}",
            r"\setlength{\tabcolsep}{4pt}",
            rf"\caption{{Dijkstra con tres colas, perfil {label}: mediana e IQR en $\mu$s.}}",
            rf"\label{{tab:benchmark_{profile}}}",
            r"\begin{tabular}{@{}rrccc l@{}}",
            r"\toprule",
            r"$|V|$ & $|E|$ & \makecell{Binary\\Heap} & \makecell{4-ary\\Heap} & \makecell{Fibonacci\\Heap} & Mejor \\",
            r"\midrule",
        ])
        for index, n in enumerate(profile_data["scales"]):
            rows = {queue: profile_data["data"][queue][index] for queue in results["queue_types"]}
            winner = min(rows, key=lambda queue: rows[queue]["median_us"])
            cells = []
            for queue in ("binary_heap", "4ary_heap", "fibonacci_heap"):
                row = rows[queue]
                cells.append(
                    rf"\makecell{{{row['median_us']:.1f}\\{{\scriptsize[{row['q1_us']:.1f}, {row['q3_us']:.1f}]}}}}"
                )
            lines.append(
                f"{n} & {rows['binary_heap']['edges']} & " + " & ".join(cells)
                + f" & {QUEUE_SHORT_LABELS[winner]} \\\\"
            )
        lines.extend([
            r"\bottomrule",
            r"\end{tabular}",
            r"\par\vspace{0.1cm}",
            r"\raggedright\fontsize{8.5}{10.5}\selectfont\textit{Nota.} Cada celda muestra la mediana y, entre corchetes, el IQR.",
            r"\end{table}",
            "",
        ])
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def export_benchmark_summary_table(
    results: Dict[str, Any],
    output_path: str,
    applied: Optional[Dict[str, Any]] = None,
) -> None:
    """Sintetiza razones medianas, victorias e intersección de intervalos."""
    profile_stats: Dict[str, Dict[str, Any]] = {}
    all_ary: List[float] = []
    all_fib: List[float] = []
    total_wins_ary = 0
    total_wins_binary = 0
    total_overlap = 0

    for profile in ("sparse", "dense"):
        if profile not in results["profiles"]:
            continue
        data = results["profiles"][profile]["data"]
        ratios_ary: List[float] = []
        ratios_fib: List[float] = []
        wins_ary = 0
        wins_binary = 0
        overlaps = 0
        for binary, ary, fib in zip(data["binary_heap"], data["4ary_heap"], data["fibonacci_heap"]):
            ratios_ary.append(_median_ratio(ary, binary))
            ratios_fib.append(_median_ratio(fib, binary))
            if ary["median_us"] < binary["median_us"]:
                wins_ary += 1
            elif binary["median_us"] < ary["median_us"]:
                wins_binary += 1
            if _iqr_overlap(ary, binary):
                overlaps += 1
        profile_stats[profile] = {
            "ratio_ary": statistics.median(ratios_ary),
            "ratio_fib": statistics.median(ratios_fib),
            "wins_ary": wins_ary,
            "wins_binary": wins_binary,
            "overlaps": overlaps,
            "scales": len(data["binary_heap"]),
        }
        all_ary.extend(ratios_ary)
        all_fib.extend(ratios_fib)
        total_wins_ary += wins_ary
        total_wins_binary += wins_binary
        total_overlap += overlaps

    total_scales = len(all_ary)
    lines = [
        r"\begin{table}[H]",
        r"\centering",
        r"\fontsize{8.5}{10.5}\selectfont",
        r"\renewcommand{\arraystretch}{1.15}",
        r"\setlength{\tabcolsep}{4pt}",
        r"\caption{Síntesis comparativa por perfil y consulta. Las razones usan la mediana; no se declara un ganador cuando los IQR se solapan.}",
        r"\label{tab:sintesis_colas}",
        r"\begin{tabular}{@{}lrrrrr@{}}",
        r"\toprule",
        r"\textbf{Perfil} & \textbf{4-ary/Binary} & \textbf{Fibonacci/Binary} & \textbf{Gana 4-ary} & \textbf{Gana Binary} & \textbf{IQR solap.} \\",
        r"\midrule",
    ]
    for profile in ("sparse", "dense"):
        if profile not in profile_stats:
            continue
        stat = profile_stats[profile]
        lines.append(
            f"{PROFILE_LABELS[profile].capitalize()} ({PROFILE_DESCRIPTIONS[profile]}) & "
            f"{stat['ratio_ary']:.3f} & {stat['ratio_fib']:.3f} & "
            f"{stat['wins_ary']} de {stat['scales']} & {stat['wins_binary']} de {stat['scales']} & "
            f"{stat['overlaps']} de {stat['scales']} \\\\"
        )
    lines.append(r"\midrule")
    lines.append(
        f"Total sintético & {statistics.median(all_ary):.3f} & {statistics.median(all_fib):.3f} & "
        f"{total_wins_ary} de {total_scales} & {total_wins_binary} de {total_scales} & "
        f"{total_overlap} de {total_scales} \\\\"
    )

    if applied and applied.get("queues", {}).get("timings"):
        timings = applied["queues"]["timings"]
        binary = timings["binary_heap"]
        ary = timings["4ary_heap"]
        fib = timings["fibonacci_heap"]
        wins_ary = int(ary["median_us"] < binary["median_us"])
        wins_binary = int(binary["median_us"] < ary["median_us"])
        lines.append(
            f"Consulta OSM & {_median_ratio(ary, binary):.3f} & {_median_ratio(fib, binary):.3f} & "
            f"{wins_ary} & {wins_binary} & -- \\\\"
        )
    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\par\vspace{0.1cm}",
        r"\raggedright\fontsize{8}{10}\selectfont\textit{Nota.} Una razón 4-ary/Binary menor que 1 indica que el 4-ario fue más rápido. La columna IQR se refiere a 4-ary frente a Binary. Fibonacci no ganó ninguna escala sintética.",
        r"\end{table}",
        "",
    ])
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
