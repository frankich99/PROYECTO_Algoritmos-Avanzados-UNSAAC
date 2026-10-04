"""
Generador de figuras científicas para el informe LaTeX y el análisis experimental.
Produce gráficos vectoriales/rasterizados en alta resolución (300 DPI) bajo paleta accesible.
Grupo 5 - Algoritmos Avanzados (UNSAAC)
"""
from pathlib import Path
from typing import Dict, Any, List
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Asegurar importaciones locales
from src.models.cusco_network import NODES_CUSCO, ROAD_SEGMENTS
from src.utils.cost_model import CuscoCostModel


def generate_network_plot(output_paths: List[str]) -> None:
    """Genera la visualización gráfica de la topología vial del Centro Histórico del Cusco."""
    pos = {
        "A": (0.0, 2.0),     # Plaza Mayor
        "B": (-2.8, 0.8),    # Plaza Regocijo
        "C": (2.8, 0.5),     # Qorikancha
        "D": (-4.2, -1.8),   # Plaza San Francisco
        "E": (-1.8, -3.5),   # Mercado San Pedro
        "F": (3.5, -2.5)     # Limacpampa
    }

    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    ax.set_facecolor('#f8fafc')

    for seg in ROAD_SEGMENTS:
        x1, y1 = pos[seg.origin]
        x2, y2 = pos[seg.destination]

        # Flecha dirigida
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(
                arrowstyle="-|>", color="#1e3a8a", lw=2.2,
                shrinkA=22, shrinkB=22, mutation_scale=18
            )
        )

        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        cost_time = CuscoCostModel.calculate_cost(seg, metric='time')
        label = f"{int(seg.length_m)}m\n({cost_time:.1f}s, {seg.gradient_pct:+.1f}%)"
        ax.text(
            mid_x, mid_y, label,
            fontsize=8, ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#cbd5e1", alpha=0.95),
            fontweight='bold', color="#0f172a"
        )

    for node_id, (x, y) in pos.items():
        color = "#10b981" if node_id == "A" else "#2563eb"
        circle = plt.Circle((x, y), 0.38, color=color, ec="#0f172a", lw=2.2, zorder=4)
        ax.add_patch(circle)
        ax.text(x, y, node_id, color="white", fontsize=14, weight="bold", ha="center", va="center", zorder=5)

        name = NODES_CUSCO[node_id]
        offset_y = 0.58 if y >= 0 else -0.58
        ax.text(x, y + offset_y, name, fontsize=9.5, weight="bold", ha="center", va="center", color="#0f172a",
                bbox=dict(boxstyle="round,pad=0.15", fc="#f1f5f9", ec="none", alpha=0.8))

    ax.set_xlim(-5.5, 5.0)
    ax.set_ylim(-4.8, 3.2)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Red Vial Dirigida: Centro Histórico del Cusco\n(Distancias, Tiempos de Emergencia y Pendientes)",
                 fontsize=13, weight="bold", pad=20, color="#0f172a")

    for path_str in output_paths:
        p = Path(path_str)
        p.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(p, bbox_inches="tight")
    plt.close()


def generate_cost_comparison_plot(output_paths: List[str]) -> None:
    """Genera gráfico comparativo entre Distancia Pura vs Costo de Tiempo de Emergencia con alta legibilidad."""
    segments_labels = [f"{s.origin} -> {s.destination}\n({s.street_name[:16]})" for s in ROAD_SEGMENTS]
    distances = [s.length_m for s in ROAD_SEGMENTS]
    times = [CuscoCostModel.calculate_cost(s, metric='time') for s in ROAD_SEGMENTS]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 5.8), dpi=300)

    # Gráfico 1: Distancia física
    ax1.barh(segments_labels, distances, color="#3b82f6", edgecolor="#1e40af", height=0.62)
    ax1.set_xlabel("Distancia Física (Metros)", fontsize=11.5, weight="bold")
    ax1.set_title("Longitud Métrica por Tramo Vial", fontsize=12.5, weight="bold", pad=10)
    ax1.tick_params(axis='x', labelsize=10.5)
    ax1.tick_params(axis='y', labelsize=10)
    ax1.grid(axis='x', linestyle='--', alpha=0.6)
    for i, v in enumerate(distances):
        ax1.text(v + 12, i, f"{int(v)} m", va='center', fontsize=10, weight='bold', color="#1e40af")
    ax1.set_xlim(0, max(distances) * 1.15)

    # Gráfico 2: Tiempo estimado
    ax2.barh(segments_labels, times, color="#f59e0b", edgecolor="#b45309", height=0.62)
    ax2.set_xlabel("Tiempo Estimado de Viaje (Segundos)", fontsize=11.5, weight="bold")
    ax2.set_title("Costo de Desplazamiento con Impedancia Andina", fontsize=12.5, weight="bold", pad=10)
    ax2.tick_params(axis='x', labelsize=10.5)
    ax2.tick_params(axis='y', labelsize=10)
    ax2.grid(axis='x', linestyle='--', alpha=0.6)
    for i, v in enumerate(times):
        ax2.text(v + 3.5, i, f"{v:.1f} s", va='center', fontsize=10, weight='bold', color="#b45309")
    ax2.set_xlim(0, max(times) * 1.16)

    plt.tight_layout()
    for path_str in output_paths:
        p = Path(path_str)
        p.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(p, bbox_inches="tight")
    plt.close()


def generate_scalability_plot(benchmark_results: Dict[str, Any], output_paths: List[str]) -> None:
    """Genera curvas de escalabilidad comparativa de tiempo de ejecución vs número de vértices."""
    scales = benchmark_results["scales"]
    bin_times = [d["mean_us"] for d in benchmark_results["data"]["binary_heap"]]
    bin_std = [d["std_us"] for d in benchmark_results["data"]["binary_heap"]]

    four_times = [d["mean_us"] for d in benchmark_results["data"]["4ary_heap"]]
    four_std = [d["std_us"] for d in benchmark_results["data"]["4ary_heap"]]

    fib_times = [d["mean_us"] for d in benchmark_results["data"]["fibonacci_heap"]]
    fib_std = [d["std_us"] for d in benchmark_results["data"]["fibonacci_heap"]]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    # Gráfico lineal
    ax1.errorbar(scales, bin_times, yerr=bin_std, fmt='-o', color='#2563eb', label='Binary Min-Heap Indexado', lw=2, capsize=4)
    ax1.errorbar(scales, four_times, yerr=four_std, fmt='-s', color='#16a34a', label='4-ary Heap Contiguo', lw=2, capsize=4)
    ax1.errorbar(scales, fib_times, yerr=fib_std, fmt='-^', color='#dc2626', label='Fibonacci Heap Dinámico', lw=2, capsize=4)
    ax1.set_xlabel("Número de Vértices (|V|)", fontsize=10, weight='bold')
    ax1.set_ylabel("Tiempo Medio de CPU (µs)", fontsize=10, weight='bold')
    ax1.set_title("Escalabilidad Temporal en Redes Viales (Escala Lineal)", fontsize=11, weight='bold')
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(frameon=True, facecolor='white', framealpha=0.9)

    # Gráfico logarítmico
    ax2.plot(scales, bin_times, '-o', color='#2563eb', label='Binary Min-Heap Indexado', lw=2)
    ax2.plot(scales, four_times, '-s', color='#16a34a', label='4-ary Heap Contiguo', lw=2)
    ax2.plot(scales, fib_times, '-^', color='#dc2626', label='Fibonacci Heap Dinámico', lw=2)
    ax2.set_xscale('log')
    ax2.set_yscale('log')
    ax2.set_xlabel("Número de Vértices (|V|) - Escala Log", fontsize=10, weight='bold')
    ax2.set_ylabel("Tiempo de CPU (µs) - Escala Log", fontsize=10, weight='bold')
    ax2.set_title("Comportamiento Asintótico (Escala Log-Log)", fontsize=11, weight='bold')
    ax2.grid(True, which="both", linestyle='--', alpha=0.6)
    ax2.legend(frameon=True, facecolor='white', framealpha=0.9)

    plt.tight_layout()
    for path_str in output_paths:
        p = Path(path_str)
        p.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(p, bbox_inches="tight")
    plt.close()


def generate_operations_breakdown_plot(benchmark_results: Dict[str, Any], output_paths: List[str]) -> None:
    """Genera gráfico del desglose cuantitativo de operaciones elementales."""
    scales = benchmark_results["scales"]
    ops_bin = benchmark_results["operation_counts"]["binary_heap"]

    inserts = [op.get("insert_ops", scales[i]) for i, op in enumerate(ops_bin)]
    extract_mins = [op.get("extract_min_ops", scales[i]) for i, op in enumerate(ops_bin)]
    decrease_keys = [op.get("decrease_key_ops", 0) for op in ops_bin]
    relax_attempts = [op.get("relax_attempts", 0) for op in ops_bin]

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    x = np.arange(len(scales))
    width = 0.2

    ax.bar(x - 1.5 * width, inserts, width, label='Insert (|V|)', color='#3b82f6')
    ax.bar(x - 0.5 * width, extract_mins, width, label='Extract-Min (|V|)', color='#10b981')
    ax.bar(x + 0.5 * width, decrease_keys, width, label='Decrease-Key Efectivos', color='#f59e0b')
    ax.bar(x + 1.5 * width, relax_attempts, width, label='Intentos de Relajación (|E|)', color='#8b5cf6')

    ax.set_xticks(x)
    ax.set_xticklabels([f"|V|={n}" for n in scales], fontsize=9, weight='bold')
    ax.set_ylabel("Número de Operaciones", fontsize=10, weight='bold')
    ax.set_yscale('log')
    ax.set_title("Distribución de Operaciones Primitivas del Algoritmo de Dijkstra en Redes Viales",
                 fontsize=11, weight='bold', pad=15)
    ax.grid(axis='y', linestyle='--', alpha=0.6)
    ax.legend(frameon=True, facecolor='white', framealpha=0.95)

    plt.tight_layout()
    for path_str in output_paths:
        p = Path(path_str)
        p.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(p, bbox_inches="tight")
    plt.close()


def generate_architecture_diagram(output_paths: List[str]) -> None:
    """Genera un diagrama gráfico de arquitectura del software en alta resolución."""
    fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
    ax.set_facecolor('#f8fafc')

    # Capas horizontales
    layers = [
        ("4. Capa de Validación, Experimentación y Reportes\n(tests/test_dijkstra.py, scalability_benchmark.py, latex_exporter.py)", 5.2, "#8b5cf6", "#ede9fe"),
        ("3. Capa de Algoritmos de Caminos Mínimos\n(algorithms/dijkstra.py - Inyección de Colas y Telemetría)", 3.6, "#10b981", "#d1fae5"),
        ("2. Capa de Estructuras de Datos (Colas de Prioridad con Decrease-Key)\n(IndexedMinHeap, DAryHeap d=4, FibonacciHeap)", 2.0, "#f59e0b", "#fef3c7"),
        ("1. Capa de Modelos Viales y Datos Geoespaciales\n(models/cusco_network.py, utils/cost_model.py, data/cusco_centro_network.json)", 0.4, "#2563eb", "#dbeafe")
    ]

    for title, y, border_color, fill_color in layers:
        rect = patches.FancyBboxPatch(
            (-5.5, y - 0.55), 11.0, 1.1,
            boxstyle="round,pad=0.2",
            fc=fill_color, ec=border_color, lw=2.2
        )
        ax.add_patch(rect)
        ax.text(0, y, title, ha='center', va='center', fontsize=10.5, weight='bold', color="#0f172a")

    # Flechas de dependencia descendente
    for y_arrow in [4.4, 2.8, 1.2]:
        ax.annotate(
            "", xy=(0, y_arrow - 0.4), xytext=(0, y_arrow + 0.4),
            arrowprops=dict(arrowstyle="-|>", color="#475569", lw=2.5, mutation_scale=20)
        )

    ax.set_xlim(-6.5, 6.5)
    ax.set_ylim(-0.6, 6.4)
    ax.axis("off")
    ax.set_title("Diagrama de Arquitectura Modular del Sistema (4 Capas Desacopladas)",
                 fontsize=13, weight="bold", pad=20, color="#0f172a")

    plt.tight_layout()
    for path_str in output_paths:
        p = Path(path_str)
        p.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(p, bbox_inches="tight")
    plt.close()


def generate_heaps_comparison_diagram(output_paths: List[str]) -> None:
    """Genera diagrama esquemático comparando las tres estructuras de montículos en memoria."""
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5), dpi=300)
    for ax in [ax1, ax2, ax3]:
        ax.set_facecolor('#f8fafc')
        ax.axis('off')

    # 1. Binary Heap Indexado
    ax1.set_title("1. Binary Min-Heap Indexado\n(Arreglo Contiguo + Tabla Hash Inversa)", fontsize=10.5, weight='bold', color="#1e3a8a")
    # Nodos de árbol binario
    ax1.plot([0, -1], [2, 1], 'k-', lw=1.5)
    ax1.plot([0, 1], [2, 1], 'k-', lw=1.5)
    ax1.plot([-1, -1.5], [1, 0], 'k-', lw=1.5)
    ax1.plot([-1, -0.5], [1, 0], 'k-', lw=1.5)
    ax1.scatter([0, -1, 1, -1.5, -0.5], [2, 1, 1, 0, 0], s=350, c='#3b82f6', ec='#1e3a8a', lw=2, zorder=3)
    ax1.text(0, 2, "A:0", ha='center', va='center', color='white', weight='bold', fontsize=8)
    ax1.text(-1, 1, "B:180", ha='center', va='center', color='white', weight='bold', fontsize=7)
    ax1.text(1, 1, "C:450", ha='center', va='center', color='white', weight='bold', fontsize=7)
    ax1.text(-1.5, 0, "D:400", ha='center', va='center', color='white', weight='bold', fontsize=6.5)
    ax1.text(-0.5, 0, "E:650", ha='center', va='center', color='white', weight='bold', fontsize=6.5)
    ax1.text(0, -0.9, "Array: [A, B, C, D, E]\npos_map: {A:0, B:1, C:2, D:3, E:4}\nDecrease-Key: O(log |V|)",
             ha='center', fontsize=8.5, bbox=dict(boxstyle="round", fc="#dbeafe", ec="#3b82f6"))

    # 2. 4-ary Heap
    ax2.set_title("2. 4-ary Heap Contiguo (d=4)\n(Alta localidad de caché L1/L2)", fontsize=10.5, weight='bold', color="#15803d")
    for dx in [-1.5, -0.5, 0.5, 1.5]:
        ax2.plot([0, dx], [2, 0.8], 'k-', lw=1.2)
    ax2.scatter([0, -1.5, -0.5, 0.5, 1.5], [2, 0.8, 0.8, 0.8, 0.8], s=350, c='#22c55e', ec='#15803d', lw=2, zorder=3)
    ax2.text(0, 2, "Raíz", ha='center', va='center', color='white', weight='bold', fontsize=8)
    ax2.text(-1.5, 0.8, "H1", ha='center', va='center', color='white', weight='bold', fontsize=8)
    ax2.text(-0.5, 0.8, "H2", ha='center', va='center', color='white', weight='bold', fontsize=8)
    ax2.text(0.5, 0.8, "H3", ha='center', va='center', color='white', weight='bold', fontsize=8)
    ax2.text(1.5, 0.8, "H4", ha='center', va='center', color='white', weight='bold', fontsize=8)
    ax2.text(0, -0.9, "Altura: ceil(log4 |V|) = 0.5 log2 |V|\n4 hijos adyacentes en memoria\nDecrease-Key: O(log4 |V|)",
             ha='center', fontsize=8.5, bbox=dict(boxstyle="round", fc="#dcfce7", ec="#22c55e"))

    # Raíces enlazadas horizontalmente con flechas bidireccionales
    ax3.annotate("", xy=(-0.35, 1.8), xytext=(-1.35, 1.8),
                 arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=2))
    ax3.annotate("", xy=(1.15, 1.8), xytext=(-0.05, 1.8),
                 arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=2))
    ax3.plot([-1.5, -1.5], [1.8, 0.8], 'k-', lw=1.5)
    ax3.plot([-0.2, -0.2], [1.8, 0.8], 'k-', lw=1.5)
    ax3.scatter([-1.5, -0.2, 1.3], [1.8, 1.8, 1.8], s=350, c='#ef4444', ec='#b91c1c', lw=2, zorder=3)
    ax3.scatter([-1.5, -0.2], [0.8, 0.8], s=280, c='#f87171', ec='#b91c1c', lw=1.5, zorder=3)
    ax3.text(-1.5, 1.8, "T1", ha='center', va='center', color='white', weight='bold', fontsize=8)
    ax3.text(-0.2, 1.8, "T2", ha='center', va='center', color='white', weight='bold', fontsize=8)
    ax3.text(1.3, 1.8, "Min", ha='center', va='center', color='white', weight='bold', fontsize=8)
    ax3.text(0, -0.9, "Árboles de grado dinámico\nCortes en cascada (cascading cuts)\nDecrease-Key: O(1) Amortizado",
             ha='center', fontsize=8.5, bbox=dict(boxstyle="round", fc="#fee2e2", ec="#ef4444"))

    for ax in [ax1, ax2, ax3]:
        ax.set_xlim(-2.2, 2.2)
        ax.set_ylim(-1.5, 2.5)

    plt.tight_layout()
    for path_str in output_paths:
        p = Path(path_str)
        p.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(p, bbox_inches="tight")
    plt.close()
