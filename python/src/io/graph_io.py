"""
Lectura y validación de instancias (módulo reutilizado por todas las alternativas).

Formatos de entrada admitidos
-----------------------------
1. JSON "vial" (red del Cusco): aristas con length_m, street_type, gradient_pct;
   el peso se calcula con CuscoCostModel según la métrica ('time' o 'distance').
2. JSON genérico: {"nodes": [...], "edges": [{"origin","destination","weight"}]}
   o aristas como listas [u, v, w]. Campos opcionales: "name", "directed",
   "source" (origen por defecto).
3. Lista de aristas en texto (.txt / .csv): una arista "u v w" por línea
   (también "u,v,w"); '#' inicia comentario; la directiva "undirected" hace
   que cada arista se agregue en ambos sentidos; "node X" declara un vértice
   aislado.
4. Cadena en línea (CLI --inline): "A B 4; B C 2; A C 9".

Toda instancia pasa por validate_graph antes de ejecutar un algoritmo.
"""
from dataclasses import dataclass, field
import json
import math
from pathlib import Path
from typing import Any, Dict, Hashable, Iterable, List, Optional, Tuple

from src.utils.cost_model import CuscoCostModel, RoadSegment

Adjacency = Dict[Hashable, List[Tuple[Hashable, float]]]


class InvalidInstanceError(ValueError):
    """Entrada inválida: el mensaje explica qué falló y dónde."""


@dataclass
class GraphInstance:
    nodes: List[Hashable]
    adj: Adjacency
    name: str = "instancia"
    names: Dict[Hashable, str] = field(default_factory=dict)
    default_source: Optional[Hashable] = None
    metric: str = "weight"

    @property
    def num_nodes(self) -> int:
        return len(self.nodes)

    @property
    def num_edges(self) -> int:
        return sum(len(v) for v in self.adj.values())

    def label(self, node: Hashable) -> str:
        return f"{node}: {self.names[node]}" if node in self.names else str(node)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa en el formato JSON genérico (formato 2)."""
        data: Dict[str, Any] = {
            "name": self.name,
            "directed": True,
            "metric": self.metric,
            "nodes": [{"id": n, "name": self.names[n]} if n in self.names else n for n in self.nodes],
            "edges": [{"origin": u, "destination": v, "weight": w}
                      for u in self.nodes for v, w in self.adj[u]],
        }
        if self.default_source is not None:
            data["source"] = self.default_source
        return data

    def save_json(self, path: str) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return out


# ---------------------------------------------------------------------------
# Validación
# ---------------------------------------------------------------------------
def _as_weight(raw: Any, where: str) -> float:
    if isinstance(raw, bool):
        raise InvalidInstanceError(f"{where}: el peso {raw!r} no es numérico.")
    try:
        w = float(raw)
    except (TypeError, ValueError):
        raise InvalidInstanceError(f"{where}: el peso {raw!r} no es numérico.") from None
    if math.isnan(w) or math.isinf(w):
        raise InvalidInstanceError(f"{where}: el peso debe ser finito (se recibió {raw!r}).")
    return w


def validate_graph(
    nodes: List[Hashable],
    adj: Adjacency,
    source: Optional[Hashable] = None,
    allow_negative: bool = False,
) -> None:
    """
    Verifica las precondiciones de los algoritmos:
    - al menos un vértice, sin identificadores repetidos;
    - toda arista conecta vértices declarados;
    - pesos numéricos y finitos; no negativos (precondición de Dijkstra)
      salvo allow_negative=True (Bellman-Ford);
    - el origen, si se indica, pertenece al grafo.
    """
    if not nodes:
        raise InvalidInstanceError("El grafo no tiene vértices.")
    node_set = set(nodes)
    if len(node_set) != len(nodes):
        dups = sorted({str(n) for n in nodes if nodes.count(n) > 1})
        raise InvalidInstanceError(f"Identificadores de vértice repetidos: {', '.join(dups)}.")
    for u in adj:
        if u not in node_set:
            raise InvalidInstanceError(f"La lista de adyacencia contiene el vértice no declarado {u!r}.")
    for u in nodes:
        for item in adj.get(u, []):
            try:
                v, w = item
            except (TypeError, ValueError):
                raise InvalidInstanceError(f"Arista mal formada desde {u!r}: {item!r}.") from None
            where = f"Arista {u!r}->{v!r}"
            if v not in node_set:
                raise InvalidInstanceError(f"{where}: el destino {v!r} no existe en el grafo.")
            w = _as_weight(w, where)
            if w < 0 and not allow_negative:
                raise InvalidInstanceError(
                    f"{where}: peso negativo ({w}). Dijkstra requiere pesos no negativos; "
                    f"use el algoritmo de referencia 'bellman_ford' si la instancia los necesita."
                )
    if source is not None and source not in node_set:
        raise InvalidInstanceError(f"El vértice origen {source!r} no existe en el grafo.")


# ---------------------------------------------------------------------------
# Construcción
# ---------------------------------------------------------------------------
def build_instance(
    edges: Iterable[Tuple[Hashable, Hashable, Any]],
    extra_nodes: Iterable[Hashable] = (),
    undirected: bool = False,
    name: str = "instancia",
    names: Optional[Dict[Hashable, str]] = None,
    default_source: Optional[Hashable] = None,
    declared_nodes: Optional[List[Hashable]] = None,
    metric: str = "weight",
) -> GraphInstance:
    """Construye la instancia a partir de aristas (u, v, w); los vértices se deducen si no se declaran."""
    edges = list(edges)
    if declared_nodes is not None:
        nodes = list(declared_nodes)
        if len(set(nodes)) != len(nodes):
            validate_graph(nodes, {})  # lanza el error de duplicados
        node_set = set(nodes)
        for i, (u, v, _) in enumerate(edges, 1):
            for x in (u, v):
                if x not in node_set:
                    raise InvalidInstanceError(f"Arista #{i} ({u!r}->{v!r}): el vértice {x!r} no fue declarado en 'nodes'.")
    else:
        nodes = []
        seen = set()
        for u, v, _ in edges:
            for x in (u, v):
                if x not in seen:
                    seen.add(x)
                    nodes.append(x)
    for x in extra_nodes:
        if x not in set(nodes):
            nodes.append(x)

    adj: Adjacency = {v: [] for v in nodes}
    for i, (u, v, w) in enumerate(edges, 1):
        weight = _as_weight(w, f"Arista #{i} ({u!r}->{v!r})")
        adj[u].append((v, weight))
        if undirected and u != v:
            adj[v].append((u, weight))

    inst = GraphInstance(nodes=nodes, adj=adj, name=name, names=dict(names or {}),
                         default_source=default_source, metric=metric)
    if default_source is not None and default_source not in adj:
        raise InvalidInstanceError(f"El origen por defecto {default_source!r} no existe en el grafo.")
    return inst


def _parse_edge_line(line: str, lineno: int) -> Tuple[str, str, Any]:
    parts = [p for p in line.replace(",", " ").replace(";", " ").split() if p]
    if len(parts) != 3:
        raise InvalidInstanceError(
            f"Línea {lineno}: se esperaban 3 campos 'origen destino peso' y se encontraron {len(parts)}: {line!r}."
        )
    return parts[0], parts[1], parts[2]


def parse_edge_list(text: str, name: str = "lista_aristas") -> GraphInstance:
    edges, extra, undirected, source = [], [], False, None
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        low = line.lower()
        if low in ("undirected", "no_dirigido", "nodirigido"):
            undirected = True
            continue
        if low in ("directed", "dirigido"):
            continue
        head, _, rest = line.partition(" ")
        if head.lower() in ("node", "nodo") and rest.strip():
            extra.extend(rest.split())
            continue
        if head.lower() in ("source", "origen") and rest.strip():
            source = rest.strip()
            continue
        edges.append(_parse_edge_line(line, lineno))
    if not edges and not extra:
        raise InvalidInstanceError("La lista de aristas está vacía.")
    return build_instance(edges, extra_nodes=extra, undirected=undirected, name=name, default_source=source)


def parse_inline(spec: str) -> GraphInstance:
    """'A B 4; B C 2' -> instancia. Pensado para proponer instancias en vivo durante la sesión."""
    if not spec or not spec.strip():
        raise InvalidInstanceError("La especificación en línea está vacía.")
    return parse_edge_list(spec.replace(";", "\n"), name="instancia_en_linea")


def _instance_from_json(data: Any, metric: str, name: str) -> GraphInstance:
    if not isinstance(data, dict):
        raise InvalidInstanceError("El JSON debe ser un objeto con las claves 'nodes' y 'edges'.")
    if "edges" not in data:
        raise InvalidInstanceError("El JSON no contiene la clave 'edges'.")
    raw_nodes = data.get("nodes")
    names: Dict[Hashable, str] = {}
    declared: Optional[List[Hashable]] = None
    if raw_nodes is not None:
        if not isinstance(raw_nodes, list):
            raise InvalidInstanceError("'nodes' debe ser una lista.")
        declared = []
        for i, n in enumerate(raw_nodes, 1):
            if isinstance(n, dict):
                if "id" not in n:
                    raise InvalidInstanceError(f"Vértice #{i} sin campo 'id'.")
                declared.append(n["id"])
                if "name" in n:
                    names[n["id"]] = str(n["name"])
            elif isinstance(n, (str, int)) and not isinstance(n, bool):
                declared.append(n)
            else:
                raise InvalidInstanceError(f"Vértice #{i} con formato no reconocido: {n!r}.")

    if not isinstance(data["edges"], list):
        raise InvalidInstanceError("'edges' debe ser una lista.")
    edges = []
    road_based = False
    for i, e in enumerate(data["edges"], 1):
        if isinstance(e, (list, tuple)):
            if len(e) != 3:
                raise InvalidInstanceError(f"Arista #{i}: se esperaba [origen, destino, peso], se recibió {e!r}.")
            edges.append(tuple(e))
        elif isinstance(e, dict):
            u = e.get("origin", e.get("u", e.get("from")))
            v = e.get("destination", e.get("v", e.get("to")))
            if u is None or v is None:
                raise InvalidInstanceError(f"Arista #{i}: faltan 'origin'/'destination'.")
            if "length_m" in e and metric in ("time", "distance"):
                road_based = True
                try:
                    seg = RoadSegment(u, v, float(e["length_m"]), e.get("street_type", "calle_centro"),
                                      float(e.get("gradient_pct", 0.0)), e.get("street_name", ""))
                except (TypeError, ValueError):
                    raise InvalidInstanceError(f"Arista #{i}: atributos viales no numéricos.") from None
                if seg.length_m < 0:
                    raise InvalidInstanceError(f"Arista #{i} ({u!r}->{v!r}): longitud negativa ({seg.length_m}).")
                edges.append((u, v, CuscoCostModel.calculate_cost(seg, metric=metric)))
            elif "weight" in e:
                edges.append((u, v, e["weight"]))
            elif "travel_time_sec" in e:
                edges.append((u, v, e["travel_time_sec"]))
            else:
                raise InvalidInstanceError(f"Arista #{i}: no tiene 'weight' ni atributos viales.")
        else:
            raise InvalidInstanceError(f"Arista #{i} con formato no reconocido: {e!r}.")

    return build_instance(
        edges,
        undirected=not bool(data.get("directed", True)),
        name=str(data.get("name", name)),
        names=names,
        default_source=data.get("source"),
        declared_nodes=declared,
        metric=metric if road_based else str(data.get("metric", "weight")),
    )


def load_instance(path: str, metric: str = "time") -> GraphInstance:
    """Carga una instancia desde .json, .txt o .csv. metric aplica a redes viales."""
    p = Path(path)
    if not p.exists():
        raise InvalidInstanceError(f"No existe el archivo de instancia: {path}")
    if p.is_dir():
        raise InvalidInstanceError(f"La ruta indicada es un directorio, no un archivo: {path}")
    if metric not in ("time", "distance"):
        raise InvalidInstanceError(f"Métrica no soportada: {metric!r} (use 'time' o 'distance').")
    suffix = p.suffix.lower()
    try:
        text = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise InvalidInstanceError(f"El archivo {path} no es texto UTF-8 válido.") from None
    if suffix == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise InvalidInstanceError(f"JSON mal formado en {p.name} (línea {exc.lineno}, columna {exc.colno}): {exc.msg}.") from None
        return _instance_from_json(data, metric, p.stem)
    if suffix in (".txt", ".csv", ".edges", ""):
        return parse_edge_list(text, name=p.stem)
    raise InvalidInstanceError(f"Extensión no soportada: {suffix!r} (use .json, .txt o .csv).")


def resolve_source(instance: GraphInstance, source: Optional[str]) -> Hashable:
    """Elige el origen: el indicado, el declarado en la instancia o el primer vértice.

    Los identificadores leídos de texto son str; si la instancia usa enteros
    (JSON con ids numéricos) se intenta la conversión.
    """
    if source is None:
        return instance.default_source if instance.default_source is not None else instance.nodes[0]
    if source in instance.adj:
        return source
    for n in instance.nodes:
        if str(n) == str(source):
            return n
    raise InvalidInstanceError(f"El vértice origen {source!r} no existe en el grafo '{instance.name}'.")
