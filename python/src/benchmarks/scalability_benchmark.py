"""
Benchmark de escalabilidad.
Compara el tiempo de ejecución y operaciones entre Binary Min-Heap, 4-ary Heap y Fibonacci Heap
variando la cantidad de nodos.
"""
import time
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any

from src.algorithms.dijkstra import dijkstra_solver


def generate_synthetic_road_network(
    num_nodes: int,
    avg_degree: float = 3.5,
    seed: int = 42
) -> Tuple[List[str], Dict[str, List[Tuple[str, float]]]]:
    """
    Genera un grafo dirigido sintético para las pruebas.
    Primero creamos un árbol para asegurar que sea conexo desde el origen y
    luego agregamos aristas hasta llegar al grado promedio.
    """
    rng = random.Random(seed)
    nodes = [f"N{i}" for i in range(num_nodes)]
    adj: Dict[str, List[Tuple[str, float]]] = {v: [] for v in nodes}

    # 1. Asegurar conectividad
    for i in range(1, num_nodes):
        parent_idx = rng.randint(max(0, i - 4), i - 1)
        w = round(rng.uniform(15.0, 300.0), 1)
        adj[nodes[parent_idx]].append((nodes[i], w))
        # Sentido inverso
        if rng.random() < 0.6:
            adj[nodes[i]].append((nodes[parent_idx], round(rng.uniform(15.0, 300.0), 1)))

    # 2. Agregar aristas hasta el grado promedio
    target_edges = int(num_nodes * avg_degree)
    current_edges = sum(len(neighbors) for neighbors in adj.values())

    existing_edges = set()
    for u, neighbors in adj.items():
        for v, _ in neighbors:
            existing_edges.add((u, v))

    attempts = 0
    max_attempts = target_edges * 5
    while current_edges < target_edges and attempts < max_attempts:
        attempts += 1
        u_idx = rng.randint(0, num_nodes - 1)
        delta = rng.choice([-3, -2, -1, 1, 2, 3])
        v_idx = u_idx + delta
        if 0 <= v_idx < num_nodes and u_idx != v_idx:
            u, v = nodes[u_idx], nodes[v_idx]
            if (u, v) not in existing_edges:
                w = round(rng.uniform(20.0, 450.0), 1)
                adj[u].append((v, w))
                existing_edges.add((u, v))
                current_edges += 1

    return nodes, adj


def run_scalability_experiment(
    scales: List[int] = None,
    num_runs: int = 20,
    seed: int = 12345
) -> Dict[str, Any]:
    """
    Ejecuta el benchmark variando N y mide el tiempo de Dijkstra con los 3 tipos de heap.
    """
    if scales is None:
        scales = [10, 25, 50, 100, 250, 500, 1000]

    queue_types = ["binary_heap", "4ary_heap", "fibonacci_heap"]
    results: Dict[str, Any] = {
        "scales": scales,
        "queue_types": queue_types,
        "data": {q: [] for q in queue_types},
        "edge_counts": [],
        "operation_counts": {q: [] for q in queue_types}
    }

    print(f"[*] Iniciando pruebas de escalabilidad con {len(scales)} tamaños y {num_runs} pasadas...")

    for n in scales:
        nodes, adj = generate_synthetic_road_network(num_nodes=n, avg_degree=3.5, seed=seed + n)
        num_edges = sum(len(nbrs) for nbrs in adj.values())
        results["edge_counts"].append(num_edges)
        source = nodes[0]

        print(f"  -> N = {n:4d}, M = {num_edges:5d}:")

        # Verificamos que las tres implementaciones den las mismas distancias
        res_baseline = dijkstra_solver(nodes, adj, source, queue_type="binary_heap")
        for q in ["4ary_heap", "fibonacci_heap"]:
            res_test = dijkstra_solver(nodes, adj, source, queue_type=q)
            for v in nodes:
                d1 = res_baseline["distances"][v]
                d2 = res_test["distances"][v]
                assert abs(d1 - d2) < 1e-4 or (d1 == float('inf') and d2 == float('inf')), \
                    f"Error de corrección en N={n}, cola {q}, nodo {v}: {d1} != {d2}"

        # Medición de tiempo
        for q in queue_types:
            for _ in range(3):
                dijkstra_solver(nodes, adj, source, queue_type=q)

            times_us = []
            stats_last = None
            for _ in range(num_runs):
                t0 = time.perf_counter()
                out = dijkstra_solver(nodes, adj, source, queue_type=q)
                t1 = time.perf_counter()
                times_us.append((t1 - t0) * 1_000_000.0)
                stats_last = out["stats"]

            mean_us = sum(times_us) / len(times_us)
            variance = sum((x - mean_us) ** 2 for x in times_us) / len(times_us)
            std_us = variance ** 0.5

            results["data"][q].append({
                "nodes": n,
                "edges": num_edges,
                "mean_us": round(mean_us, 2),
                "std_us": round(std_us, 2),
                "min_us": round(min(times_us), 2),
                "max_us": round(max(times_us), 2)
            })
            results["operation_counts"][q].append(stats_last)

            print(f"     [{q:14s}] Media: {mean_us:8.2f} µs | Dec-Key: {stats_last['decrease_key_ops']}")

    return results


def export_benchmark_latex_table(results: Dict[str, Any], output_path: str) -> None:
    """Exporta los resultados a una tabla LaTeX."""
    scales = results["scales"]
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
        r"        \midrule"
    ]

    for i, n in enumerate(scales):
        edges = results["edge_counts"][i]
        bin_data = results["data"]["binary_heap"][i]
        four_data = results["data"]["4ary_heap"][i]
        fib_data = results["data"]["fibonacci_heap"][i]

        t_bin = bin_data["mean_us"]
        t_4 = four_data["mean_us"]
        t_fib = fib_data["mean_us"]

        sp_4 = f"{t_bin / t_4:.2f}x" if t_4 > 0 else "N/A"
        sp_fib = f"{t_bin / t_fib:.2f}x" if t_fib > 0 else "N/A"

        lines.append(
            f"        {n} & {edges} & {t_bin:.1f} $\\pm {bin_data['std_us']:.1f}$ & "
            f"{t_4:.1f} $\\pm {four_data['std_us']:.1f}$ & {sp_4} & "
            f"{t_fib:.1f} $\\pm {fib_data['std_us']:.1f}$ & {sp_fib} \\\\"
        )

    lines.extend([
        r"        \bottomrule",
        r"    \end{tabular*}",
        r"    \vspace{0.15cm}",
        r"    \raggedright",
        r"    \textit{Nota.} Promedio de 20 pasadas. Speedup relativo al Binary Heap.",
        r"\end{table}"
    ])

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  [OK] Tabla guardada en: {output_path}")
