"""Condiciones meteorológicas de Cusco y escenario de sensibilidad vial.

Open-Meteo entrega estimaciones de modelos meteorológicos. No se etiqueta como
estación física. Cada consulta puede guardarse como snapshot JSON para que una
demostración y un experimento puedan repetirse sin depender de Internet.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any, Dict, Optional

import requests

OPEN_METEO_ENDPOINT = "https://api.open-meteo.com/v1/forecast"
CUSCO_LATITUDE = -13.5165
CUSCO_LONGITUDE = -71.9788


class WeatherServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class WeatherObservation:
    observed_at: str
    latitude: float
    longitude: float
    temperature_c: float
    precipitation_mm: float
    visibility_m: float
    wind_speed_kmh: float
    wind_gusts_kmh: float
    weather_code: int
    source: str = "Open-Meteo (datos de modelo)"
    cached: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any], cached: bool = False) -> "WeatherObservation":
        allowed = {field.name for field in cls.__dataclass_fields__.values()}
        payload = {key: value for key, value in data.items() if key in allowed}
        payload["cached"] = cached
        return cls(**payload)


@dataclass(frozen=True)
class WeatherImpactCoefficients:
    """Coeficientes de escenario, no parámetros calibrados de tránsito."""

    precipitation: float = 0.20
    low_visibility: float = 0.15
    wind_gust: float = 0.10
    reference_precipitation_mm: float = 10.0
    reference_visibility_m: float = 10_000.0
    reference_gust_kmh: float = 80.0


def weather_multiplier(
    observation: WeatherObservation,
    coefficients: WeatherImpactCoefficients = WeatherImpactCoefficients(),
) -> float:
    """Devuelve Omega>=1 para comparar el escenario base con el meteorológico."""
    rain = min(max(observation.precipitation_mm, 0.0) / coefficients.reference_precipitation_mm, 1.0)
    visibility = max(
        0.0,
        1.0 - min(max(observation.visibility_m, 0.0), coefficients.reference_visibility_m)
        / coefficients.reference_visibility_m,
    )
    gust = min(max(observation.wind_gusts_kmh, 0.0) / coefficients.reference_gust_kmh, 1.0)
    factor = (
        1.0
        + coefficients.precipitation * rain
        + coefficients.low_visibility * visibility
        + coefficients.wind_gust * gust
    )
    return round(factor, 4)


def _snapshot_payload(observation: WeatherObservation, raw_response: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "observation": asdict(observation),
        "raw_response": raw_response,
    }


def save_snapshot(
    path: str | Path,
    observation: WeatherObservation,
    raw_response: Optional[Dict[str, Any]] = None,
) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(_snapshot_payload(observation, raw_response or {}), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return destination


def load_snapshot(path: str | Path) -> WeatherObservation:
    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
        return WeatherObservation.from_dict(payload["observation"], cached=True)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise WeatherServiceError(f"Snapshot meteorológico inválido: {source}.") from exc


class OpenMeteoClient:
    def __init__(
        self,
        session: Optional[requests.Session] = None,
        timeout: float = 10.0,
        retries: int = 3,
    ) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout
        self.retries = max(1, retries)

    def fetch_current(
        self,
        latitude: float = CUSCO_LATITUDE,
        longitude: float = CUSCO_LONGITUDE,
        snapshot_path: str | Path | None = None,
    ) -> WeatherObservation:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,precipitation,visibility,wind_speed_10m,"
                "wind_gusts_10m,weather_code"
            ),
            "timezone": "America/Lima",
        }
        last_error: Optional[Exception] = None
        for attempt in range(self.retries):
            try:
                response = self.session.get(OPEN_METEO_ENDPOINT, params=params, timeout=self.timeout)
                response.raise_for_status()
                raw = response.json()
                current = raw["current"]
                observation = WeatherObservation(
                    observed_at=str(current["time"]),
                    latitude=float(raw.get("latitude", latitude)),
                    longitude=float(raw.get("longitude", longitude)),
                    temperature_c=float(current.get("temperature_2m", 0.0)),
                    precipitation_mm=float(current.get("precipitation", 0.0)),
                    visibility_m=float(current.get("visibility", 10_000.0)),
                    wind_speed_kmh=float(current.get("wind_speed_10m", 0.0)),
                    wind_gusts_kmh=float(current.get("wind_gusts_10m", current.get("wind_speed_10m", 0.0))),
                    weather_code=int(current.get("weather_code", 0)),
                )
                if snapshot_path is not None:
                    save_snapshot(snapshot_path, observation, raw)
                return observation
            except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
                last_error = exc
                if attempt + 1 < self.retries:
                    time.sleep(0.25 * (2**attempt))
        raise WeatherServiceError("No se pudieron obtener las condiciones meteorológicas actuales.") from last_error

    def fetch_or_cached(
        self,
        snapshot_path: str | Path,
        latitude: float = CUSCO_LATITUDE,
        longitude: float = CUSCO_LONGITUDE,
    ) -> WeatherObservation:
        try:
            return self.fetch_current(latitude, longitude, snapshot_path)
        except WeatherServiceError:
            if Path(snapshot_path).exists():
                return load_snapshot(snapshot_path)
            raise
