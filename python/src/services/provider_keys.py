"""Credenciales locales de proveedores; nunca se envían al cliente."""

import os
from pathlib import Path
from typing import Literal


Provider = Literal["openweathermap", "tomtom"]
_NAMES = {"openweathermap": "OPENWEATHERMAP_API_KEY", "tomtom": "TOMTOM_API_KEY"}
_DEFAULTS = {
    "openweathermap": "e0cd9ce83348676c0ef4a46aa041e194",
    "tomtom": "jFzYvp3UJmio3PeiTkKQCBqebIFhKHMO",
}
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
    return _DEFAULTS.get(provider, "")
