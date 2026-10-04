"""
Exportador de tablas LaTeX.
"""
from pathlib import Path
from typing import List, Dict, Any
from src.utils.cost_model import CuscoCostModel


def export_road_segments_table(output_paths: List[str]) -> None:
    """Exporta tabla de tramos."""
    from src.models.cusco_network import ROAD_SEGMENTS
    lines = [
        r"\begin{table}[H]",
        r"    \centering",
        r"    \fontsize{10}{12.5}\selectfont",
        r"    \setlength{\tabcolsep}{4pt}",
        r"    \caption{Tramos viales, distancias y tiempos.}",
        r"    \label{tab:road_segments}",
        r"    \begin{tabular}{@{}cclrrr@{}}",
        r"        \toprule",
        r"        \textbf{Origen} & \textbf{Destino} & \textbf{Vía} & \textbf{Dist. (m)} & \textbf{Pend. (\%)} & \textbf{Tiempo (s)} \\",
        r"        \midrule"
    ]

    for seg in ROAD_SEGMENTS:
        t_sec = CuscoCostModel.calculate_cost(seg, metric='time')
        lines.append(f"        {seg.origin} & {seg.destination} & {seg.street_name} & {seg.length_m:.0f} & {seg.gradient_pct:+.1f} & {t_sec:.1f} \\\\")

    lines.extend([
        r"        \bottomrule",
        r"    \end{tabular}",
        r"    \vspace{0.15cm}",
        r"    \raggedright",
        r"    \textit{Nota.} Tiempo estimado con $\alpha = 2.5$.",
        r"\end{table}"
    ])

    content = "\n".join(lines) + "\n"
    for p in output_paths:
        out = Path(p)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(content)


def export_trace_table(history: List[Dict[str, Any]], output_paths: List[str]) -> None:
    """Exporta traza de Dijkstra."""
    from src.models.cusco_network import NODES_CUSCO
    nodes = list(NODES_CUSCO.keys())
    header_nodes = " & ".join([f"\\textbf{{{n}}}" for n in nodes])
    
    lines = [
        r"\begin{table}[H]",
        r"    \centering",
        r"    \fontsize{10}{12.5}\selectfont",
        r"    \setlength{\tabcolsep}{3pt}",
        r"    \caption{Traza de distancias y predecesores.}",
        r"    \label{tab:traza_dijkstra}",
        f"    \\begin{{tabular}}{{@{{}}ccl{'c' * len(nodes)}@{{}}}}",
        r"        \toprule",
        f"        \\textbf{{Iter.}} & \\textbf{{Nodo $u$}} & \\textbf{{Acción}} & {header_nodes} \\\\",
        r"        \midrule"
    ]

    init_cells = " & ".join(["0 / -" if n == "A" else r"$\infty$ / -" for n in nodes])
    lines.append(f"        $k=0$ & Inicial & Encolar & {init_cells} \\\\")

    closed_nodes = set()
    for step in history:
        k = step["iteration"]
        u = step["extracted_node"]
        d_u = step["extracted_dist"]
        closed_nodes.add(u)

        rel_notes = []
        for r in step["relaxations"]:
            if r["relaxed"]:
                rel_notes.append(f"Relaja {r['destination']} ({r['new_dist']:.0f})")
            else:
                rel_notes.append(f"Descarta {r['destination']}")
        action_text = ", ".join(rel_notes) if rel_notes else "Sin aristas"

        row_cells = []
        for n in nodes:
            dist_val = step["current_distances"].get(n, float('inf'))
            prev_val = step["current_predecessors"].get(n) or "-"
            d_str = f"{dist_val:.0f}" if dist_val != float('inf') else r"$\infty$"
            cell_text = f"{d_str} / {prev_val}"
            if n in closed_nodes:
                cell_text = f"\\textbf{{{d_str}}} / {prev_val}"
            row_cells.append(cell_text)

        cells_joined = " & ".join(row_cells)
        lines.append(f"        $k={k}$ & {u} ($d={d_u:.0f}$) & {action_text} & {cells_joined} \\\\")

    lines.extend([
        r"        \bottomrule",
        r"    \end{tabular}",
        r"    \vspace{0.15cm}",
        r"    \raggedright",
        r"    \textit{Nota.} Formato: $d[v] / \pi[v]$. Negrita: cerrados.",
        r"\end{table}"
    ])

    content = "\n".join(lines) + "\n"
    for p in output_paths:
        out = Path(p)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(content)


def export_results_summary_table(
    dist_results: Dict[str, Any],
    time_results: Dict[str, Any],
    output_paths: List[str]
) -> None:
    """Exporta resultados de distancias y tiempos."""
    from src.models.cusco_network import NODES_CUSCO
    nodes = list(NODES_CUSCO.keys())

    lines = [
        r"\begin{table}[H]",
        r"    \centering",
        r"    \fontsize{10}{12.5}\selectfont",
        r"    \setlength{\tabcolsep}{4pt}",
        r"    \caption{Distancias y tiempos óptimos.}",
        r"    \label{tab:resultados_distancias}",
        r"    \begin{tabularx}{\textwidth}{@{}clrrX@{}}",
        r"        \toprule",
        r"        \textbf{Nodo} & \textbf{Intersección} & \textbf{Dist. (m)} & \textbf{Tiempo (s)} & \textbf{Ruta} \\",
        r"        \midrule"
    ]

    for node in nodes:
        name = NODES_CUSCO[node]
        d_val = dist_results["distances"][node]
        t_val = time_results["distances"][node]
        path_str = " -> ".join(dist_results["paths"][node])
        lines.append(f"        \\textbf{{{node}}} & {name} & {d_val:.1f} & {t_val:.1f} & \\texttt{{{path_str}}} \\\\")

    lines.extend([
        r"        \bottomrule",
        r"    \end{tabularx}",
        r"    \vspace{0.15cm}",
        r"    \raggedright",
        r"    \textit{Nota.} Origen: A.",
        r"\end{table}"
    ])

    content = "\n".join(lines) + "\n"
    for p in output_paths:
        out = Path(p)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(content)


def export_preliminary_benchmark_table(
    bench_data: List[Dict[str, Any]],
    output_paths: List[str]
) -> None:
    """Exporta benchmark de Dijkstra."""
    lines = [
        r"\begin{table}[H]",
        r"    \centering",
        r"    \fontsize{10}{12.5}\selectfont",
        r"    \setlength{\tabcolsep}{4pt}",
        r"    \caption{Benchmark de colas de prioridad.}",
        r"    \label{tab:benchmark_preliminar}",
        r"    \begin{tabularx}{\textwidth}{@{}lrrrX@{}}",
        r"        \toprule",
        r"        \textbf{Cola} & \textbf{Tiempo ($\mu s$)} & \textbf{Desv. ($\mu s$)} & \textbf{Speedup} & \textbf{Observaciones} \\",
        r"        \midrule"
    ]

    base_time = bench_data[0]["mean_us"]
    for row in bench_data:
        q_name = row["name"]
        mean_t = row["mean_us"]
        std_t = row["std_us"]
        obs = row["obs"]
        speedup = f"{base_time / mean_t:.2f}x" if row["name"] != bench_data[0]["name"] else r"\textbf{1.00x}"
        name_fmt = f"\\textbf{{{q_name}}}" if row["name"] == bench_data[0]["name"] else q_name
        lines.append(f"        {name_fmt} & {mean_t:.1f} & $\\pm {std_t:.1f}$ & {speedup} & {obs} \\\\")

    lines.extend([
        r"        \bottomrule",
        r"    \end{tabularx}",
        r"    \vspace{0.15cm}",
        r"    \raggedright",
        r"    \textit{Nota.} N=6, 10000 repeticiones.",
        r"\end{table}"
    ])

    content = "\n".join(lines) + "\n"
    for p in output_paths:
        out = Path(p)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(content)
