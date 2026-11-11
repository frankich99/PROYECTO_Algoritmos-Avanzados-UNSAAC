"""Escenarios horarios hipotéticos y consulta puntual opcional de tráfico."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any, Dict, Optional
import requests


class TrafficServiceError(RuntimeError):
    pass


TRAFFIC_LEVELS = {
    "fluido": {"base_multiplier": 1.00, "label": "Tráfico fluido (flujo libre)"},
    "moderado": {"base_multiplier": 1.25, "label": "Tráfico moderado"},
    "alto": {"base_multiplier": 1.65, "label": "Tráfico denso / congestión alta"},
    "hora_punta": {"base_multiplier": 2.20, "label": "Hora punta / saturación crítica"},
}

# Sensibilidad multiplicativa según la topología de la vía en Cusco
STREET_TYPE_SENSITIVITY = {
    "calle_centro": 1.35,      # Casco colonial estrecho: gran vulnerabilidad a tranques
    "avenida": 1.15,           # Av. El Sol, Cultura, Tullumayo: alto volumen
    "calle_residencial": 0.95, # Calles barriales con menor impacto
    "peatonal": 1.00,          # Tramos peatonales
}

TOMTOM_FLOW_ENDPOINT = "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json"


@dataclass(frozen=True)
class TrafficObservation:
    observed_at: str
    level: str
    base_multiplier: float
    description: str
    is_rush_hour: bool
    hour_of_day: float
    source: str = "Escenario horario hipotético (no medido)"
    cached: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any], cached: bool = False) -> "TrafficObservation":
        allowed = {field.name for field in cls.__dataclass_fields__.values()}
        payload = {key: value for key, value in data.items() if key in allowed}
        payload["cached"] = cached
        return cls(**payload)


class TomTomTrafficClient:
    """Cliente para la API de flujo vehicular y congestión de TomTom Traffic."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        session: Optional[requests.Session] = None,
        timeout: float = 8.0,
    ) -> None:
        self.api_key = api_key
        self.session = session or requests.Session()
        self.timeout = timeout

    def fetch_flow(self, lat: float = -13.5165, lon: float = -71.9788) -> Optional[Dict[str, Any]]:
        """Consulta una velocidad puntual; no infiere velocidades de otras vías."""
        if not self.api_key:
            return None
        params = {
            "point": f"{lat},{lon}",
            "key": self.api_key,
            "unit": "kmph",
        }
        try:
            resp = self.session.get(TOMTOM_FLOW_ENDPOINT, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            flow = data["flowSegmentData"]
            current_speed = float(flow["currentSpeed"])
            free_flow = float(flow["freeFlowSpeed"])
            if not all(math.isfinite(speed) and speed > 0 for speed in (current_speed, free_flow)):
                return None
            ratio = free_flow / current_speed
            if not math.isfinite(ratio):
                return None
            return {
                "current_speed_kmh": current_speed,
                "free_flow_speed_kmh": free_flow,
                "multiplier": max(1.0, round(ratio, 4)),
                "confidence": float(flow["confidence"]) if flow.get("confidence") is not None else None,
                "road_closure": bool(flow["roadClosure"]) if "roadClosure" in flow else None,
            }
        except (requests.RequestException, KeyError, TypeError, ValueError, OverflowError):
            return None


def get_traffic_by_schedule(hour_decimal: float) -> TrafficObservation:
    """Elige un nivel supuesto según la hora simulada en Cusco."""
    is_rush_hour = False
    if (7.25 <= hour_decimal <= 9.0) or (18.0 <= hour_decimal <= 20.25):
        level = "hora_punta"
        is_rush_hour = True
        desc = "Hora punta intensa: alta saturación en corredores principales y centro histórico."
    elif 12.5 <= hour_decimal <= 14.25:
        level = "alto"
        is_rush_hour = True
        desc = "Tráfico denso de mediodía (salida escolar y almuerzo)."
    elif 9.0 < hour_decimal < 12.5 or 14.25 < hour_decimal < 18.0:
        level = "moderado"
        desc = "Tráfico moderado habitual de jornada comercial."
    elif 21.5 <= hour_decimal or hour_decimal < 6.5:
        level = "fluido"
        desc = "Tráfico nocturno o de madrugada con flujo libre."
    else:
        level = "moderado"
        desc = "Tráfico regular en transición."

    multiplier = TRAFFIC_LEVELS[level]["base_multiplier"]
    now_str = datetime.now(timezone.utc).isoformat()

    return TrafficObservation(
        observed_at=now_str,
        level=level,
        base_multiplier=multiplier,
        description=desc,
        is_rush_hour=is_rush_hour,
        hour_of_day=round(hour_decimal, 2),
    )


# Alias
get_cusco_traffic_by_hour = get_traffic_by_schedule


def get_current_cusco_traffic(tomtom_key: Optional[str] = None) -> TrafficObservation:
    """Obtiene la congestión actual en hora local de Cusco (UTC-5), consultando TomTom si hay clave."""
    now = datetime.now(timezone.utc)
    local_hour = (now.hour - 5) % 24 + (now.minute / 60.0)

    # Si hay clave TomTom, intentar consulta en vivo
    if tomtom_key:
        client = TomTomTrafficClient(api_key=tomtom_key)
        live_data = client.fetch_flow()
        if live_data:
            mult = live_data["multiplier"]
            level = "hora_punta" if mult >= 2.0 else ("alto" if mult >= 1.5 else ("moderado" if mult >= 1.15 else "fluido"))
            return TrafficObservation(
                observed_at=now.isoformat(),
                level=level,
                base_multiplier=mult,
                description=f"TomTom Live Traffic: Velocidad actual {live_data['current_speed_kmh']:.1f} km/h (Flujo libre: {live_data['free_flow_speed_kmh']:.1f} km/h)",
                is_rush_hour=mult >= 1.5,
                hour_of_day=round(local_hour, 2),
                source="TomTom Traffic Flow REST API",
                cached=False,
            )

    return get_traffic_by_schedule(local_hour)


def calculate_traffic_multiplier(
    observation: TrafficObservation,
    street_type: str = "avenida",
    weather_multiplier: float = 1.0,
) -> float:
    """Calcula el multiplicador final considerando el tipo de vía y sinergia climática.

    En calzadas estrechas o cuando llueve, el impacto del tráfico se amplifica.
    """
    sensitivity = STREET_TYPE_SENSITIVITY.get(street_type, 1.0)
    base_m = observation.base_multiplier

    # La congestión por encima de 1.0 se amplifica por la sensibilidad de la vía
    net_delay = (base_m - 1.0) * sensitivity

    # Sinergia clima-tráfico: si hay lluvia/clima adverso (weather_multiplier > 1.0),
    # las colas y frenadas aumentan un 20% adicional sobre el retraso por congestión
    weather_amplification = 1.0 + 0.20 * max(0.0, weather_multiplier - 1.0)

    final_multiplier = 1.0 + net_delay * weather_amplification
    return round(max(1.0, final_multiplier), 4)


def save_traffic_snapshot(path: str | Path, observation: TrafficObservation) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        "observation": asdict(observation),
    }
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return destination


def load_traffic_snapshot(path: str | Path) -> TrafficObservation:
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
        return TrafficObservation.from_dict(data["observation"], cached=True)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise TrafficServiceError(f"Snapshot de tráfico inválido: {source}.") from exc
