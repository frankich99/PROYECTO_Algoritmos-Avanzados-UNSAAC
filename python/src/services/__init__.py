"""Integraciones externas aisladas del núcleo algorítmico."""
from src.services.traffic import (
    TrafficObservation,
    calculate_traffic_multiplier,
    get_current_cusco_traffic,
    get_traffic_by_schedule,
    load_traffic_snapshot,
    save_traffic_snapshot,
)
from src.services.weather import (
    DEFAULT_OWM_API_KEY,
    OpenMeteoClient,
    OpenWeatherMapClient,
    WeatherImpactCoefficients,
    WeatherObservation,
    WeatherServiceError,
    get_default_owm_key,
    load_snapshot as load_weather_snapshot,
    save_snapshot as save_weather_snapshot,
    weather_multiplier,
)
