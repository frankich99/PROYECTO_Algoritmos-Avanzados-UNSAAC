#!/usr/bin/env python
"""Regenera los resultados canónicos, las tablas y las figuras del informe.

El protocolo por defecto coincide con el del informe: 15 repeticiones por
instancia, tres instancias por escala y semilla 12345. El caso aplicado usa el
snapshot OSM y el snapshot meteorológico versionados; no consulta la red si
ambos existen.

Ejemplos:
    python scripts/reproduce_canonical.py
    python scripts/reproduce_canonical.py --skip-benchmark --skip-applied
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PYTHON_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = PYTHON_DIR.parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from src.benchmarks.applied_analysis import (  # noqa: E402
    export_applied_latex,
    run_applied_analysis,
    save_applied_analysis,
)
from src.benchmarks.scalability_benchmark import (  # noqa: E402
    export_benchmark_latex_table,
    export_benchmark_summary_table,
    run_canonical_benchmark,
    save_benchmark,
)
from src.io.osm_loader import load_snapshot as load_osm_snapshot  # noqa: E402
from src.visualization.generate_figures import (  # noqa: E402
    generate_operations_breakdown_plot,
    generate_osm_route_plot,
    generate_scalability_plot,
)

DATA_DIR = PYTHON_DIR / "data" / "processed"
DOCUMENT_DIR = REPO_ROOT / "documento"
TABLES_DIR = DOCUMENT_DIR / "tablas"
FIGURES_DIR = DOCUMENT_DIR / "figuras"
BENCHMARK_PATH = DATA_DIR / "benchmark_results.json"
APPLIED_PATH = DATA_DIR / "applied_results.json"
OSM_PATH = DATA_DIR / "cusco_osm_drive.json"
WEATHER_PATH = DATA_DIR / "weather_cusco.json"


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Falta {path}. Ejecute primero la fase correspondiente.")
    return json.loads(path.read_text(encoding="utf-8"))


def _require(path: Path, purpose: str) -> None:
    if not path.exists():
        raise SystemExit(f"Falta {path}, necesario para {purpose}.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Regenera el benchmark canónico, el caso OSM, las tablas y las figuras."
    )
    parser.add_argument("--runs", type=int, default=15, help="Repeticiones por instancia (default: 15).")
    parser.add_argument("--instances", type=int, default=3, help="Instancias por escala (default: 3).")
    parser.add_argument("--seed", type=int, default=12345, help="Semilla base (default: 12345).")
    parser.add_argument("--applied-runs", type=int, default=30, help="Repeticiones en la consulta OSM (default: 30).")
    parser.add_argument("--skip-benchmark", action="store_true", help="Reutiliza benchmark_results.json.")
    parser.add_argument("--skip-applied", action="store_true", help="Reutiliza applied_results.json.")
    parser.add_argument("--skip-tables", action="store_true", help="No reescribe las tablas LaTeX.")
    parser.add_argument("--skip-figures", action="store_true", help="No reescribe las figuras PNG.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.runs < 1 or args.instances < 1 or args.applied_runs < 1:
        raise SystemExit("Los conteos de repeticiones e instancias deben ser positivos.")

    if args.skip_benchmark:
        results = _load_json(BENCHMARK_PATH)
        print(f"[1/4] Benchmark reutilizado: {BENCHMARK_PATH.relative_to(REPO_ROOT)}")
    else:
        print("[1/4] Ejecutando benchmark canónico...")
        results = run_canonical_benchmark(
            runs=args.runs,
            instances_per_size=args.instances,
            seed=args.seed,
            verbose=True,
        )
        save_benchmark(results, BENCHMARK_PATH)
        print(f"      escrito en {BENCHMARK_PATH.relative_to(REPO_ROOT)}")

    if args.skip_applied:
        applied = _load_json(APPLIED_PATH)
        print(f"[2/4] Caso aplicado reutilizado: {APPLIED_PATH.relative_to(REPO_ROOT)}")
    else:
        _require(OSM_PATH, "el caso aplicado")
        _require(WEATHER_PATH, "la sensibilidad meteorológica")
        print("[2/4] Ejecutando el caso aplicado sobre el snapshot OSM...")
        applied = run_applied_analysis(OSM_PATH, WEATHER_PATH, runs=args.applied_runs)
        save_applied_analysis(applied, APPLIED_PATH)
        print(f"      escrito en {APPLIED_PATH.relative_to(REPO_ROOT)}")

    if args.skip_tables:
        print("[3/4] Tablas omitidas.")
    else:
        TABLES_DIR.mkdir(parents=True, exist_ok=True)
        export_benchmark_latex_table(results, str(TABLES_DIR / "benchmark_canonico.tex"))
        export_benchmark_summary_table(results, str(TABLES_DIR / "sintesis_colas.tex"), applied)
        export_applied_latex(applied, TABLES_DIR / "caso_osm.tex")
        print(f"[3/4] Tablas escritas en {TABLES_DIR.relative_to(REPO_ROOT)}")

    if args.skip_figures:
        print("[4/4] Figuras omitidas.")
    else:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        if "sparse" in results.get("profiles", {}):
            generate_operations_breakdown_plot(
                results, [str(FIGURES_DIR / "operaciones_canonicas.png")]
            )
        generate_scalability_plot(results, [str(FIGURES_DIR / "benchmark_canonico.png")])
        _require(OSM_PATH, "la figura de la ruta")
        instance = load_osm_snapshot(OSM_PATH, metric="time")
        generate_osm_route_plot(
            instance,
            applied["query"]["path"],
            [str(FIGURES_DIR / "ruta_osm_cusco.png")],
        )
        print(f"[4/4] Figuras escritas en {FIGURES_DIR.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
