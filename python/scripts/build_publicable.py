"""Genera el paquete publicable de la web y la API en un solo servicio."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
NAME = f"rutas-cusco-v{VERSION}"
OUTPUT = ROOT / "dist_publicable"
TARGET = OUTPUT / NAME
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".mypy_cache")


def copy_tree(source: Path, destination: Path) -> None:
    if not source.is_dir():
        raise SystemExit(f"Falta la carpeta requerida: {source}")
    shutil.copytree(source, destination, ignore=IGNORE)


def write(path: Path, content: str, executable: bool = False) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")
    if executable:
        path.chmod(0o755)


def build() -> Path:
    dist = ROOT / "web" / "dist"
    if not (dist / "index.html").is_file():
        raise SystemExit("Falta web/dist. Ejecute primero: cd web && npm ci && npm run build")

    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(parents=True)

    copy_tree(ROOT / "python" / "src", TARGET / "python" / "src")
    copy_tree(ROOT / "python" / "data" / "processed", TARGET / "python" / "data" / "processed")
    copy_tree(ROOT / "python" / "data" / "instances", TARGET / "python" / "data" / "instances")
    copy_tree(dist, TARGET / "web" / "dist")
    shutil.copy2(ROOT / "python" / "web_api.py", TARGET / "python" / "web_api.py")
    shutil.copy2(ROOT / "CHANGELOG.md", TARGET / "CHANGELOG.md")
    shutil.copy2(ROOT / "VERSION", TARGET / "VERSION")

    docs = TARGET / "docs"
    docs.mkdir()
    shutil.copy2(ROOT / "docs" / "DATOS_Y_MODELO.md", docs / "DATOS_Y_MODELO.md")

    write(TARGET / "requirements-runtime.txt", "\n".join([
        "fastapi>=0.115.0",
        "uvicorn>=0.30.0",
        "requests>=2.31.0",
        "networkx>=3.2.0",
        "",
    ]))
    write(TARGET / "Procfile",
          "web: uvicorn web_api:app --app-dir python --host 0.0.0.0 --port $PORT\n")
    write(TARGET / ".dockerignore", "\n".join([
        ".venv/",
        "__pycache__/",
        "*.py[cod]",
        ".pytest_cache/",
        "",
    ]))
    write(TARGET / "Dockerfile", "\n".join([
        "FROM python:3.12-slim",
        "ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1",
        "WORKDIR /app",
        "COPY requirements-runtime.txt .",
        "RUN pip install --no-cache-dir -r requirements-runtime.txt",
        "COPY . .",
        "EXPOSE 8000",
        'CMD ["sh", "-c", "uvicorn web_api:app --app-dir python --host 0.0.0.0 --port ${PORT:-8000}"]',
        "",
    ]))
    write(TARGET / "iniciar.ps1", "\n".join([
        '$ErrorActionPreference = "Stop"',
        "Set-Location $PSScriptRoot",
        'if (-not (Test-Path ".venv")) { python -m venv .venv }',
        ".\\\\.venv\\\\Scripts\\\\python.exe -m pip install --disable-pip-version-check -r requirements-runtime.txt",
        '$port = if ($env:PORT) { $env:PORT } else { "8000" }',
        ".\\\\.venv\\\\Scripts\\\\python.exe -m uvicorn web_api:app --app-dir python --host 0.0.0.0 --port $port",
        "",
    ]))
    write(TARGET / "iniciar.sh", "\n".join([
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        'cd "$(dirname "$0")"',
        "if [ ! -d .venv ]; then python3 -m venv .venv; fi",
        ". .venv/bin/activate",
        "pip install --disable-pip-version-check -r requirements-runtime.txt",
        'exec uvicorn web_api:app --app-dir python --host 0.0.0.0 --port "${PORT:-8000}"',
        "",
    ]), executable=True)

    write(TARGET / "README.md", f"""# Rutas mínimas en Cusco · publicable v{VERSION}

Paquete autónomo con la API FastAPI y la interfaz React ya compilada. Un solo
proceso sirve la web en `/` y la API en `/api/v1`.

## Ejecutar en Windows

```powershell
.\\iniciar.ps1
```

## Ejecutar en Linux o macOS

```bash
chmod +x iniciar.sh
./iniciar.sh
```

Abrir <http://127.0.0.1:8000/>. Documentación de la API: `/docs`.

## Docker

```bash
docker build -t rutas-cusco:{VERSION} .
docker run --rm -p 8000:8000 -e PORT=8000 rutas-cusco:{VERSION}
```

## Proveedores cloud

Comando de arranque:

```text
uvicorn web_api:app --app-dir python --host 0.0.0.0 --port $PORT
```

El `Procfile` y el `Dockerfile` incluidos permiten desplegar en Render,
Railway, Fly.io o un VPS. Verifique `/api/v1/health` y `/api/v1/version`.

## Variables

- `PORT`: puerto de escucha (por defecto `8000`).
- `RUTAS_CORS_ORIGINS`: orígenes permitidos si la web está en otro dominio.
- `RUTAS_WEB_DIST`: ruta alternativa del build web.

## Advertencia

La API ejecuta algoritmos que consumen CPU y puede consultar proveedores
externos. No la exponga a Internet sin autenticación y límites de tráfico.
No guarde claves en archivos del proyecto.

Los resultados canónicos están en `python/data/processed/` y no se modifican
al usar la web. Las consultas y experimentos nuevos son resultados de sesión.
""")

    manifest = {
        "name": NAME,
        "version": VERSION,
        "python": "3.12",
        "start": "uvicorn web_api:app --app-dir python --host 0.0.0.0 --port $PORT",
        "web": "web/dist",
        "data": "python/data/processed",
    }
    (TARGET / "publicable.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    archive = shutil.make_archive(str(OUTPUT / NAME), "zip", root_dir=OUTPUT, base_dir=NAME)
    return Path(archive)


if __name__ == "__main__":
    archive = build()
    size_mb = archive.stat().st_size / (1024 * 1024)
    print(f"Paquete: {TARGET}")
    print(f"ZIP:     {archive} ({size_mb:.2f} MB)")
