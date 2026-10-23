"""
Interfaz de línea de comandos común a todas las alternativas (Avance 5).

    python main.py list
    python main.py run      [--input F | --inline "A B 4; B C 2"] [--source A] [--queue binary|4ary|fibonacci|bellman_ford|all]
    python main.py compare  [--input F | --inline ...] [--source A]
    python main.py generate --type random|grid|road-grid ... --output F
    python main.py verify   --input F --result R
    python main.py benchmark [--scales 10 50 100] [--runs 5]
    python main.py menu     (menú interactivo para la demostración)
    python main.py demo     (pipeline completo; equivale a `python main.py` sin argumentos)

Códigos de salida: 0 = correcto, 1 = la verificación encontró errores,
2 = entrada inválida (archivo, formato, pesos negativos, origen inexistente...).
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.algorithms.registry import (METHOD_LABELS, REFERENCE_METHOD, available_methods,
                                     expand_methods, solve)
from src.algorithms.reference import NegativeCycleError
from src.io.graph_io import (GraphInstance, InvalidInstanceError, load_instance, parse_inline,
                             resolve_source)
from src.models.cusco_network import load_cusco_instance
from src.utils import presentation as pres
from src.verification.certificate import compare_results, verify_shortest_paths

PY_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Carga de la instancia (módulo de lectura reutilizado por todos los comandos)
# ---------------------------------------------------------------------------
def _add_input_args(p: argparse.ArgumentParser) -> None:
    g = p.add_mutually_exclusive_group()
    g.add_argument("--input", "-i", help="Archivo de instancia (.json, .txt, .csv). Por defecto: red del Cusco.")
    g.add_argument("--inline", help='Instancia escrita en la línea de comandos: "A B 4; B C 2; A C 9".')
    p.add_argument("--metric", choices=["time", "distance"], default="time",
                   help="Métrica para redes viales (tiempo con impedancia andina o distancia en metros).")
    p.add_argument("--source", "-s", help="Vértice origen (por defecto el de la instancia o el primero).")
    p.add_argument("--undirected", action="store_true", help="Con --inline: agregar cada arista en ambos sentidos.")


def load_from_args(args) -> GraphInstance:
    if getattr(args, "inline", None):
        spec = args.inline
        if getattr(args, "undirected", False):
            spec = "undirected; " + spec
        return parse_inline(spec)
    if getattr(args, "input", None):
        return load_instance(args.input, metric=args.metric)
    return load_cusco_instance(metric=args.metric)


def _unit(inst: GraphInstance) -> str:
    return {"time": " s", "distance": " m"}.get(inst.metric, "")


def _describe(inst: GraphInstance, source) -> str:
    return (f"Instancia '{inst.name}': |V|={inst.num_nodes}, |E|={inst.num_edges}, "
            f"métrica={inst.metric}, origen={inst.label(source)}")


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------
def cmd_list(_args) -> int:
    print("Alternativas disponibles (misma entrada, mismo formato de salida):")
    for m in available_methods():
        print(f"  {m:<15} {METHOD_LABELS[m]}")
    print("  all             Todas las colas de prioridad (binary, 4ary, fibonacci)")
    return 0


def cmd_run(args, inst: Optional[GraphInstance] = None) -> int:
    inst = inst or load_from_args(args)
    source = resolve_source(inst, args.source)
    methods = expand_methods(args.queue)
    if args.target is not None:
        target = resolve_source(inst, args.target)
    else:
        target = None
    print(_describe(inst, source))

    results: Dict[str, Dict[str, Any]] = {}
    exit_code = 0
    for m in methods:
        res = solve(inst, source, m, record_trace=args.trace)
        results[m] = res
        print(f"\n=== {METHOD_LABELS[m]} ===")
        if target is not None:
            path = res["paths"][target]
            print(f"Ruta {source} -> {target}: {' -> '.join(map(str, path)) if path else '(inalcanzable)'}"
                  f" | costo = {pres.fmt_num(res['distances'][target])}{_unit(inst)}")
        else:
            print(pres.result_table(inst, res, _unit(inst)))
        print("Operaciones:", pres.stats_line(res))
        if args.trace and res["history"]:
            print("Traza:\n" + pres.trace_text(inst, res))
        cert = verify_shortest_paths(inst.nodes, inst.adj, source, res)
        if cert["ok"]:
            print(f"Verificación: OK ({cert['checked_edges']} aristas sin relajación pendiente, "
                  f"{cert['checked_paths']} rutas con costo = distancia)")
        else:
            exit_code = 1
            print("Verificación: FALLÓ")
            for v in cert["violations"]:
                print("  -", v)

    if len(results) > 1:
        cmp = compare_results(inst.adj, inst.nodes, results)
        _print_comparison(cmp)
        if not cmp["distances_equal"]:
            exit_code = 1

    if args.output:
        payload = ({"results": {m: pres.result_to_dict(inst, r) for m, r in results.items()}}
                   if len(results) > 1 else pres.result_to_dict(inst, results[methods[0]]))
        out = pres.save_results_json(args.output, payload)
        print(f"\nResultado guardado en {out}")
    return exit_code


def _print_comparison(cmp: Dict[str, Any]) -> None:
    print(f"\n=== Comparación de alternativas (base: {cmp['baseline']}) ===")
    print(f"Distancias: {cmp['verdict']}")
    for m in cmp["distance_mismatches"]:
        print("  ERROR:", m)
    if cmp["alternative_optimal_paths"]:
        print("Rutas distintas con el mismo costo (empates; propiedad esperada, no es error):")
        for t in cmp["alternative_optimal_paths"]:
            others = {k: v for k, v in t.items() if k not in ("node", "cost", "same_cost")}
            desc = " | ".join(f"{k}: {'->'.join(map(str, v))}" for k, v in others.items())
            print(f"  {t['node']} (costo {pres.fmt_num(t['cost'])}): {desc}")
    else:
        print("Rutas: idénticas en todas las alternativas.")
    ops = cmp["operation_counts"]
    keys = sorted({k for d in ops.values() for k in d})
    rows = [[name] + [ops[name].get(k, "-") for k in keys] for name in ops]
    print("Contadores de operaciones (difieren por diseño de cada estructura):")
    print(pres.table(["método"] + keys, rows))


def cmd_compare(args, inst: Optional[GraphInstance] = None) -> int:
    inst = inst or load_from_args(args)
    source = resolve_source(inst, args.source)
    print(_describe(inst, source))
    methods = expand_methods("all")
    results = {m: solve(inst, source, m) for m in methods}
    ref = solve(inst, source, REFERENCE_METHOD)
    results[REFERENCE_METHOD] = ref

    header = ["Destino"] + methods + [REFERENCE_METHOD]
    rows = [[inst.label(v)[:28]] + [pres.fmt_num(results[m]["distances"][v]) for m in header[1:]]
            for v in inst.nodes]
    print("\nDistancias por alternativa:")
    print(pres.table(header, rows))

    cmp = compare_results(inst.adj, inst.nodes, results, reference=REFERENCE_METHOD)
    _print_comparison(cmp)

    certs = {m: verify_shortest_paths(inst.nodes, inst.adj, source, results[m]) for m in results}
    print("\nCertificado de optimalidad por alternativa:")
    for m, c in certs.items():
        print(f"  {m:<15} {'OK' if c['ok'] else 'FALLÓ: ' + '; '.join(c['violations'][:3])}")
    print("\nTiempo de una ejecución (ms): " + ", ".join(f"{m}={r['elapsed_ms']:.3f}" for m, r in results.items()))

    if args.output:
        payload = {"instance": inst.name, "source": source, "comparison": cmp,
                   "certificates": certs,
                   "results": {m: pres.result_to_dict(inst, r) for m, r in results.items()}}
        print(f"Reporte guardado en {pres.save_results_json(args.output, payload)}")
    ok = cmp["distances_equal"] and all(c["ok"] for c in certs.values())
    return 0 if ok else 1


def cmd_generate(args) -> int:
    from src.generators.instance_generator import grid_network, random_road_network, road_grid_network
    if args.type == "random":
        inst = random_road_network(args.nodes, avg_degree=args.degree, seed=args.seed)
    elif args.type == "grid":
        inst = grid_network(args.rows, args.cols, weight_mode=args.weights, seed=args.seed)
    else:
        inst = road_grid_network(args.rows, args.cols, seed=args.seed, metric=args.metric)
    out = inst.save_json(args.output)
    print(f"Instancia '{inst.name}' generada: |V|={inst.num_nodes}, |E|={inst.num_edges} -> {out}")
    return 0


def cmd_verify(args) -> int:
    inst = load_from_args(args)
    res = pres.load_result_json(args.result, inst)
    source = resolve_source(inst, res["source"])
    cert = verify_shortest_paths(inst.nodes, inst.adj, source, res)
    print(_describe(inst, source))
    print(f"Resultado verificado: {args.result} ({res.get('algorithm')}/{res.get('queue')})")
    if cert["ok"]:
        print(f"OK: certificado válido ({cert['checked_edges']} aristas, {cert['checked_paths']} rutas).")
        return 0
    print("FALLÓ:")
    for v in cert["violations"]:
        print("  -", v)
    return 1


def cmd_benchmark(args) -> int:
    from src.benchmarks.scalability_benchmark import export_benchmark_latex_table, run_scalability_experiment
    res = run_scalability_experiment(scales=args.scales, num_runs=args.runs, seed=args.seed)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pres.save_results_json(str(out_dir / "benchmark_results.json"), res)
    export_benchmark_latex_table(res, str(out_dir / "tabla_benchmark_escalabilidad.tex"))
    try:
        from src.visualization.generate_figures import generate_scalability_plot
        generate_scalability_plot(res, [str(out_dir / "benchmark_escalabilidad.png")])
    except Exception as exc:  # matplotlib opcional
        print(f"(Figura no generada: {exc})")
    print(f"Resultados en {out_dir}")
    return 0


def cmd_graphviz(args) -> int:
    from src.visualization.generate_figures import export_graphviz_dot
    out_dir = PY_DIR / "results" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = args.output or str(out_dir / ("ruta_optima_cusco.dot" if args.target else "red_vial_cusco.dot"))

    highlight = None
    if args.target:
        from src.models.cusco_network import load_cusco_instance
        from src.algorithms.registry import solve
        inst = load_cusco_instance(args.metric)
        source = args.source or "A"
        res = solve(inst, source, "binary_heap")
        highlight = res["paths"].get(args.target, [])
        if not highlight:
            print(f"[AVISO] No hay ruta alcanzable hacia el destino '{args.target}'.")

    export_graphviz_dot([out_file], metric=args.metric, highlight_path=highlight)
    print(f"Especificación Graphviz exportada exitosamente en: {out_file}")
    if highlight:
        print(f"Ruta óptima resaltada hacia {args.target}: {' -> '.join(highlight)}")
    print("Nota: Puedes visualizar este archivo con la extensión Graphviz de VS Code o en https://dreampuf.github.io/GraphvizOnline/")
    return 0


def cmd_menu(_args, input_fn=input) -> int:
    """Menú interactivo: pensado para la demostración en vivo sin recordar parámetros."""
    inst: GraphInstance = load_cusco_instance("time")
    while True:
        print("\n--- Menú (instancia actual: %s, |V|=%d, |E|=%d) ---" % (inst.name, inst.num_nodes, inst.num_edges))
        print("1) Cargar red del Cusco (tiempo)   2) Cargar red del Cusco (distancia)")
        print("3) Cargar archivo de instancia      4) Escribir instancia en línea")
        print("5) Generar instancia aleatoria      6) Ejecutar una alternativa")
        print("7) Comparar todas las alternativas  8) Exportar grafo a Graphviz (.dot)")
        print("0) Salir")
        op = input_fn("Opción: ").strip()
        try:
            if op == "0":
                return 0
            if op in ("1", "2"):
                inst = load_cusco_instance("time" if op == "1" else "distance")
            elif op == "3":
                inst = load_instance(input_fn("Ruta del archivo: ").strip(),
                                     metric=input_fn("Métrica [time/distance] (time): ").strip() or "time")
            elif op == "4":
                inst = parse_inline(input_fn('Aristas "u v w; u v w": '))
            elif op == "5":
                from src.generators.instance_generator import random_road_network
                n = int(input_fn("Número de vértices: "))
                seed = int(input_fn("Semilla (42): ") or 42)
                inst = random_road_network(n, seed=seed)
            elif op in ("6", "7"):
                src_txt = input_fn(f"Origen ({inst.default_source or inst.nodes[0]}): ").strip() or None
                ns = argparse.Namespace(input=None, inline=None, metric=inst.metric, source=src_txt,
                                        undirected=False, queue="all", target=None, trace=False, output=None)
                if op == "6":
                    ns.queue = input_fn("Alternativa [binary/4ary/fibonacci/bellman_ford/all] (binary): ").strip() or "binary"
                    ns.trace = input_fn("¿Mostrar traza? [s/N]: ").strip().lower() == "s"
                (cmd_compare if op == "7" else cmd_run)(ns, inst)
            elif op == "8":
                tgt = input_fn("Destino a resaltar [B/C/D/E/F] (E): ").strip().upper() or "E"
                ns = argparse.Namespace(metric=inst.metric, source="A", target=tgt, output=None)
                cmd_graphviz(ns)
            else:
                print("Opción no válida.")
        except (InvalidInstanceError, ValueError) as exc:
            print(f"[ERROR] Entrada inválida: {exc}")


def cmd_demo(_args) -> int:
    from main import run_demo_pipeline
    run_demo_pipeline()
    return 0


# ---------------------------------------------------------------------------
def cmd_astar(args) -> int:
    from src.models.cusco_network import load_cusco_instance, NODES_CUSCO
    from src.algorithms.dijkstra import dijkstra_solver
    from src.algorithms.a_star import a_star_solver
    
    inst = load_from_args(args)
    source = resolve_source(inst, args.source)
    target = getattr(args, "target", None)
    if not target:
        target = "E" if "E" in inst.nodes else inst.nodes[-1]
    
    print(_describe(inst, source))
    print(f"Búsqueda Heurística A* (A-Star) hacia destino objetivo: {inst.label(target)}")
    
    # Resolver con Dijkstra (SSSP tradicional)
    dijk_res = dijkstra_solver(inst.nodes, inst.adj, source, queue_type=args.queue)
    dijk_dist = dijk_res["distances"][target]
    dijk_path = " -> ".join(dijk_res["paths"][target])
    
    # Resolver con A* (Búsqueda focalizada con heurística admisible)
    astar_res = a_star_solver(inst.nodes, inst.adj, source, target, queue_type=args.queue, metric=inst.metric)
    astar_dist = astar_res["target_distance"]
    astar_path = " -> ".join(astar_res["path"])
    
    u = _unit(inst)
    print("\nComparativa Dijkstra vs A* (A-Star):")
    rows = [
        ["Algoritmo", "Nodos Expandidos", "Relajaciones", "Costo Óptimo", "Ruta Reconstruida"],
        ["Dijkstra Canónico", str(len(inst.nodes)), str(dijk_res["stats"].get("relax_attempts", "-")), f"{dijk_dist:.2f}{u}", dijk_path],
        ["A* Heurístico", str(astar_res["stats"]["expanded_nodes"]), str(astar_res["stats"]["relax_attempts"]), f"{astar_dist:.2f}{u}", astar_path]
    ]
    print(pres.table(rows[0], rows[1:]))
    
    poda_pct = (1.0 - (astar_res["stats"]["expanded_nodes"] / len(inst.nodes))) * 100.0
    print(f"\nEficiencia de Poda A*: {poda_pct:.1f}% de nodos no necesitaron ser expandidos.")
    print(f"Optimalidad: {'GARANTIZADA (Costos idénticos)' if abs(dijk_dist - astar_dist) < 1e-6 else 'Diferencia detectada'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="Rutas mínimas con colas de prioridad intercambiables (Grupo 5 - UNSAAC).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="Lista las alternativas disponibles").set_defaults(func=cmd_list)

    p = sub.add_parser("run", help="Ejecuta una o varias alternativas sobre una instancia")
    _add_input_args(p)
    p.add_argument("--queue", "-q", default="binary_heap",
                   help="binary_heap | 4ary_heap | fibonacci_heap | bellman_ford | all | lista separada por comas")
    p.add_argument("--target", "-t", help="Mostrar solo la ruta hacia este destino")
    p.add_argument("--trace", action="store_true", help="Imprimir la traza paso a paso")
    p.add_argument("--output", "-o", help="Guardar el resultado en JSON (verificable con `verify`)")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("compare", help="Ejecuta todas las colas + referencia y compara resultados")
    _add_input_args(p)
    p.add_argument("--output", "-o", help="Guardar el reporte de comparación en JSON")
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("generate", help="Genera una instancia sintética reproducible")
    p.add_argument("--type", choices=["random", "grid", "road-grid"], default="random")
    p.add_argument("--nodes", type=int, default=50)
    p.add_argument("--degree", type=float, default=3.5)
    p.add_argument("--rows", type=int, default=5)
    p.add_argument("--cols", type=int, default=5)
    p.add_argument("--weights", choices=["unit", "random"], default="unit")
    p.add_argument("--metric", choices=["time", "distance"], default="time")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--output", "-o", required=True)
    p.set_defaults(func=cmd_generate)

    p = sub.add_parser("verify", help="Verifica un resultado JSON contra su instancia (sin reejecutar)")
    _add_input_args(p)
    p.add_argument("--result", "-r", required=True)
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("benchmark", help="Benchmark de escalabilidad de las tres colas")
    p.add_argument("--scales", type=int, nargs="+", default=[10, 50, 100, 500, 1000])
    p.add_argument("--runs", type=int, default=5)
    p.add_argument("--seed", type=int, default=12345)
    p.add_argument("--output-dir", default=str(PY_DIR / "results" / "benchmark"))
    p.set_defaults(func=cmd_benchmark)

    p = sub.add_parser("graphviz", help="Exporta la red vial o ruta óptima a especificación Graphviz (.dot)")
    p.add_argument("--metric", choices=["time", "distance"], default="time", help="Métrica de impedancia")
    p.add_argument("--source", "-s", default="A", help="Nodo origen")
    p.add_argument("--target", "-t", help="Nodo destino para resaltar el camino óptimo")
    p.add_argument("--output", "-o", help="Ruta de salida del archivo .dot")
    p.set_defaults(func=cmd_graphviz)

    p = sub.add_parser("astar", help="Ejecuta el Algoritmo A* y lo compara contra Dijkstra")
    _add_input_args(p)
    p.add_argument("--target", "-t", default="E", help="Vértice objetivo")
    p.add_argument("--queue", "-q", default="binary_heap", help="binary_heap | 4ary_heap | fibonacci_heap")
    p.set_defaults(func=cmd_astar)

    sub.add_parser("menu", help="Menú interactivo").set_defaults(func=cmd_menu)
    sub.add_parser("demo", help="Pipeline completo de demostración").set_defaults(func=cmd_demo)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except NegativeCycleError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    except (InvalidInstanceError, ValueError) as exc:
        print(f"[ERROR] Entrada inválida: {exc}", file=sys.stderr)
        return 2
    except KeyError as exc:
        print(f"[ERROR] Resultado o instancia incompleta: falta {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"[ERROR] JSON mal formado: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"[ERROR] Archivo no encontrado: {exc.filename}", file=sys.stderr)
        return 2
