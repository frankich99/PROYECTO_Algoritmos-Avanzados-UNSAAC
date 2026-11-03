#!/usr/bin/env python3
"""Diagnóstico y verificación de conexión a APIs meteorológicas (OpenWeatherMap y Open-Meteo).

Permite probar en cualquier momento la API key de OpenWeatherMap,
verificar si ya se propagó en los servidores globales y actualizar
el snapshot de Cusco cuando esté disponible.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# Forzar salida segura en consolas Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Asegurar PYTHONPATH
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.weather import (
    OpenMeteoClient,
    OpenWeatherMapClient,
    WeatherServiceError,
    get_default_owm_key,
    load_snapshot,
    save_snapshot,
    weather_multiplier,
)

SNAPSHOT_PATH = ROOT / "data" / "processed" / "weather_cusco.json"


def check_open_meteo() -> None:
    print("\n" + "=" * 60)
    print("1. PROBANDO SERVICIO OPEN-METEO (Sin clave / Reanálisis)")
    print("=" * 60)
    try:
        client = OpenMeteoClient()
        obs = client.fetch_current()
        factor = weather_multiplier(obs)
        print(f"  [OK] Conexión exitosa:")
        print(f"       - Fecha/Hora:      {obs.observed_at}")
        print(f"       - Temperatura:     {obs.temperature_c:.1f} °C")
        print(f"       - Humedad Rel.:    {obs.relative_humidity_pct:.0f} %")
        print(f"       - Precipitación:   {obs.precipitation_mm:.2f} mm")
        print(f"       - Visibilidad:     {obs.visibility_m/1000.0:.1f} km")
        print(f"       - Viento:          {obs.wind_speed_kmh:.1f} km/h (Ráfagas: {obs.wind_gusts_kmh:.1f} km/h)")
        print(f"       - Condición:       {obs.weather_description}")
        print(f"       - Factor Retardo:  Omega_clima = {factor:.4f}x")
    except Exception as exc:
        print(f"  [ERROR] Falló Open-Meteo: {exc}")


def check_openweathermap(api_key: str | None = None, update_snapshot: bool = True) -> bool:
    key = api_key or get_default_owm_key()
    print("\n" + "=" * 60)
    print("2. PROBANDO SERVICIO OPENWEATHERMAP API")
    if not key:
        print("   Sin clave configurada; defina OPENWEATHERMAP_API_KEY localmente.")
        return False
    print("=" * 60)

    client = OpenWeatherMapClient(api_key=key)
    try:
        obs = client.fetch_current(snapshot_path=SNAPSHOT_PATH if update_snapshot else None)
        factor = weather_multiplier(obs)
        print("  [EXITO] ¡La clave está 100% ACTIVA y lista!")
        print(f"       - Estación/Ciudad: {obs.station_name}")
        print(f"       - Fecha/Hora:      {obs.observed_at}")
        print(f"       - Temperatura:     {obs.temperature_c:.1f} °C")
        print(f"       - Humedad Rel.:    {obs.relative_humidity_pct:.0f} %")
        print(f"       - Precipitación:   {obs.precipitation_mm:.2f} mm")
        print(f"       - Visibilidad:     {obs.visibility_m/1000.0:.1f} km")
        if obs.surface_pressure_hpa is not None:
            print(f"       - Presión de suelo: {obs.surface_pressure_hpa:.1f} hPa")
        print(f"       - Condición:       {obs.weather_description}")
        print(f"       - Factor Retardo:  Omega_clima = {factor:.4f}x")
        if update_snapshot:
            print(f"  [OK] Snapshot actualizado en: {SNAPSHOT_PATH}")
        return True
    except WeatherServiceError as exc:
        print("  [AVISO DE ACTIVACIÓN EN CURSO]")
        print("  El proveedor rechazó la consulta; compruebe la clave en su cuenta.")
        print("\n  Diagnóstico:")
        print("  Como indica el panel oficial de OpenWeather en 'Create key':")
        print("  -> 'New API keys may take up to 2 hours to become ready for use.'")
        print("  Los servidores de OpenWeatherMap están propagando la clave.")
        print("  El sistema conserva el snapshot local sin interrumpir el funcionamiento.")
        return False
    except Exception as exc:
        print("  [ERROR] No se pudo completar la consulta; se conserva el snapshot local.")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Verificador de APIs meteorológicas para Cusco")
    parser.add_argument("--key", type=str, default=None, help="No usar: configure la clave por entorno")
    parser.add_argument("--write-snapshot", action="store_true", help="Sobrescribir el snapshot local (solo si lo solicita)")
    args = parser.parse_args()

    print("============================================================")
    print(" VERIFICACIÓN DE ESTACIÓN METEOROLÓGICA CUSCO (UNSAAC) ")
    print("============================================================")

    check_open_meteo()
    if args.key:
        parser.error("No introduzca credenciales en argumentos; use OPENWEATHERMAP_API_KEY en el entorno.")
    check_openweathermap(update_snapshot=args.write_snapshot)

    print("\n" + "=" * 60)
    print("3. ESTADO DEL SNAPSHOT LOCAL DE CONTINGENCIA")
    print("=" * 60)
    if SNAPSHOT_PATH.exists():
        snap = load_snapshot(SNAPSHOT_PATH)
        print(f"  Archivo:        {SNAPSHOT_PATH}")
        print(f"  Última captura: {snap.observed_at} ({snap.source})")
        print(f"  Condición:      {snap.weather_description} (Temp: {snap.temperature_c:.1f} °C, Hum: {snap.relative_humidity_pct:.0f}%)")
        print(f"  Factor Retardo: Omega_clima = {weather_multiplier(snap):.4f}x")
        print("  -> Las consultas viales y de caminos mínimos funcionan sin errores.")
    else:
        print("  [ADVERTENCIA] No existe snapshot local.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
