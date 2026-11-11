from dataclasses import replace

import pytest
import requests

from src.services.weather import (
    OpenMeteoClient,
    OpenWeatherMapClient,
    WeatherObservation,
    WeatherServiceError,
    load_snapshot,
    weather_multiplier,
)


def observation(**changes):
    base = WeatherObservation(
        observed_at="2026-10-28T12:00",
        latitude=-13.5165,
        longitude=-71.9788,
        temperature_c=18.0,
        precipitation_mm=0.0,
        visibility_m=10_000.0,
        wind_speed_kmh=5.0,
        wind_gusts_kmh=0.0,
        weather_code=0,
    )
    return replace(base, **changes)


def test_clear_weather_has_unit_multiplier():
    assert weather_multiplier(observation()) == 1.0


def test_adverse_weather_increases_time_cost():
    adverse = observation(precipitation_mm=8.0, visibility_m=2_000.0, wind_gusts_kmh=60.0)
    assert 1.0 < weather_multiplier(adverse) <= 1.45


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "latitude": -13.51,
            "longitude": -71.97,
            "current": {
                "time": "2026-10-28T12:00",
                "temperature_2m": 17.5,
                "precipitation": 0.4,
                "visibility": 8_000,
                "wind_speed_10m": 10.0,
                "wind_gusts_10m": 20.0,
                "weather_code": 61,
            },
        }


class FakeSession:
    def get(self, *_args, **_kwargs):
        return FakeResponse()


class FailingSession:
    def get(self, *_args, **_kwargs):
        raise requests.ConnectionError("sin red")


def test_fetch_saves_reproducible_snapshot(tmp_path):
    path = tmp_path / "weather.json"
    result = OpenMeteoClient(FakeSession(), retries=1).fetch_current(snapshot_path=path)
    cached = load_snapshot(path)
    assert result.precipitation_mm == pytest.approx(0.4)
    assert cached.cached is True
    assert cached.observed_at == result.observed_at


def test_fetch_or_cached_falls_back_without_network(tmp_path):
    path = tmp_path / "weather.json"
    OpenMeteoClient(FakeSession(), retries=1).fetch_current(snapshot_path=path)
    result = OpenMeteoClient(FailingSession(), retries=1).fetch_or_cached(path)
    assert result.cached is True


class FakeOWMResponse:
    def __init__(self, status_code: int = 200, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {
            "name": "Cusco",
            "main": {"temp": 16.4, "humidity": 58, "pressure": 1013, "grnd_level": 688},
            "wind": {"speed": 3.5, "gust": 7.2},
            "rain": {"1h": 1.2},
            "visibility": 9000,
            "clouds": {"all": 40},
            "weather": [{"id": 500, "main": "Rain", "description": "lluvia ligera"}],
        }

    def raise_for_status(self):
        if self.status_code >= 400:
            err = requests.HTTPError(f"HTTP {self.status_code}")
            err.response = self
            raise err

    def json(self):
        return self._payload


class FakeOWMSession:
    def __init__(self, response: FakeOWMResponse | None = None):
        self._response = response or FakeOWMResponse()

    def get(self, *_args, **_kwargs):
        return self._response


def test_owm_fetch_current_success():
    client = OpenWeatherMapClient(api_key="valid_token_test", session=FakeOWMSession(), retries=1)
    obs = client.fetch_current()
    assert obs.temperature_c == pytest.approx(16.4)
    assert obs.precipitation_mm == pytest.approx(1.2)
    assert obs.visibility_m == pytest.approx(9000.0)
    assert obs.wind_speed_kmh == pytest.approx(3.5 * 3.6)
    assert obs.wind_gusts_kmh == pytest.approx(7.2 * 3.6)
    assert obs.relative_humidity_pct == pytest.approx(58.0)
    assert obs.surface_pressure_hpa == pytest.approx(688.0)
    assert obs.weather_description == "Lluvia ligera"
    assert "OpenWeatherMap" in obs.source


def test_owm_fetch_saves_snapshot_and_load(tmp_path):
    path = tmp_path / "weather_owm.json"
    client = OpenWeatherMapClient(api_key="valid_token_test", session=FakeOWMSession(), retries=1)
    obs = client.fetch_current(snapshot_path=path)
    assert path.exists()

    cached = load_snapshot(path)
    assert cached.cached is True
    assert cached.temperature_c == obs.temperature_c
    assert cached.weather_description == "Lluvia ligera"


def test_owm_fetch_or_cached_fallback(tmp_path):
    path = tmp_path / "weather_owm.json"
    client_ok = OpenWeatherMapClient(api_key="valid_token_test", session=FakeOWMSession(), retries=1)
    client_ok.fetch_current(snapshot_path=path)

    client_fail = OpenWeatherMapClient(api_key="valid_token_test", session=FailingSession(), retries=1)
    cached = client_fail.fetch_or_cached(path)
    assert cached.cached is True
    assert cached.temperature_c == pytest.approx(16.4)


def test_owm_401_unauthorized_error():
    session_401 = FakeOWMSession(FakeOWMResponse(status_code=401))
    client = OpenWeatherMapClient(api_key="recent_inactive_key", session=session_401, retries=1)
    with pytest.raises(WeatherServiceError) as exc_info:
        client.fetch_current()
    err_msg = str(exc_info.value)
    assert "HTTP 401 Unauthorized" in err_msg
    assert "10 y 30 minutos" in err_msg


def test_owm_missing_api_key():
    client = OpenWeatherMapClient(api_key="", retries=1)
    with pytest.raises(WeatherServiceError) as exc_info:
        client.fetch_current()
    assert "No se especificó la API Key de OpenWeatherMap" in str(exc_info.value)


def test_owm_does_not_confuse_sea_level_with_ground_pressure():
    client = OpenWeatherMapClient(api_key="clave-de-prueba", session=FakeOWMSession(
        FakeOWMResponse(payload={
            "main": {"temp": 16.4, "pressure": 1013, "humidity": 55},
            "weather": [],
        })
    ), retries=1)
    assert client.fetch_current().surface_pressure_hpa is None


def test_owm_missing_observation_time_is_not_replaced_by_fetch_time():
    client = OpenWeatherMapClient(api_key="clave-de-prueba", session=FakeOWMSession(), retries=1)
    assert client.fetch_current().observed_at == "sin hora indicada por el proveedor"


def test_owm_connection_error_does_not_expose_api_key():
    class KeyInExceptionSession:
        def get(self, *_args, **_kwargs):
            raise requests.ConnectionError("https://example.invalid/?appid=clave-de-prueba")

    client = OpenWeatherMapClient(api_key="clave-de-prueba", session=KeyInExceptionSession(), retries=1)
    with pytest.raises(WeatherServiceError) as exc_info:
        client.fetch_current()
    assert "clave-de-prueba" not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
