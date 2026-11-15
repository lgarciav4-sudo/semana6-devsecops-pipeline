#!/usr/bin/env python3
"""Puerta de calidad SAST + SCA. Entrada real: Semgrep JSON y Dependency-Check JSON."""
import argparse
import json
import sys
from pathlib import Path

LEVELS = {'INFO': 1, 'LOW': 2, 'MEDIUM': 3, 'MODERATE': 3, 'HIGH': 4, 'CRITICAL': 5}
SEMGREP = {'INFO': 'LOW', 'WARNING': 'MEDIUM', 'ERROR': 'HIGH'}


def read_json(filename):
    try:
        return json.loads(Path(filename).read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f'No se pudo leer el reporte obligatorio {filename}: {exc}') from exc


def normalized_severity(value, fallback_score=None):
    key = str(value or '').upper()
    if key in LEVELS:
        return key
    if fallback_score is not None:
        score = float(fallback_score)
        return 'CRITICAL' if score >= 9 else 'HIGH' if score >= 7 else 'MEDIUM' if score >= 4 else 'LOW'
    raise ValueError(f'Severidad desconocida: {value!r}; detener por seguridad')


def dc_severity(vulnerability):
    """Preferir severidad explícita NVD; usar CVSS solo si falta."""
    val = vulnerability.get('severity')
    if val:
        return normalized_severity(val)
    for k in ('cvssv3', 'cvssv4', 'cvssv2'):
        cvss = vulnerability.get(k) or {}
        score = cvss.get('baseScore')
        if score is not None:
            return normalized_severity(None, score)
    raise ValueError(f'Vulnerabilidad sin severidad ni CVSS: {vulnerability.get("name", "desconocida")}')


def evaluate(semgrep, dependency_check, threshold):
    if not isinstance(semgrep.get('results'), list):
        raise ValueError('Reporte Semgrep incompleto: falta results[]')
    if not isinstance(dependency_check.get('dependencies'), list):
        raise ValueError('Reporte Dependency-Check incompleto: falta dependencies[]')
    if semgrep.get('errors'):
        raise ValueError('Semgrep reportó errores de análisis; no se puede aprobar el build')
    if dependency_check.get('scanInfo', {}).get('analysisExceptions'):
        raise ValueError('Dependency-Check reportó excepciones de análisis')
    findings = []
    for issue in semgrep['results']:
        raw = (issue.get('extra') or {}).get('severity', '')
        severity = normalized_severity(SEMGREP.get(str(raw).upper(), raw))
        findings.append(('SAST / Semgrep', severity, issue.get('check_id', 'sin_regla')))
    for dep in dependency_check['dependencies']:
        for vuln in dep.get('vulnerabilities') or []:
            severity = dc_severity(vuln)
            findings.append(('SCA / Dependency-Check', severity, vuln.get('name', 'CVE sin nombre')))
    blocking = [f for f in findings if LEVELS[f[1]] >= LEVELS[threshold]]
    return findings, blocking


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--semgrep', required=True)
    p.add_argument('--dependency-check', required=True)
    p.add_argument('--fail-on', choices=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'], default='HIGH')
    args = p.parse_args()
    try:
        findings, blocking = evaluate(read_json(args.semgrep), read_json(args.dependency_check), args.fail_on)
    except (ValueError, TypeError, OverflowError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2
    print(f'Política: bloquear desde {args.fail_on}. Hallazgos: {len(findings)}; bloqueantes: {len(blocking)}.')
    for source, sev, rule in findings:
        print(f'  [{sev}] {source}: {rule}')
    if blocking:
        print('BUILD BLOQUEADO: se superó el umbral de severidad.')
        return 1
    print('BUILD APROBADO: ningún hallazgo supera el umbral configurado.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
