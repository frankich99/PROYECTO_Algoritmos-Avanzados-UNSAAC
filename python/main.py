"""
Punto de entrada del sistema.

    python main.py                 -> pipeline completo de demostración
    python main.py <comando> ...   -> interfaz común (ver `python main.py --help`)

Pipeline de demostración:
  1. Carga y serializa la red vial del Centro Histórico del Cusco.
  2. Ejecuta Dijkstra con las tres colas (binary, 4-ary, Fibonacci) y la
     referencia Bellman-Ford, para distancia y tiempo.
  3. Verifica cada salida (certificado de optimalidad) y la equivalencia.
  4. Exporta tablas LaTeX, un benchmark pequeño y figuras.
"""
import json
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from src.algorithms.registry import REFERENCE_METHOD, available_methods, solve
from src.models.cusco_network import NODES_CUSCO, export_network_json, load_cusco_instance
from src.utils import presentation as pres
from src.verification.certificate import compare_results, verify_shortest_paths


def run_demo_pipeline(run_benchmark: bool = True, make_figures: bool = True) -> int:
    print("=" * 74)
    print("PROYECTO ALGORITMOS AVANZADOS - GRUPO 5 (UNSAAC)")
    print("Rutas mínimas con colas de prioridad en la red vial del Cusco")
    print("=" * 74)

    tables_dir = CURRENT_DIR / "results" / "tables"
    figures_dir = CURRENT_DIR / "results" / "figures"
    data_dir = CURRENT_DIR / "data" / "processed"
    for d in (tables_dir, figures_dir, data_dir):
        d.mkdir(parents=True, exist_ok=True)

    print("\n[1/4] Red vial del Centro Histórico")
    json_path = data_dir / "cusco_centro_network.json"
    export_network_json(str(json_path))
    print(f"      serializada en {json_path.relative_to(CURRENT_DIR)}")

    inst_dist = load_cusco_instance("distance")
    inst_time = load_cusco_instance("time")
    source = "A"
    methods = available_methods()      # 3 colas + bellman_ford

    print(f"\n[2/4] Rutas mínimas desde {source} ({NODES_CUSCO[source]}) con {len(methods)} alternativas")
    res_dist = {m: solve(inst_dist, source, m, record_trace=True) for m in methods}
    res_time = {m: solve(inst_time, source, m, record_trace=True) for m in methods}

    base_d, base_t = res_dist["binary_heap"], res_time["binary_heap"]
    rows = []
    for n in inst_dist.nodes:
        rows.append([f"{n}: {NODES_CUSCO[n][:24]}", pres.fmt_num(base_d["distances"][n], 1) + " m",
                     pres.fmt_num(base_t["distances"][n], 1) + " s",
                     " -> ".join(base_d["paths"][n]), " -> ".join(base_t["paths"][n])])
    print(pres.table(["Destino", "Distancia", "Tiempo", "Ruta (distancia)", "Ruta (tiempo)"], rows))

    print("\n[3/4] Verificación")
    all_ok = True
    for label, inst, res in (("distancia", inst_dist, res_dist), ("tiempo", inst_time, res_time)):
        cmp = compare_results(inst.adj, inst.nodes, res, reference=REFERENCE_METHOD)
        certs = {m: verify_shortest_paths(inst.nodes, inst.adj, source, r)["ok"] for m, r in res.items()}
        ok = cmp["distances_equal"] and all(certs.values())
        all_ok &= ok
        print(f"      métrica {label:<9}: distancias {cmp['verdict']}; certificados "
              + ", ".join(f"{m}={'OK' if c else 'FALLÓ'}" for m, c in certs.items()))
    for m in methods:
        print(f"      {m:<15} {pres.stats_line(res_dist[m])}")

    print("\n[4/4] Exportación de tablas, benchmark y figuras")
    try:
        from src.utils.latex_exporter import (export_results_summary_table, export_road_segments_table,
                                              export_trace_table)
        export_road_segments_table([str(tables_dir / "tabla_aristas_cusco.tex")])
        export_trace_table(base_d["history"], [str(tables_dir / "tabla_traza_detallada.tex")])
        export_results_summary_table(base_d, base_t, [str(tables_dir / "tabla_resultados_distancias.tex")])
        print(f"      tablas LaTeX en {tables_dir.relative_to(CURRENT_DIR)}")
    except Exception as exc:
        print(f"      (tablas no exportadas: {exc})")

    bench = None
    if run_benchmark:
        from src.benchmarks.scalability_benchmark import export_benchmark_latex_table, run_scalability_experiment
        bench = run_scalability_experiment(scales=[10, 25, 50, 100, 250], num_runs=5)
        with open(data_dir / "benchmark_results.json", "w", encoding="utf-8") as f:
            json.dump(bench, f, indent=2)
        export_benchmark_latex_table(bench, str(tables_dir / "tabla_benchmark_escalabilidad.tex"))

    if make_figures:
        try:
            from src.visualization.generate_figures import (generate_cost_comparison_plot, generate_network_plot,
                                                            generate_operations_breakdown_plot,
                                                            generate_scalability_plot)
            generate_network_plot([str(figures_dir / "grafo_cusco_mapa.png")])
            generate_cost_comparison_plot([str(figures_dir / "comparativa_metricas.png")])
            if bench is not None:
                generate_scalability_plot(bench, [str(figures_dir / "benchmark_escalabilidad.png")])
                generate_operations_breakdown_plot(bench, [str(figures_dir / "desglose_operaciones.png")])
            print(f"      figuras en {figures_dir.relative_to(CURRENT_DIR)}")
        except Exception as exc:  # matplotlib/networkx opcionales
            print(f"      (figuras no generadas: {exc})")

    print("\n[OK] Ejecución completada." if all_ok else "\n[ATENCIÓN] La verificación encontró diferencias.")
    return 0 if all_ok else 1


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        return run_demo_pipeline()
    from src.cli import main as cli_main
    return cli_main(argv)


if __name__ == "__main__":
    sys.exit(main())
