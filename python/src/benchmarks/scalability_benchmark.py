"""
Benchmark de escalabilidad: Binary Heap vs 4-ary Heap vs Fibonacci Heap.

Reutiliza los módulos comunes: generación (instance_generator), ejecución
(dijkstra_solver), verificación (compare_results / certificado) y medición
(measure). Antes de medir, comprueba que las tres colas producen las mismas
distancias; si no, aborta (no se reportan tiempos de un resultado incorrecto).
"""
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.algorithms.dijkstra import dijkstra_solver
from src.datastructures.registry import available_queues
from src.generators.instance_generator import generate_synthetic_road_network  # noqa: F401 (re-export)
from src.generators.instance_generator import random_road_network
from src.utils.measurement import measure
from src.verification.certificate import compare_results, verify_shortest_paths


def run_scalability_experiment(
    scales: Optional[List[int]] = None,
    num_runs: int = 20,
    seed: int = 12345,
    avg_degree: float = 3.5,
    queue_types: Optional[List[str]] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    if scales is None:
        scales = [10, 25, 50, 100, 250, 500, 1000]
    queue_types = queue_types or available_queues()
    results: Dict[str, Any] = {
        "scales": scales,
        "queue_types": queue_types,
        "num_runs": num_runs,
        "seed": seed,
        "data": {q: [] for q in queue_types},
        "edge_counts": [],
        "operation_counts": {q: [] for q in queue_types},
    }
    if verbose:
        print(f"[*] Escalabilidad: {len(scales)} tamaños x {num_runs} pasadas, colas = {', '.join(queue_types)}")

    for n in scales:
        inst = random_road_network(n, avg_degree=avg_degree, seed=seed + n)
        nodes, adj, source = inst.nodes, inst.adj, inst.nodes[0]
        results["edge_counts"].append(inst.num_edges)

        outs = {q: dijkstra_solver(nodes, adj, source, queue_type=q) for q in queue_types}
        cmp = compare_results(adj, nodes, outs)
        cert = verify_shortest_paths(nodes, adj, source, outs[queue_types[0]])
        if not cmp["distances_equal"] or not cert["ok"]:
            raise AssertionError(f"Error de corrección en N={n}: {cmp['distance_mismatches'][:3]} {cert['violations'][:3]}")

        if verbose:
            print(f"  -> N = {n:5d}, M = {inst.num_edges:6d} (resultados equivalentes y certificados)")
        for q in queue_types:
            t = measure(lambda q=q: dijkstra_solver(nodes, adj, source, queue_type=q,
                                                   validate=False, build_paths=False),
                        runs=num_runs, warmup=2)
            results["data"][q].append({"nodes": n, "edges": inst.num_edges, **t})
            results["operation_counts"][q].append(outs[q]["stats"])
            if verbose:
                st = outs[q]["stats"]
                print(f"     [{q:14s}] media {t['mean_us']:10.2f} µs ± {t['std_us']:8.2f} | "
                      f"dec-key {st['decrease_key_ops']:6d} | comparaciones {st['comparisons']:8d}")
    return results


def export_benchmark_latex_table(results: Dict[str, Any], output_path: str) -> None:
    """Exporta los resultados a una tabla LaTeX (speedup relativo al Binary Heap)."""
    lines = [
        r"\begin{table}[H]",
        r"    \centering",
        r"    \fontsize{10}{12.5}\selectfont",
        r"    \setlength{\tabcolsep}{3pt}",
        r"    \caption{Tiempos de ejecución ($\mu s$) por cantidad de vértices y tipo de heap}",
        r"    \label{tab:benchmark_escalabilidad}",
        r"    \begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}rrcrcrc@{}}",
        r"        \toprule",
        r"        \textbf{$|V|$} & \textbf{$|E|$} & \textbf{Bin. Heap ($\mu s$)} & \textbf{4-ary ($\mu s$)} & \textbf{Sp. 4-ary} & \textbf{Fib. Heap ($\mu s$)} & \textbf{Sp. Fib.} \\",
        r"        \midrule",
    ]
    for i, n in enumerate(results["scales"]):
        b = results["data"]["binary_heap"][i]
        f4 = results["data"]["4ary_heap"][i]
        fb = results["data"]["fibonacci_heap"][i]
        sp4 = f"{b['mean_us'] / f4['mean_us']:.2f}x" if f4["mean_us"] > 0 else "N/A"
        spf = f"{b['mean_us'] / fb['mean_us']:.2f}x" if fb["mean_us"] > 0 else "N/A"
        lines.append(
            f"        {n} & {results['edge_counts'][i]} & {b['mean_us']:.1f} $\\pm {b['std_us']:.1f}$ & "
            f"{f4['mean_us']:.1f} $\\pm {f4['std_us']:.1f}$ & {sp4} & "
            f"{fb['mean_us']:.1f} $\\pm {fb['std_us']:.1f}$ & {spf} \\\\"
        )
    lines += [
        r"        \bottomrule",
        r"    \end{tabular*}",
        r"    \vspace{0.15cm}",
        r"    \raggedright",
        f"    \\textit{{Nota.}} Promedio de {results.get('num_runs', 20)} pasadas (2 de calentamiento). Speedup relativo al Binary Heap.",
        r"\end{table}",
    ]
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
