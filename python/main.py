"""
Pipeline principal de ejecución - Prototipo Inicial (Fase 1: Noe Choquenaira).
Carga la red vial del Cusco, ejecuta Dijkstra para distancias e impedancias,
y valida la salida determinista.
"""
import sys
import time
import json
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from src.models.cusco_network import get_cusco_adjacency, export_network_json, NODES_CUSCO
from src.algorithms.dijkstra import dijkstra_solver

# Módulos avanzados integrados progresivamente por el equipo
try:
    from src.benchmarks.scalability_benchmark import run_scalability_experiment, export_benchmark_latex_table
except ImportError:
    run_scalability_experiment = None
    export_benchmark_latex_table = None

try:
    from src.utils.latex_exporter import (
        export_road_segments_table,
        export_trace_table,
        export_results_summary_table,
        export_preliminary_benchmark_table
    )
except ImportError:
    export_road_segments_table = None
    export_trace_table = None
    export_results_summary_table = None
    export_preliminary_benchmark_table = None

try:
    from src.visualization.generate_figures import (
        generate_network_plot,
        generate_cost_comparison_plot,
        generate_scalability_plot,
        generate_operations_breakdown_plot,
        generate_architecture_diagram,
        generate_heaps_comparison_diagram
    )
except ImportError:
    generate_network_plot = None
    generate_cost_comparison_plot = None
    generate_scalability_plot = None
    generate_operations_breakdown_plot = None
    generate_architecture_diagram = None
    generate_heaps_comparison_diagram = None


def main() -> None:
    print("=" * 70)
    print("PROYECTO ALGORITMOS AVANZADOS - GRUPO 5 (UNSAAC)")
    print("Rutas Minimas con Colas de Prioridad en Redes Viales del Cusco")
    print("=" * 70)

    # 1. Preparar directorios de salida
    PY_TABLAS = CURRENT_DIR / "results" / "tables"
    PY_FIGURES = CURRENT_DIR / "results" / "figures"
    DATA_PROCESSED = CURRENT_DIR / "data" / "processed"

    for d in [PY_TABLAS, PY_FIGURES, DATA_PROCESSED]:
        d.mkdir(parents=True, exist_ok=True)

    # 2. Cargar y exportar red vial de Cusco
    print("\n[1/3] Cargando topologia vial del Centro Historico del Cusco...")
    json_path = DATA_PROCESSED / "cusco_centro_network.json"
    export_network_json(str(json_path))
    print(f"      -> Red vial serializada en: {json_path.name}")

    nodes, adj_dist = get_cusco_adjacency(metric="distance")
    _, adj_time = get_cusco_adjacency(metric="time")
    source_node = "A"

    # 3. Ejecutar algoritmo de Dijkstra
    print(f"\n[2/3] Calculando rutas minimas desde: {source_node} ({NODES_CUSCO[source_node]})...")
    res_dist = dijkstra_solver(nodes, adj_dist, source=source_node, queue_type="binary_heap")
    res_time = dijkstra_solver(nodes, adj_time, source=source_node, queue_type="binary_heap")

    print("\n" + "-" * 70)
    print(f"{'Destino':<30} | {'Distancia':<10} | {'Tiempo':<10} | {'Ruta Optima'}")
    print("-" * 70)
    for n in nodes:
        path_str = " -> ".join(res_dist["paths"][n])
        dest_name = f"{n}: {NODES_CUSCO[n][:25]}"
        print(f"{dest_name:<30} | {res_dist['distances'][n]:>8.1f}m | {res_time['distances'][n]:>8.1f}s | {path_str}")
    print("-" * 70)

    # 4. Modulos avanzados (activados al incorporar commits de Yeni, Romario y Aldo)
    if export_road_segments_table is not None and export_trace_table is not None:
        print("\n[3/3] Exportando tablas tecnicas LaTeX...")
        export_road_segments_table([str(PY_TABLAS / "tabla_aristas_cusco.tex")])
        export_trace_table(res_dist["history"], [str(PY_TABLAS / "tabla_traza_detallada.tex")])
        if export_results_summary_table is not None:
            export_results_summary_table(res_dist, res_time, [str(PY_TABLAS / "tabla_resultados_distancias.tex")])

    if run_scalability_experiment is not None:
        print("\n[Benchmark] Modulo de escalabilidad detectado. Ejecutando experimentos...")
        scalability_results = run_scalability_experiment(scales=[10, 25, 50, 100], num_runs=5)
        with open(DATA_PROCESSED / "benchmark_results.json", "w", encoding="utf-8") as f:
            json.dump(scalability_results, f, indent=2)

    if generate_network_plot is not None:
        print("\n[Visualizacion] Generando graficos vectoriales...")
        generate_network_plot([str(PY_FIGURES / "grafo_cusco_mapa.png")])
        generate_cost_comparison_plot([str(PY_FIGURES / "comparativa_metricas.png")])

    print("\n[OK] Ejecucion completada exitosamente.")


if __name__ == "__main__":
    main()
