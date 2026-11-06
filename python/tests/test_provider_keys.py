"""La configuración privada permite sobrescribir la clave sin publicarla."""
from src.services import provider_keys


def test_local_env_and_process_override(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text("OPENWEATHERMAP_API_KEY=clave-clima\nTOMTOM_API_KEY=clave-trafico\n", encoding="utf-8")
    monkeypatch.setattr(provider_keys, "_ENV_FILE", env)
    monkeypatch.delenv("OPENWEATHERMAP_API_KEY", raising=False)
    monkeypatch.delenv("TOMTOM_API_KEY", raising=False)
    assert provider_keys.provider_key("tomtom") == "clave-trafico"
    assert provider_keys.provider_key("openweathermap") == "clave-clima"
    monkeypatch.setenv("TOMTOM_API_KEY", "clave-en-entorno")
    assert provider_keys.provider_key("tomtom") == "clave-en-entorno"
    monkeypatch.setenv("TOMTOM_API_KEY", "")
    assert provider_keys.provider_key("tomtom") == ""
