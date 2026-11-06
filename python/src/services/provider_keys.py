"""Credenciales locales de proveedores; nunca se envían al cliente."""

import os
from pathlib import Path
from typing import Literal


Provider = Literal["openweathermap", "tomtom"]
_NAMES = {"openweathermap": "OPENWEATHERMAP_API_KEY", "tomtom": "TOMTOM_API_KEY"}
_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


def provider_key(provider: Provider) -> str:
    name = _NAMES[provider]
    if name in os.environ:
        return os.environ[name].strip()
    try:
        with _ENV_FILE.open(encoding="utf-8") as source:
            for line in source:
                key, _, value = line.partition("=")
                if key.strip() == name:
                    return value.strip().strip('"\'')
    except (OSError, UnicodeError):
        pass
    return ""
