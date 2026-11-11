"""
Verificación independiente de la salida (no vuelve a ejecutar Dijkstra).

1. verify_shortest_paths: comprueba que (d, pi) es un "certificado" de caminos
   mínimos. Para pesos no negativos, d es la distancia mínima si y solo si:
     (a) d[s] = 0;
     (b) para toda arista (u,v,w) con d[u] finito: d[v] <= d[u] + w   (no queda relajación posible);
      (c) los predecesores de todos los vértices con distancia finita forman
          cadenas de aristas ajustadas que terminan en s (no en ciclos de peso cero);
     (d) cada camino reportado empieza en s, termina en v, usa aristas
         existentes y su costo es d[v]; los inalcanzables tienen d = inf y [].
    Sin caminos explícitos, se valida en O(V + E). Si se reportan caminos,
    leerlos cuesta además O(suma de sus longitudes).

2. compare_results: compara varias alternativas sobre la misma instancia y
   clasifica cada diferencia como esperada o como error.
"""
import math
from typing import Any, Dict, Hashable, List, Optional, Tuple

INF = float("inf")
DEFAULT_EPS = 1e-6


def _close(a: float, b: float, eps: float) -> bool:
    if a == INF or b == INF:
        return a == b
    if not math.isfinite(a) or not math.isfinite(b):
        return False
    return abs(a - b) <= eps * max(1.0, abs(a), abs(b))


def _min_edge_weight(adj, u, v) -> Optional[float]:
    ws = [w for x, w in adj.get(u, []) if x == v]
    return min(ws) if ws else None


def path_cost(adj, path: List[Hashable]) -> Optional[float]:
    """Costo de un camino usando la arista paralela más barata; None si falta una arista."""
    total = 0.0
    for a, b in zip(path, path[1:]):
        w = _min_edge_weight(adj, a, b)
        if w is None:
            return None
        total += w
    return total


def verify_shortest_paths(
    nodes: List[Hashable],
    adj: Dict[Hashable, List[Tuple[Hashable, float]]],
    source: Hashable,
    result: Dict[str, Any],
    eps: float = DEFAULT_EPS,
) -> Dict[str, Any]:
    dist = result["distances"]
    prev = result.get("predecessors", {})
    paths = result.get("paths", {})
    violations: List[str] = []

    missing = [v for v in nodes if v not in dist]
    if missing:
        violations.append(f"Faltan distancias para: {missing}")
        return {"ok": False, "violations": violations, "checked_edges": 0, "checked_paths": 0}

    if not _close(dist[source], 0.0, eps):
        violations.append(f"(a) d[{source}] = {dist[source]} != 0")

    edge_weights: Dict[Tuple[Hashable, Hashable], float] = {}
    checked_edges = 0
    for u in nodes:
        for v, w in adj.get(u, []):
            pair = (u, v)
            if pair not in edge_weights or w < edge_weights[pair]:
                edge_weights[pair] = w
            if dist[u] != INF:
                checked_edges += 1
            if dist[u] != INF and dist[v] > dist[u] + w and not _close(dist[v], dist[u] + w, eps):
                violations.append(f"(b) arista {u}->{v}: d[{v}]={dist[v]} > d[{u}]+w={dist[u] + w}")

    if prev.get(source) is not None:
        violations.append(f"(c) el origen {source} no debe tener predecesor")

    anchored = {source}
    unanchored = set()
    for v in nodes:
        if v == source or dist[v] == INF:
            continue
        chain = []
        in_chain = set()
        current = v
        while current not in anchored and current not in unanchored and current not in in_chain:
            in_chain.add(current)
            chain.append(current)
            parent = prev.get(current)
            weight = edge_weights.get((parent, current))
            if (parent not in dist or dist[parent] == INF or weight is None
                    or not _close(dist[current], dist[parent] + weight, eps)):
                violations.append(f"(c) predecesor inválido para {current}: pi={parent}")
                unanchored.add(current)
                break
            current = parent
        if current in anchored:
            anchored.update(chain)
        else:
            if current in in_chain:
                violations.append(f"(c) ciclo de predecesores sin camino desde {source}: {v}")
            unanchored.update(chain)

    checked_paths = 0
    for v in nodes:
        if not paths:
            break
        if dist[v] == INF:
            if paths.get(v):
                violations.append(f"(d) {v} es inalcanzable pero se reportó el camino {paths[v]}")
            continue
        checked_paths += 1
        p = paths.get(v, [])
        if not isinstance(p, list) or not p or p[0] != source or p[-1] != v:
            violations.append(f"(d) camino a {v} no va de {source} a {v}: {p}")
            continue
        weights = [edge_weights.get((a, b)) for a, b in zip(p, p[1:])]
        if any(weight is None for weight in weights):
            violations.append(f"(d) camino a {v} usa una arista inexistente: {p}")
        else:
            cost = sum(weights)
            if not _close(cost, dist[v], eps):
                violations.append(f"(d) camino a {v} cuesta {cost} pero d[{v}]={dist[v]}")

    return {"ok": not violations, "violations": violations,
            "checked_edges": checked_edges, "checked_paths": checked_paths}


def compare_results(
    adj: Dict[Hashable, List[Tuple[Hashable, float]]],
    nodes: List[Hashable],
    results: Dict[str, Dict[str, Any]],
    reference: Optional[str] = None,
    eps: float = DEFAULT_EPS,
) -> Dict[str, Any]:
    """
    Compara las salidas de varias alternativas.

    Clasificación:
    - distances distintas                 -> ERROR (Dijkstra es exacto con pesos >= 0)
    - caminos distintos con igual costo   -> ESPERADO: hay varios caminos óptimos y
                                             cada estructura desempata distinto
    - contadores internos distintos       -> ESPERADO: propiedad de cada estructura
    """
    names = list(results)
    base = reference if reference in results else names[0]
    dist_mismatch: List[str] = []
    tie_paths: List[Dict[str, Any]] = []
    for name in names:
        if name == base:
            continue
        for v in nodes:
            a, b = results[base]["distances"][v], results[name]["distances"][v]
            if not _close(a, b, eps):
                dist_mismatch.append(f"{v}: {base}={a} vs {name}={b}")
            pa, pb = results[base]["paths"][v], results[name]["paths"][v]
            if pa != pb and _close(a, b, eps):
                tie_paths.append({"node": v, base: pa, name: pb,
                                  "cost": a, "same_cost": True})
    op_keys = ["extract_min_ops", "decrease_key_ops", "relax_attempts", "comparisons"]
    ops = {name: {k: results[name]["stats"].get(k) for k in op_keys if k in results[name]["stats"]}
           for name in names}
    return {
        "baseline": base,
        "distances_equal": not dist_mismatch,
        "distance_mismatches": dist_mismatch,
        "alternative_optimal_paths": tie_paths,
        "operation_counts": ops,
        "verdict": "EQUIVALENTES" if not dist_mismatch else "DIFERENCIA (ERROR)",
    }
