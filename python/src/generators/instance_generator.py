"""
Generación de instancias sintéticas reproducibles (semilla fija).

- random_road_network: grafo dirigido disperso tipo red vial (árbol de
  conectividad + aristas locales). Es el generador que ya usaba el benchmark.
- grid_network: cuadrícula urbana filas x columnas, doble sentido; con
  weight_mode='unit' produce muchos empates (útil para mostrar caminos
  alternativos de igual costo entre estructuras).
- road_grid_network: cuadrícula con longitudes y pendientes, pesada con el
  modelo de impedancia andina (CuscoCostModel).
"""
import random
from typing import Dict, Hashable, List, Tuple

from src.io.graph_io import GraphInstance, InvalidInstanceError
from src.utils.cost_model import CuscoCostModel, RoadSegment

Adj = Dict[Hashable, List[Tuple[Hashable, float]]]


def _check_positive_int(value, name: str, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise InvalidInstanceError(f"'{name}' debe ser un entero >= {minimum} (se recibió {value!r}).")
    return value


def generate_synthetic_road_network(num_nodes: int, avg_degree: float = 3.5,
                                    seed: int = 42) -> Tuple[List[str], Adj]:
    """
    Grafo dirigido sintético. Primero un árbol (alcanzable desde N0) y luego
    aristas locales (|i-j| <= 3) hasta llegar al grado promedio.
    """
    _check_positive_int(num_nodes, "num_nodes")
    if avg_degree <= 0:
        raise InvalidInstanceError("'avg_degree' debe ser positivo.")
    rng = random.Random(seed)
    nodes = [f"N{i}" for i in range(num_nodes)]
    adj: Adj = {v: [] for v in nodes}

    for i in range(1, num_nodes):
        parent_idx = rng.randint(max(0, i - 4), i - 1)
        adj[nodes[parent_idx]].append((nodes[i], round(rng.uniform(15.0, 300.0), 1)))
        if rng.random() < 0.6:
            adj[nodes[i]].append((nodes[parent_idx], round(rng.uniform(15.0, 300.0), 1)))

    target_edges = int(num_nodes * avg_degree)
    existing = {(u, v) for u, nb in adj.items() for v, _ in nb}
    current = len(existing)
    attempts, max_attempts = 0, target_edges * 5
    while current < target_edges and attempts < max_attempts:
        attempts += 1
        u_idx = rng.randint(0, num_nodes - 1)
        v_idx = u_idx + rng.choice([-3, -2, -1, 1, 2, 3])
        if 0 <= v_idx < num_nodes:
            u, v = nodes[u_idx], nodes[v_idx]
            if (u, v) not in existing:
                adj[u].append((v, round(rng.uniform(20.0, 450.0), 1)))
                existing.add((u, v))
                current += 1
    return nodes, adj


def random_road_network(num_nodes: int, avg_degree: float = 3.5, seed: int = 42) -> GraphInstance:
    nodes, adj = generate_synthetic_road_network(num_nodes, avg_degree, seed)
    return GraphInstance(nodes=nodes, adj=adj, name=f"random_n{num_nodes}_s{seed}",
                         default_source=nodes[0])


def random_directed_network(
    num_nodes: int,
    target_edges: int,
    seed: int = 42,
    profile: str = "synthetic",
) -> GraphInstance:
    """Grafo alcanzable con exactamente ``target_edges`` aristas, si es posible."""
    _check_positive_int(num_nodes, "num_nodes")
    maximum = num_nodes * (num_nodes - 1)
    minimum = max(0, num_nodes - 1)
    if not isinstance(target_edges, int) or isinstance(target_edges, bool):
        raise InvalidInstanceError("target_edges debe ser entero.")
    if target_edges < minimum or target_edges > maximum:
        raise InvalidInstanceError(
            f"target_edges debe estar entre {minimum} y {maximum} para {num_nodes} nodos."
        )
    rng = random.Random(seed)
    nodes = [f"N{i}" for i in range(num_nodes)]
    adj: Adj = {node: [] for node in nodes}
    existing = set()

    # La cadena dirigida garantiza alcanzabilidad desde N0.
    for index in range(num_nodes - 1):
        u, v = nodes[index], nodes[index + 1]
        adj[u].append((v, round(rng.uniform(1.0, 1_000.0), 3)))
        existing.add((index, index + 1))

    while len(existing) < target_edges:
        u_index = rng.randrange(num_nodes)
        v_index = rng.randrange(num_nodes)
        if u_index == v_index or (u_index, v_index) in existing:
            continue
        existing.add((u_index, v_index))
        adj[nodes[u_index]].append((nodes[v_index], round(rng.uniform(1.0, 1_000.0), 3)))

    for node in nodes:
        adj[node].sort(key=lambda item: (str(item[0]), item[1]))
    return GraphInstance(
        nodes=nodes,
        adj=adj,
        name=f"{profile}_n{num_nodes}_m{target_edges}_s{seed}",
        default_source=nodes[0],
        metadata={"generator": "random_directed_network", "profile": profile, "seed": seed},
    )


def benchmark_network(num_nodes: int, profile: str, seed: int = 42) -> GraphInstance:
    """Perfiles canónicos: disperso O(V) y denso con 8% de aristas posibles."""
    if profile == "sparse":
        target = min(num_nodes * (num_nodes - 1), max(num_nodes - 1, 4 * num_nodes))
    elif profile == "dense":
        target = max(num_nodes - 1, round(0.08 * num_nodes * (num_nodes - 1)))
    else:
        raise InvalidInstanceError("profile debe ser 'sparse' o 'dense'.")
    return random_directed_network(num_nodes, target, seed=seed, profile=profile)


def grid_network(rows: int, cols: int, weight_mode: str = "unit", seed: int = 7,
                 low: float = 1.0, high: float = 10.0) -> GraphInstance:
    _check_positive_int(rows, "rows")
    _check_positive_int(cols, "cols")
    if weight_mode not in ("unit", "random"):
        raise InvalidInstanceError("weight_mode debe ser 'unit' o 'random'.")
    rng = random.Random(seed)
    name = lambda r, c: f"{r}_{c}"
    nodes = [name(r, c) for r in range(rows) for c in range(cols)]
    adj: Adj = {v: [] for v in nodes}
    for r in range(rows):
        for c in range(cols):
            for dr, dc in ((0, 1), (1, 0)):
                rr, cc = r + dr, c + dc
                if rr < rows and cc < cols:
                    w1 = 1.0 if weight_mode == "unit" else round(rng.uniform(low, high), 1)
                    w2 = 1.0 if weight_mode == "unit" else round(rng.uniform(low, high), 1)
                    adj[name(r, c)].append((name(rr, cc), w1))
                    adj[name(rr, cc)].append((name(r, c), w2))
    return GraphInstance(nodes=nodes, adj=adj, name=f"grid_{rows}x{cols}_{weight_mode}",
                         default_source=nodes[0])


def road_grid_network(rows: int, cols: int, seed: int = 7, metric: str = "time") -> GraphInstance:
    """Cuadrícula con calles de 80-220 m, pendientes de -8% a +12% y tipos de vía mixtos."""
    _check_positive_int(rows, "rows")
    _check_positive_int(cols, "cols")
    rng = random.Random(seed)
    types = ["calle_centro", "calle_centro", "calle_residencial", "avenida"]
    name = lambda r, c: f"{r}_{c}"
    nodes = [name(r, c) for r in range(rows) for c in range(cols)]
    adj: Adj = {v: [] for v in nodes}
    for r in range(rows):
        for c in range(cols):
            for dr, dc in ((0, 1), (1, 0)):
                rr, cc = r + dr, c + dc
                if rr < rows and cc < cols:
                    length = round(rng.uniform(80, 220), 0)
                    slope = round(rng.uniform(-8, 12), 1)
                    st = rng.choice(types)
                    a, b = name(r, c), name(rr, cc)
                    adj[a].append((b, CuscoCostModel.calculate_cost(RoadSegment(a, b, length, st, slope, ""), metric)))
                    adj[b].append((a, CuscoCostModel.calculate_cost(RoadSegment(b, a, length, st, -slope, ""), metric)))
    return GraphInstance(nodes=nodes, adj=adj, name=f"road_grid_{rows}x{cols}_s{seed}",
                         default_source=nodes[0], metric=metric)
