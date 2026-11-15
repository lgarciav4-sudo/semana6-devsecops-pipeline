#!/usr/bin/env bash
# Análisis SCA con OWASP Dependency-Check.
# La actualización NVD y el escaneo están separados: un fallo de red no borra
# una base ya descargada, y el escaneo usa --noupdate.
set -euo pipefail

VERSION="13.0.0"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="${ODC_DATA_DIR:-$ROOT/odc-data}"
REPORT_DIR="${ODC_REPORT_DIR:-$ROOT/reports}"
SCAN_DIR="${ODC_SCAN_DIR:-$ROOT/app}"
INSTALL_DIR="${ODC_INSTALL_DIR:-$ROOT/.tools/dependency-check}"
SKIP_UPDATE="${ODC_SKIP_UPDATE:-false}"

mkdir -p "$DATA_DIR" "$REPORT_DIR" "$(dirname "$INSTALL_DIR")"

if ! command -v java >/dev/null 2>&1; then
  echo "ERROR: Java no está en PATH. Dependency-Check no puede ejecutarse." >&2
  exit 2
fi

if [[ ! -x "$INSTALL_DIR/bin/dependency-check.sh" ]]; then
  tmp="$(mktemp -d)"
  echo "Descargando OWASP Dependency-Check ${VERSION}."
  curl -fsSL \
    -o "$tmp/dc.zip" \
    "https://github.com/dependency-check/DependencyCheck/releases/download/v${VERSION}/dependency-check-${VERSION}-release.zip"
  unzip -q "$tmp/dc.zip" -d "$tmp"
  rm -rf "$INSTALL_DIR"
  mv "$tmp/dependency-check" "$INSTALL_DIR"
  rm -rf "$tmp"
  chmod +x "$INSTALL_DIR/bin/dependency-check.sh"
fi

DC="$INSTALL_DIR/bin/dependency-check.sh"

clean_locks() {
  find "$DATA_DIR" -maxdepth 2 -type f \( -name '*.lock.db' -o -name '*.lock' \) -delete 2>/dev/null || true
}

db_ready() {
  local match
  match="$(find "$DATA_DIR" -maxdepth 1 -type f -name '*.mv.db' -print -quit)"
  [[ -n "$match" ]]
}

require_api_key() {
  if [[ -z "${NVD_API_KEY:-}" ]]; then
    echo "ERROR: falta NVD_API_KEY. No se genera un reporte SCA ficticio." >&2
    exit 2
  fi
}

update_db() {
  local attempt
  require_api_key
  for attempt in 1 2 3; do
    clean_locks
    echo "Actualización NVD, intento ${attempt}/3. La clave no se imprime."
    if "$DC" \
        --updateonly \
        --data "$DATA_DIR" \
        --nvdApiKey "$NVD_API_KEY" \
        --nvdApiDelay 1000 \
        --nvdMaxRetryCount 8 \
        --nvdValidForHours 168; then
      return 0
    fi
    echo "La actualización NVD falló en el intento ${attempt}." >&2
    sleep $((attempt * 20))
  done
  return 1
}

run_scan() {
  clean_locks
  "$DC" \
    --project "Semana6-Secure-SDLC" \
    --scan "$SCAN_DIR" \
    --data "$DATA_DIR" \
    --out "$REPORT_DIR" \
    --format JSON \
    --format HTML \
    --noupdate \
    --failOnCVSS 11 \
    --disableOssIndex \
    --disableYarnAudit \
    --disablePnpmAudit
}

echo "Dependency-Check ${VERSION}. Directorio de datos: ${DATA_DIR}"
clean_locks

if db_ready && [[ "$SKIP_UPDATE" == "true" ]]; then
  echo "Caché NVD reutilizada. No se descarga la base de nuevo."
elif db_ready; then
  echo "Hay una base NVD previa. Se intenta una actualización incremental."
  if ! update_db; then
    echo "AVISO: la actualización NVD falló. El análisis continúa con la base local y --noupdate." >&2
  fi
else
  echo "No hay base NVD en caché. La descarga inicial es obligatoria."
  if ! update_db; then
    echo "ERROR: no se pudo construir la base NVD. No se inventan vulnerabilidades ni reportes." >&2
    exit 13
  fi
fi

if ! db_ready; then
  echo "ERROR: la base H2 no quedó disponible. No hay documentos NVD para un análisis real." >&2
  exit 13
fi

if ! run_scan; then
  if [[ "$SKIP_UPDATE" == "true" ]]; then
    echo "El análisis con la caché falló. Se intenta actualizar la NVD una vez." >&2
    if ! update_db || ! db_ready || ! run_scan; then
      echo "ERROR técnico de Dependency-Check. No se afirma que el código esté libre de vulnerabilidades." >&2
      exit 13
    fi
  else
    echo "ERROR técnico de Dependency-Check durante el análisis." >&2
    exit 13
  fi
fi

python3 - "$REPORT_DIR" <<'PY'
import json
import sys
from collections import Counter
from pathlib import Path

report_dir = Path(sys.argv[1])
json_path = report_dir / "dependency-check-report.json"
html_path = report_dir / "dependency-check-report.html"
if not json_path.is_file() or json_path.stat().st_size < 50:
    sys.exit("ERROR: dependency-check-report.json ausente o vacío")
if not html_path.is_file() or html_path.stat().st_size < 50:
    sys.exit("ERROR: dependency-check-report.html ausente o vacío")
data = json.loads(json_path.read_text(encoding="utf-8"))
dependencies = data.get("dependencies")
if not isinstance(dependencies, list):
    sys.exit("ERROR: el JSON no contiene dependencies[]")
exceptions = (data.get("scanInfo") or {}).get("analysisExceptions") or []
if exceptions:
    sys.exit(f"ERROR: Dependency-Check reportó excepciones de análisis: {len(exceptions)}")
counts = Counter()
vulnerable = 0
for dep in dependencies:
    vulns = dep.get("vulnerabilities") or []
    if vulns:
        vulnerable += 1
    for vuln in vulns:
        counts[str(vuln.get("severity") or "DESCONOCIDA").upper()] += 1
print(f"Reporte SCA válido. Dependencias: {len(dependencies)}. Con vulnerabilidades: {vulnerable}.")
if counts:
    print("Hallazgos por severidad: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
else:
    print("Dependency-Check no reportó vulnerabilidades en las dependencias analizadas.")
PY

touch "$DATA_DIR/CACHE_OK"
echo "Análisis SCA terminado. El bloqueo del build lo decide scripts/security_gate.py."
