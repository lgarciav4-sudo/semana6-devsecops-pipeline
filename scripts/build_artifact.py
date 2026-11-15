#!/usr/bin/env python3
"""Empaqueta app/ en dist/semana7-app.zip y escribe la procedencia declarada."""
import hashlib
import json
import os
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "app"
DIST = ROOT / "dist"
ZIP_NAME = "semana7-app.zip"
SKIP_DIRS = {"node_modules", "__pycache__", ".git"}


def git_value(*args):
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def listed_files():
    files = []
    for path in SOURCE.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(SOURCE).parts):
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(SOURCE).as_posix())


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    if not SOURCE.is_dir():
        raise SystemExit(f"No existe el directorio de la aplicación: {SOURCE}")
    files = listed_files()
    if not files:
        raise SystemExit("app/ no contiene archivos para empaquetar.")
    DIST.mkdir(exist_ok=True)
    archive = DIST / ZIP_NAME
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in files:
            bundle.write(path, path.relative_to(SOURCE).as_posix())
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    workflow = os.environ.get("GITHUB_WORKFLOW", "")
    ref = os.environ.get("GITHUB_REF", git_value("rev-parse", "--abbrev-ref", "HEAD"))
    sha = os.environ.get("GITHUB_SHA", git_value("rev-parse", "HEAD"))
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    provenance = {
        "tipo": "procedencia-declarada",
        "artefacto": ZIP_NAME,
        "sha256": sha256(archive),
        "tamano_bytes": archive.stat().st_size,
        "archivos": [path.relative_to(SOURCE).as_posix() for path in files],
        "repositorio": repository or git_value("config", "--get", "remote.origin.url"),
        "commit": sha,
        "ref": ref,
        "workflow": workflow,
        "archivo_workflow": ".github/workflows/semana7-cosign.yml",
        "ejecucion": run_id,
        "url_ejecucion": (
            f"{server}/{repository}/actions/runs/{run_id}" if repository and run_id else ""
        ),
        "actor": os.environ.get("GITHUB_ACTOR", ""),
        "evento": os.environ.get("GITHUB_EVENT_NAME", "local"),
        "emisor_oidc_esperado": "https://token.actions.githubusercontent.com",
        "identidad_esperada": os.environ.get("EXPECTED_IDENTITY", ""),
        "sistema": os.environ.get("RUNNER_OS", os.name),
        "arquitectura": os.environ.get("RUNNER_ARCH", ""),
        "herramienta": "scripts/build_artifact.py",
        "entradas": ["app/"],
        "fecha_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    manifest = DIST / "provenance.json"
    manifest.write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Artefacto: {archive}")
    print(f"SHA-256: {provenance['sha256']}")
    print(f"Procedencia: {manifest}")
    print(f"Archivos empaquetados: {len(files)}")


if __name__ == "__main__":
    main()
