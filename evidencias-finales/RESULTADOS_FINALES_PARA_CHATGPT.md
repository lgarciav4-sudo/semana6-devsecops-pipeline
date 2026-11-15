# RESULTADOS FINALES PARA CHATGPT — SEMANA 6

Usar estos datos para el PowerPoint. No completar huecos con vulnerabilidades que no estén aquí.

- Repositorio: https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline
- Rama: `main`
- Commit del análisis verificado: `04e4bc33e98279d4d8151eaab0c04d635c3f7332`
- Ejecución: https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline/actions/runs/43670979336
- Inicio: 2026-11-15T03:08:21Z. Fin: 2026-11-15T03:09:54Z
- Conclusión del workflow: `failure`, porque la política devolvió código 1

## Resultado de cada etapa

| Etapa | Resultado |
| --- | --- |
| Pruebas de la política | success. 13 pruebas, OK, 0.197 s |
| SAST Semgrep 1.185.0 | success. 209 reglas, 5 archivos, 3 hallazgos, `errors` vacío |
| SBOM Syft 1.42.3 | success. CycloneDX 1.6, 53 componentes |
| SCA Dependency-Check 13.0.0 | success. 10 dependencias, 8 con avisos, 22 vulnerabilidades. Actualización NVD del espejo oficial: 57 s. Análisis: 2 s |
| Política HIGH/CRITICAL | failure esperada. 25 hallazgos, 11 bloqueantes, código 1, texto `BUILD BLOQUEADO: se superó el umbral de severidad.` |

## Hallazgos reales de Semgrep

Conversión de `security_gate.py`: INFO→LOW, WARNING→MEDIUM, ERROR→HIGH.

1. INFO, línea 18 de `app/src/server.js`. Regla `javascript.express.security.audit.express-check-csurf-middleware-usage.express-check-csurf-middleware-usage`. Falta middleware CSRF. No bloquea.
2. ERROR, línea 40. Regla `javascript.lang.security.detect-child-process.detect-child-process`. `child_process` con datos del request. Se convierte a HIGH y bloquea.
3. WARNING, línea 48. Regla `javascript.lang.security.audit.md5-used-as-password.md5-used-as-password`. MD5 como hash de contraseña. Se convierte a MEDIUM y no bloquea.

## Dependency-Check

Origen de los 22 avisos en el JSON: `NPM`. La caché NVD sí se descargó; `scanInfo` marca última modificación `2026-11-14T16:17:04Z`. No hay `analysisExceptions`.

Severidad del JSON: 1 critical, 9 high, 6 moderate, 6 low.

Directas: `express@4.17.1` (2 avisos) y `lodash@4.17.11` (6 avisos, incluido CRITICAL CVE-2019-10744, CVSS 9.1, GHSA-jf85-cpcp-j695, versiones anteriores a 4.17.12).

Transitivas con avisos: body-parser 1.19.0, cookie 0.4.0, path-to-regexp 0.1.7, qs 6.7.0, send 0.17.1, serve-static 1.14.1.

El aviso GHSA-pxg6-pf52-xh8x de cookie 0.4.0 no trae CVE. El resto de los avisos sí incluyen uno o más CVE en el JSON. La tabla completa está en `INFORME_FINAL_SEMANA6.md`.

## SBOM

`sbom.cyclonedx.json`: JSON válido, `bomFormat` CycloneDX, `specVersion` 1.6, 53 componentes.

## Política

- Umbral HIGH.
- Ejemplo bajo: BUILD APROBADO, código 0.
- Ejemplo HIGH: BUILD BLOQUEADO, código 1.
- Reportes reales: BUILD BLOQUEADO, código 1.
- Reporte ausente o inválido: código 2, sin afirmar que el código está limpio.
- No se bajó el umbral para poner el workflow en verde.

## Errores técnicos

Resueltos en la ejecución de referencia:

- Run 43658501440: Docker, bloqueo exclusivo de H2 y `No documents exist`, código 13.
- Run 43668921377: NVD respondió que el secreto `NVD_API_KEY` no es válido. No se muestra la clave.
- Run 43669591176: bash recortó `{0}` en la URL del espejo.

Pendiente: sustituir `NVD_API_KEY` en GitHub Settings por una clave vigente de https://nvd.nist.gov/developers/request-an-api-key si se quiere usar la API directa. El análisis verificado usa el espejo oficial `https://dependency-check.github.io/DependencyCheck_Builder/nvd_cache/nvdcve-{0}.json.gz` y no envía el secreto.

## Archivos de esta carpeta

- `INFORME_FINAL_SEMANA6.md`
- `GUIA_PRESENTACION_7_MINUTOS.md`
- `RESULTADOS_FINALES_PARA_CHATGPT.md`
- `resumen-workflow.txt`
- `semgrep.json`
- `dependency-check-report.json`
- `dependency-check-report.html`
- `sbom.cyclonedx.json`
- `sbom-resumen.txt`
- `unit-tests.txt`
- `politica-real.txt`
- `politica-real.exit`
- `politica-simulada-aprobada.txt`
- `politica-simulada-bloqueada.txt`

El ZIP `SEMANA6_EVIDENCIAS_FINALES.zip` contiene esta carpeta y no incluye secretos.
