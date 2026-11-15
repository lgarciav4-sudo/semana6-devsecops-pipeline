#!/usr/bin/env python3
"""Resume el certificado y el registro de transparencia de un bundle de Cosign."""
import base64
import json
import subprocess
import sys
from pathlib import Path


def text_from_der(der_path):
    result = subprocess.run(
        ["openssl", "x509", "-inform", "DER", "-in", str(der_path), "-noout", "-text"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Uso: resumir_firma.py <bundle.json> <salida.txt>")
    bundle_path = Path(sys.argv[1])
    output = Path(sys.argv[2])
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    material = bundle.get("verificationMaterial") or {}
    certificate = (material.get("certificate") or {}).get("rawBytes")
    if not certificate:
        raise SystemExit("El bundle no contiene el certificado de Fulcio.")
    der_path = output.with_suffix(".der")
    der_path.write_bytes(base64.b64decode(certificate))
    certificate_text = text_from_der(der_path)
    entries = material.get("tlogEntries") or []
    lines = [
        f"Bundle: {bundle_path.name}",
        f"mediaType: {bundle.get('mediaType', '')}",
        f"Entradas en el registro de transparencia: {len(entries)}",
    ]
    for index, entry in enumerate(entries, start=1):
        lines.append(f"logIndex[{index}]: {entry.get('logIndex', '')}")
        lines.append(f"integratedTime[{index}]: {entry.get('integratedTime', '')}")
    lines.extend(["", "Certificado de corta duración:", certificate_text.rstrip()])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Resumen de identidad: {output}")


if __name__ == "__main__":
    main()
