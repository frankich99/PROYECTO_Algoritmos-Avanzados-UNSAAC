#!/usr/bin/env python
"""Ejecuta y conserva el piloto del protocolo, sin tocar los datos canónicos."""
import argparse
import json
import math
import statistics
import sys
from pathlib import Path

PYTHON_DIR = Path(__file__).resolve().parents[1]
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

import matplotlib

matplotlib.use("Agg")

from src.benchmarks.scalability_benchmark import run_canonical_benchmark, save_benchmark
from src.generators.instance_generator import benchmark_network
from src.visualization.generate_figures import generate_pilot_plot


def main() -> None:
    parser = argparse.ArgumentParser(description="Piloto reproducible del protocolo de medición.")
    parser.add_argument("--plot-only", action="store_true", help="Regenera solo la imagen con el JSON guardado.")
    args = parser.parse_args()
    path = PYTHON_DIR / "data" / "processed" / "pilot_benchmark_results.json"
    if not args.plot_only:
        results = run_canonical_benchmark(
            sparse_scales=[100], dense_scales=[100], runs=3,
            instances_per_size=1, seed=12345, verbose=False,
        )
        for profile, data in results["profiles"].items():
            for queue in results["queue_types"]:
                row = data["data"][queue][0]
                if row["sample_count"] != len(row["samples_us"]) or row["sample_count"] != 3:
                    raise ValueError(f"Número de muestras incorrecto: {profile}, {queue}")
                if not (row["q1_us"] <= row["median_us"] <= row["q3_us"]):
                    raise ValueError(f"Cuartiles inconsistentes: {profile}, {queue}")
                if not math.isclose(statistics.median(row["samples_us"]), row["median_us"], abs_tol=0.001):
                    raise ValueError(f"Mediana inconsistente: {profile}, {queue}")
            seed = data["data"]["binary_heap"][0]["instance_seeds"][0]
            if benchmark_network(100, profile, seed).adj != benchmark_network(100, profile, seed).adj:
                raise ValueError(f"Grafo no reproducible: {profile}")
        save_benchmark(results, path)
    results = json.loads(path.read_text(encoding="utf-8"))
    figure = PYTHON_DIR.parent / "latex" / "figuras" / "piloto_mediciones.png"
    generate_pilot_plot(results, str(figure))
    print(f"{'Figura reconstruida' if args.plot_only else 'Piloto verificado: 18 muestras'}: {figure}")


if __name__ == "__main__":
    main()
