"""
Presentación de resultados (consola y archivos), común a todas las alternativas.

El JSON de resultados usa null para distancias infinitas (JSON estándar no
admite Infinity) y puede volver a cargarse con load_result_json para la
verificación independiente (comando `verify`).
"""
import json
from pathlib import Path
from typing import Any, Dict, Hashable, Iterable, List

from src.io.graph_io import GraphInstance

INF = float("inf")


def fmt_num(x: float, nd: int = 2) -> str:
    return "inf" if x == INF else f"{x:.{nd}f}"


def table(headers: List[str], rows: Iterable[List[Any]]) -> str:
    rows = [[str(c) for c in r] for r in rows]
    widths = [max(len(h), *(len(r[i]) for r in rows)) if rows else len(h) for i, h in enumerate(headers)]
    sep = "-+-".join("-" * w for w in widths)
    out = [" | ".join(h.ljust(w) for h, w in zip(headers, widths)), sep]
    out += [" | ".join(c.ljust(w) for c, w in zip(r, widths)) for r in rows]
    return "\n".join(out)


def result_table(instance: GraphInstance, result: Dict[str, Any], unit: str = "") -> str:
    rows = []
    for v in instance.nodes:
        d = result["distances"][v]
        path = " -> ".join(map(str, result["paths"][v])) if result["paths"][v] else "(inalcanzable)"
        rows.append([instance.label(v)[:32], fmt_num(d) + unit, path])
    return table(["Destino", "Costo", "Ruta óptima"], rows)


def stats_line(result: Dict[str, Any]) -> str:
    s = result["stats"]
    keys = ["insert_ops", "extract_min_ops", "decrease_key_ops", "relax_attempts", "comparisons",
            "swaps", "links", "cuts", "cascading_cuts", "rounds"]
    parts = [f"{k}={s[k]}" for k in keys if k in s]
    return ", ".join(parts) + f" | tiempo={result['elapsed_ms']:.3f} ms"


def trace_text(instance: GraphInstance, result: Dict[str, Any]) -> str:
    lines = []
    for step in result["history"]:
        rel = []
        for r in step["relaxations"]:
            mark = "relaja" if r["relaxed"] else "descarta"
            rel.append(f"{r['to_node']}: {fmt_num(r['old_dist'])}->{fmt_num(r['new_dist'])} ({mark})")
        lines.append(f"k={step['k']:>2} extrae {step['extracted']} (d={fmt_num(step['dist_extracted'])}) "
                     f"| S={{{', '.join(map(str, step['permanent_set']))}}} | " + ("; ".join(rel) or "sin aristas salientes"))
    return "\n".join(lines)


def _jsonable_dist(d: float):
    return None if d == INF else d


def result_to_dict(instance: GraphInstance, result: Dict[str, Any]) -> Dict[str, Any]:
    nodes = instance.nodes
    return {
        "instance": instance.name,
        "algorithm": result["algorithm"],
        "queue": result.get("queue"),
        "source": result["source"],
        "distances": {str(v): _jsonable_dist(result["distances"][v]) for v in nodes},
        "predecessors": {str(v): result["predecessors"][v] for v in nodes},
        "paths": {str(v): result["paths"][v] for v in nodes},
        "stats": result["stats"],
        "elapsed_ms": round(result["elapsed_ms"], 4),
    }


def save_results_json(path: str, payload: Any) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return out


def load_result_json(path: str, instance: GraphInstance) -> Dict[str, Any]:
    """Lee un resultado exportado y restituye los ids originales de la instancia."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict) and "results" in data:      # salida de `run --queue all`
        data = next(iter(data["results"].values()))
    by_str: Dict[str, Hashable] = {str(n): n for n in instance.nodes}
    back = lambda x: by_str.get(str(x), x) if x is not None else None
    dist = {back(k): (INF if v is None else float(v)) for k, v in data["distances"].items()}
    return {
        "source": back(data["source"]),
        "distances": dist,
        "predecessors": {back(k): back(v) for k, v in data.get("predecessors", {}).items()},
        "paths": {back(k): [back(x) for x in p] for k, p in data.get("paths", {}).items()},
        "algorithm": data.get("algorithm"), "queue": data.get("queue"),
    }
