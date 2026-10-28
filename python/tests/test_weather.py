from dataclasses import replace

import pytest
import requests

from src.services.weather import (
    OpenMeteoClient,
    WeatherObservation,
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
