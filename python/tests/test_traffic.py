import pytest
import requests
from src.services.traffic import (
    TomTomTrafficClient,
    TrafficObservation,
    calculate_traffic_multiplier,
    get_cusco_traffic_by_hour,
    get_current_cusco_traffic,
    load_traffic_snapshot,
    save_traffic_snapshot,
)


def test_traffic_schedule_rush_hour():
    morning_rush = get_cusco_traffic_by_hour(8.0)
    assert morning_rush.level == "hora_punta"
    assert morning_rush.is_rush_hour is True
    assert morning_rush.base_multiplier == pytest.approx(2.20)

    lunch_rush = get_cusco_traffic_by_hour(13.0)
    assert lunch_rush.level == "alto"
    assert lunch_rush.is_rush_hour is True

    night_flow = get_cusco_traffic_by_hour(23.0)
    assert night_flow.level == "fluido"
    assert night_flow.is_rush_hour is False
    assert night_flow.base_multiplier == pytest.approx(1.00)


def test_traffic_multiplier_street_sensitivity():
    obs = TrafficObservation(
        observed_at="2026-10-28T12:00",
        level="alto",
        base_multiplier=1.65,
        description="Denso",
        is_rush_hour=True,
        hour_of_day=12.0,
    )
    # Centro histórico saturates more than residential
    mult_centro = calculate_traffic_multiplier(obs, street_type="calle_centro")
    mult_residencial = calculate_traffic_multiplier(obs, street_type="calle_residencial")
    assert mult_centro > mult_residencial


def test_traffic_weather_synergy():
    obs = TrafficObservation(
        observed_at="2026-10-28T12:00",
        level="moderado",
        base_multiplier=1.25,
        description="Moderado",
        is_rush_hour=False,
        hour_of_day=10.0,
    )
    mult_dry = calculate_traffic_multiplier(obs, "avenida", weather_multiplier=1.0)
    mult_rain = calculate_traffic_multiplier(obs, "avenida", weather_multiplier=1.25)
    assert mult_rain > mult_dry


def test_traffic_snapshot_persistence(tmp_path):
    path = tmp_path / "traffic_snapshot.json"
    obs = get_cusco_traffic_by_hour(8.5)
    saved = save_traffic_snapshot(path, obs)
    assert saved.exists()

    loaded = load_traffic_snapshot(path)
    assert loaded.cached is True
    assert loaded.level == obs.level
    assert loaded.base_multiplier == obs.base_multiplier


class FlowResponse:
    def __init__(self, flow):
        self.flow = flow

    def raise_for_status(self):
        return None

    def json(self):
        return {"flowSegmentData": self.flow}


class FlowSession:
    def __init__(self, response):
        self.response = response

    def get(self, *_args, **_kwargs):
        return self.response


def test_tomtom_uses_only_reported_speeds():
    client = TomTomTrafficClient(api_key="clave-de-prueba", session=FlowSession(
        FlowResponse({"currentSpeed": 18, "freeFlowSpeed": 36})
    ))
    assert client.fetch_flow() == {
        "current_speed_kmh": 18, "free_flow_speed_kmh": 36,
        "multiplier": 2.0, "confidence": None, "road_closure": None,
    }


@pytest.mark.parametrize("flow", [
    {}, {"currentSpeed": 30}, {"currentSpeed": 0, "freeFlowSpeed": 40},
    {"currentSpeed": float("nan"), "freeFlowSpeed": 40},
])
def test_tomtom_does_not_invent_missing_or_invalid_speeds(flow):
    client = TomTomTrafficClient(api_key="clave-de-prueba", session=FlowSession(FlowResponse(flow)))
    assert client.fetch_flow() is None


def test_tomtom_failure_does_not_expose_api_key():
    class FailingSession:
        def get(self, *_args, **_kwargs):
            raise requests.ConnectionError("URL incluye key=clave-de-prueba")

    client = TomTomTrafficClient(api_key="clave-de-prueba", session=FailingSession())
    assert client.fetch_flow() is None
