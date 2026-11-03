"""Condiciones meteorológicas de Cusco y escenario de sensibilidad vial.

Open-Meteo entrega estimaciones de modelos meteorológicos, no lecturas de una
estación física. La etiqueta `station_name` heredada de la interfaz no acredita
una estación en Perayoc. Cada consulta puede guardarse como snapshot JSON
para repetir una demostración sin depender de Internet.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, Optional

import requests

OPEN_METEO_ENDPOINT = "https://api.open-meteo.com/v1/forecast"
CUSCO_LATITUDE = -13.5165
CUSCO_LONGITUDE = -71.9788


class WeatherServiceError(RuntimeError):
    pass


WMO_WEATHER_CODES = {
    0: "Cielo despejado",
    1: "Principalmente despejado",
    2: "Parcialmente nublado",
    3: "Nublado / Cubierto",
    45: "Niebla",
    48: "Niebla con escarcha",
    51: "Llovizna ligera",
    53: "Llovizna moderada",
    55: "Llovizna densa",
    61: "Lluvia ligera",
    63: "Lluvia moderada",
    65: "Lluvia fuerte",
    71: "Nevada ligera / Granizo fino",
    73: "Nevada moderada",
    75: "Nevada intensa",
    80: "Chubascos de lluvia ligeros",
    81: "Chubascos de lluvia moderados",
    82: "Chubascos de lluvia violentos",
    95: "Tormenta eléctrica",
    96: "Tormenta eléctrica con granizo ligero",
    99: "Tormenta eléctrica con granizo fuerte",
}


def weather_code_to_description(code: int) -> str:
    return WMO_WEATHER_CODES.get(code, f"Condición meteorológica (código {code})")


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
    relative_humidity_pct: float = 50.0
    rain_mm: float = 0.0
    surface_pressure_hpa: Optional[float] = None
    cloud_cover_pct: float = 20.0
    weather_description: str = "Despejado"
    station_name: str = "Consulta meteorológica para Cusco (Open-Meteo)"
    source: str = "Open-Meteo (datos de modelo)"
    cached: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any], cached: bool = False) -> "WeatherObservation":
        allowed = {field.name for field in cls.__dataclass_fields__.values()}
        payload = {key: value for key, value in data.items() if key in allowed}
        payload["cached"] = cached
        if "weather_description" not in payload and "weather_code" in payload:
            payload["weather_description"] = weather_code_to_description(int(payload["weather_code"]))
        return cls(**payload)


@dataclass(frozen=True)
class WeatherImpactCoefficients:
    """Coeficientes de escenario no calibrados con tiempos de viaje observados."""

    precipitation: float = 0.20
    low_visibility: float = 0.15
    wind_gust: float = 0.10
    humidity: float = 0.08
    reference_precipitation_mm: float = 10.0
    reference_visibility_m: float = 10_000.0
    reference_gust_kmh: float = 80.0
    humidity_threshold_pct: float = 65.0


def weather_multiplier(
    observation: WeatherObservation,
    coefficients: WeatherImpactCoefficients = WeatherImpactCoefficients(),
) -> float:
    """Devuelve Omega>=1 para comparar el escenario base con el meteorológico.

    Incorpora precipitación pluvial, visibilidad reducida por neblina, ráfagas
    de viento andino y humedad relativa alta sobre calzada de adoquín/asfalto.
    """
    rain = min(max(observation.precipitation_mm, 0.0) / coefficients.reference_precipitation_mm, 1.0)
    visibility = max(
        0.0,
        1.0 - min(max(observation.visibility_m, 0.0), coefficients.reference_visibility_m)
        / coefficients.reference_visibility_m,
    )
    gust = min(max(observation.wind_gusts_kmh, 0.0) / coefficients.reference_gust_kmh, 1.0)

    # Factor de humedad relativa solo cuando supera el umbral (pérdida de adherencia en calzadas cusqueñas)
    humidity_factor = 0.0
    if observation.relative_humidity_pct > coefficients.humidity_threshold_pct:
        humidity_factor = min(
            1.0,
            (observation.relative_humidity_pct - coefficients.humidity_threshold_pct)
            / (100.0 - coefficients.humidity_threshold_pct),
        )

    factor = (
        1.0
        + coefficients.precipitation * rain
        + coefficients.low_visibility * visibility
        + coefficients.wind_gust * gust
        + coefficients.humidity * humidity_factor
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
                "temperature_2m,relative_humidity_2m,precipitation,rain,visibility,"
                "wind_speed_10m,wind_gusts_10m,surface_pressure,cloud_cover,weather_code"
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
                weather_code = int(current.get("weather_code", 0))
                observation = WeatherObservation(
                    observed_at=str(current["time"]),
                    latitude=float(raw.get("latitude", latitude)),
                    longitude=float(raw.get("longitude", longitude)),
                    temperature_c=float(current.get("temperature_2m", 0.0)),
                    precipitation_mm=float(current.get("precipitation", 0.0)),
                    visibility_m=float(current.get("visibility", 10_000.0)),
                    wind_speed_kmh=float(current.get("wind_speed_10m", 0.0)),
                    wind_gusts_kmh=float(current.get("wind_gusts_10m", current.get("wind_speed_10m", 0.0))),
                    weather_code=weather_code,
                    relative_humidity_pct=float(current.get("relative_humidity_2m", 50.0)),
                    rain_mm=float(current.get("rain", current.get("precipitation", 0.0))),
                    surface_pressure_hpa=(
                        float(current["surface_pressure"]) if current.get("surface_pressure") is not None else None
                    ),
                    cloud_cover_pct=float(current.get("cloud_cover", 20.0)),
                    weather_description=weather_code_to_description(weather_code),
                    station_name="Consulta meteorológica para Cusco (Open-Meteo)",
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


OPENWEATHERMAP_ENDPOINT = "https://api.openweathermap.org/data/2.5/weather"
DEFAULT_OWM_API_KEY = ""


def get_default_owm_key() -> str:
    """La CLI solo acepta credenciales proporcionadas mediante el entorno."""
    return os.environ.get("OPENWEATHERMAP_API_KEY", "").strip()


class OpenWeatherMapClient:
    """Cliente para consultar OpenWeatherMap API (Current Weather Data v2.5).

    Permite usar una API key generada en https://home.openweathermap.org/api_keys
    tras registrarse en https://home.openweathermap.org/users/sign_up.
    Soporta guardado de snapshots JSON locales y modo de contingencia desconectado.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        session: Optional[requests.Session] = None,
        timeout: float = 8.0,
        retries: int = 2,
    ) -> None:
        raw_key = api_key if api_key is not None else get_default_owm_key()
        self.api_key = raw_key.strip()
        self.session = session or requests.Session()
        self.timeout = timeout
        self.retries = max(1, retries)

    def fetch_current(
        self,
        latitude: float = CUSCO_LATITUDE,
        longitude: float = CUSCO_LONGITUDE,
        snapshot_path: str | Path | None = None,
    ) -> WeatherObservation:
        if not self.api_key:
            raise WeatherServiceError(
                "No se especificó la API Key de OpenWeatherMap. "
                "Para obtener una clave gratuita regístrese en https://home.openweathermap.org/users/sign_up "
                "y cópiela desde https://home.openweathermap.org/api_keys."
            )

        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "metric",
            "lang": "es",
        }
        for attempt in range(self.retries):
            try:
                resp = self.session.get(OPENWEATHERMAP_ENDPOINT, params=params, timeout=self.timeout)
                if resp.status_code == 401:
                    raise WeatherServiceError(
                        "Clave de API inválida o aún no activada en OpenWeatherMap (HTTP 401 Unauthorized).\n"
                        "Nota importante: Las claves recién creadas en OpenWeatherMap tardan habitualmente "
                        "entre 10 y 30 minutos en propagarse y activarse en sus servidores globales. "
                        "Si se registró recientemente en https://home.openweathermap.org/users/sign_up, "
                        "espere unos minutos e intente nuevamente."
                    )
                resp.raise_for_status()
                data = resp.json()
                main = data.get("main", {})
                wind = data.get("wind", {})
                rain_dict = data.get("rain", {})
                rain_val = float(rain_dict.get("1h", rain_dict.get("3h", 0.0)))
                weather_list = data.get("weather", [])
                weather = weather_list[0] if weather_list else {}
                desc = weather.get("description", "Cielo variable").capitalize()
                weather_id = int(weather.get("id", 800))
                clouds = float(data.get("clouds", {}).get("all", 20.0))

                observation = WeatherObservation(
                    observed_at=(datetime.fromtimestamp(int(data["dt"]), timezone.utc).isoformat()
                                 if data.get("dt") is not None else "sin hora indicada por el proveedor"),
                    latitude=latitude,
                    longitude=longitude,
                    temperature_c=float(main.get("temp", 15.0)),
                    precipitation_mm=rain_val,
                    visibility_m=float(data.get("visibility", 10000.0)),
                    wind_speed_kmh=float(wind.get("speed", 0.0) * 3.6),
                    wind_gusts_kmh=float(wind.get("gust", wind.get("speed", 0.0)) * 3.6),
                    weather_code=weather_id,
                    relative_humidity_pct=float(main.get("humidity", 50.0)),
                    rain_mm=rain_val,
                    surface_pressure_hpa=(
                        float(main["grnd_level"]) if main.get("grnd_level") is not None else None
                    ),
                    cloud_cover_pct=clouds,
                    weather_description=desc,
                    station_name=f"Consulta meteorológica para {data.get('name', 'Cusco')} (OpenWeatherMap)",
                    source="OpenWeatherMap REST API",
                    cached=False,
                )
                if snapshot_path is not None:
                    save_snapshot(snapshot_path, observation, data)
                return observation
            except WeatherServiceError:
                raise
            except (requests.RequestException, KeyError, TypeError, ValueError):
                if attempt + 1 < self.retries:
                    time.sleep(0.25 * (2**attempt))

        # La excepción de requests puede incluir la URL con la clave en appid.
        raise WeatherServiceError(
            "No se pudieron obtener las condiciones meteorológicas desde OpenWeatherMap."
        ) from None

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
