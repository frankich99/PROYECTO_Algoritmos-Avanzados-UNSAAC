"""
Red vial del Centro Histórico del Cusco: 6 intersecciones, 9 tramos dirigidos.
"""
from typing import Dict, List, Tuple
from src.utils.cost_model import RoadSegment, CuscoCostModel

# Catálogo de nodos
NODES_CUSCO = {
    "A": "Plaza Mayor del Cusco",
    "B": "Plaza Regocijo (Cusipata)",
    "C": "Qorikancha (Santo Domingo)",
    "D": "Plaza San Francisco",
    "E": "Mercado Central San Pedro",
    "F": "Plazoleta Limacpampa"
}

# Tramos viales con datos cartográficos y topográficos reales del Cusco
ROAD_SEGMENTS = [
    RoadSegment("A", "B", 180.0, "calle_centro", 1.5, "Calle Espaderos / Portal Carnicerías"),
    RoadSegment("A", "C", 450.0, "calle_centro", -2.0, "Calle Loreto / Pampa del Castillo"),
    RoadSegment("B", "D", 220.0, "calle_centro", 3.0, "Calle Garcilaso / Calle Marqués"),
    RoadSegment("B", "C", 400.0, "calle_centro", -1.0, "Calle San Bernardo / Almagro"),
    RoadSegment("C", "F", 350.0, "avenida", 0.5, "Calle Ahuacpinta / Limacpampa Grande"),
    RoadSegment("C", "E", 600.0, "calle_centro", 2.0, "Calle Matará / Tres Cruces de Oro"),
    RoadSegment("D", "E", 250.0, "calle_centro", 2.5, "Calle Santa Clara / Arco Santa Clara"),
    RoadSegment("D", "C", 500.0, "calle_centro", -2.5, "Calle Marqués / Mantas"),
    RoadSegment("E", "F", 700.0, "avenida", -1.0, "Calle Nueva Baja / Av. Tullumayo")
]

def get_cusco_adjacency(metric: str = "distance") -> Tuple[List[str], Dict[str, List[Tuple[str, float]]]]:
    """
    Construye la lista de adyacencia según la métrica elegida:
    - 'distance': distancias físicas en metros.
    - 'time': tiempo de viaje efectivo en segundos (costo aplicado).
    """
    nodes = list(NODES_CUSCO.keys())
    adj: Dict[str, List[Tuple[str, float]]] = {v: [] for v in nodes}

    for seg in ROAD_SEGMENTS:
        cost = CuscoCostModel.calculate_cost(seg, metric=metric)
        adj[seg.origin].append((seg.destination, cost))

    return nodes, adj

def export_network_json(filepath: str = "data/processed/cusco_centro_network.json") -> None:
    """Exporta la red vial a formato JSON estructurado."""
    import json
    from pathlib import Path
    
    out_path = Path(filepath)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "nodes": [{"id": k, "name": v} for k, v in NODES_CUSCO.items()],
        "edges": [
            {
                "origin": s.origin,
                "destination": s.destination,
                "length_m": s.length_m,
                "street_type": s.street_type,
                "gradient_pct": s.gradient_pct,
                "street_name": s.street_name,
                "travel_time_sec": CuscoCostModel.calculate_cost(s, metric="time")
            }
            for s in ROAD_SEGMENTS
        ]
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_network_json(filepath: str = "data/processed/cusco_centro_network.json") -> Tuple[List[str], Dict[str, List[Tuple[str, float]]]]:
    """Carga la lista de adyacencia desde un archivo JSON."""
    import json
    from pathlib import Path
    
    with open(Path(filepath), "r", encoding="utf-8") as f:
        data = json.load(f)
    
    nodes = [n["id"] for n in data["nodes"]]
    adj: Dict[str, List[Tuple[str, float]]] = {v: [] for v in nodes}
    for e in data["edges"]:
        adj[e["origin"]].append((e["destination"], e["travel_time_sec"]))
    return nodes, adj

