# Informe final — Semana 6: pipeline SAST, SCA y SBOM

## 1. Objetivo del laboratorio

Construir y ejecutar un pipeline de DevSecOps que analice el código con Semgrep (SAST), las dependencias con OWASP Dependency-Check (SCA), genere un SBOM CycloneDX con Syft y bloquee el build cuando aparezca un hallazgo HIGH o CRITICAL.

Repositorio de trabajo: https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline

Referencia original: https://github.com/kbcasurf/secure-sdlc-pipeline

La aplicación de `app/` es un demo vulnerable a propósito. No debe desplegarse.

## 2. Herramientas utilizadas

| Herramienta | Versión verificada | Función |
| --- | --- | --- |
| Semgrep | 1.185.0, reglas `p/default` | SAST sobre `app/` |
| OWASP Dependency-Check | 13.0.0 | SCA sobre las dependencias npm |
| Syft, mediante `anchore/sbom-action` v0.24.0 | Syft 1.42.3 | SBOM CycloneDX JSON |
| `scripts/security_gate.py` | política del repositorio | Bloqueo desde HIGH |
| Python | 3.12 en GitHub Actions | Pruebas y política |
| Java Temurin | 21 | Runtime de Dependency-Check |

## 3. Arquitectura y funcionamiento del pipeline

El workflow `.github/workflows/semana6-sast-sca.yml` separa el trabajo en cinco jobs. SAST, SBOM, SCA y las pruebas unitarias corren en paralelo. La generación del SBOM no espera a Dependency-Check.

```text
push o workflow_dispatch
        |
        +-- Pruebas de la política
        +-- SAST Semgrep --------------+
        +-- SBOM Syft                  |
        +-- SCA Dependency-Check ------+
                                       |
                                       v
                          Política HIGH/CRITICAL
```

La política descarga los JSON reales de Semgrep y Dependency-Check. Si falta un reporte, el JSON es inválido o la herramienta reportó un error de análisis, el script sale con código 2. Si hay hallazgos en el umbral o por encima, sale con código 1 y el mensaje `BUILD BLOQUEADO`. Si no los hay, sale con código 0.

El umbral configurado es `HIGH`. No se bajó para obtener una marca verde.

## 4. Configuración implementada

- Semgrep 1.185.0 con `--config p/default`, `--metrics=off` y salida `reports/semgrep.json`. Un hallazgo (código 1 de Semgrep) no tumba el job: la política decide después. Un error técnico de Semgrep sí lo tumba.
- Dependency-Check 13.0.0, fijado por la URL del release. El escaneo usa `--noupdate` y `--failOnCVSS 11`, de modo que las vulnerabilidades no hacen fallar la herramienta. La decisión queda en `security_gate.py`.
- La base NVD se guarda con `actions/cache` bajo la clave semanal `odc-nvd-13.0.0`. Si la caché de esa semana ya existe, no se vuelve a descargar.
- El SBOM se genera después de `npm ci --ignore-scripts`, para que Syft vea `package-lock.json` y `node_modules`.
- Los reportes se publican como artifacts aunque un job posterior falle. Retención: 15 días.
- Los cambios que solo tocan `evidencias/` o `evidencias-finales/` no relanzan este workflow.

## 5. Errores encontrados y correcciones aplicadas

### 5.1 Bloqueo H2 y base vacía

Ejecución: https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline/actions/runs/43658501440

Duración aproximada: 40 minutos. Código de salida: 13.

Semgrep sí terminó en esa ejecución: 209 reglas, 5 archivos y 3 hallazgos. Dependency-Check, en la imagen Docker `owasp/dependency-check:latest`, montó un directorio vacío del runner sobre `/usr/share/dependency-check/data`. El proceso no pudo obtener el bloqueo exclusivo de H2, la actualización no dejó documentos y el análisis se detuvo con estos mensajes:

- `Unable to update 1 or more Cached Web DataSource`
- `Unable to obtain an exclusive lock on the H2 database to perform updates`
- `No documents exist`

Corrección: el SCA dejó de usar ese montaje Docker. El CLI 13.0.0 corre sobre el sistema de archivos del runner, limpia archivos de bloqueo previos y separa la actualización de la base del escaneo con `--noupdate`.

### 5.2 La API de NVD rechazó el secreto

Ejecución: https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline/actions/runs/43668921377

El secreto `NVD_API_KEY` existe en GitHub Actions, pero la API respondió `Invalid API Key`. No se imprime ni se incluye la clave en este informe. El job salió con código 13 y no se fabricó un reporte.

Corrección: la actualización usa el espejo oficial documentado por Dependency-Check, construido desde la NVD:

`https://dependency-check.github.io/DependencyCheck_Builder/nvd_cache/nvdcve-{0}.json.gz`

El workflow ya no inyecta `NVD_API_KEY` en el job, para no reenviar una clave rechazada. El secreto sigue guardado en GitHub. Para volver a la API directa hay que sustituirlo por una clave vigente solicitada en https://nvd.nist.gov/developers/request-an-api-key, sin pegarla en el chat ni en el repositorio.

### 5.3 La URL del espejo quedó cortada

Ejecución: https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline/actions/runs/43669591176

La asignación `${VAR:-...nvdcve-{0}.json.gz}` usó la primera `}` como cierre de la expansión. Dependency-Check recibió `nvdcve-{0.json.gz}` y rechazó la URL. La corrección guarda la plantilla entre comillas simples.

### 5.4 SBOM sin dependencias

En el primer intento Syft produjo un CycloneDX válido, pero solo describía la carpeta `./app`: no había `package-lock.json` ni `node_modules`. Después de resolver las dependencias con npm, el mismo job validó 53 componentes.

## 6. Resultados reales del análisis SAST

Fuente: artifact `semgrep-report` de la ejecución 43670979336, archivo `semgrep.json`. El log del job confirma: `Ran 209 rules on 5 files: 3 findings.`

Archivos analizados: `app/Dockerfile`, `app/README.md`, `app/package.json`, `app/src/db.js`, `app/src/server.js`.

`errors` del JSON está vacío. Semgrep no reportó un fallo técnico.

La política no copia las etiquetas de Semgrep tal cual. `scripts/security_gate.py` convierte `INFO` a `LOW`, `WARNING` a `MEDIUM` y `ERROR` a `HIGH`.

| Semgrep | Regla | Archivo y línea | Conversión | ¿Bloquea en HIGH? |
| --- | --- | --- | --- | --- |
| INFO | `javascript.express.security.audit.express-check-csurf-middleware-usage.express-check-csurf-middleware-usage` | `app/src/server.js:18` | LOW | No |
| ERROR | `javascript.lang.security.detect-child-process.detect-child-process` | `app/src/server.js:40` | HIGH | Sí |
| WARNING | `javascript.lang.security.audit.md5-used-as-password.md5-used-as-password` | `app/src/server.js:48` | MEDIUM | No |

Riesgo y remediación, según el mensaje de cada regla:

1. CSRF. Semgrep no detectó un middleware como `csurf` o `csrf`. El riesgo es aceptar peticiones cambiando el estado sin validar un token o una cookie. Remediación: validar CSRF en las rutas que modifican datos.
2. Inyección de comandos. `exec` recibe datos de `req` en `GET /ping`. El riesgo es ejecutar comandos del sistema si el parámetro es controlable. Remediación: evitar `child_process` con entrada de usuario o usar una lista de argumentos, sin shell, y una allowlist.
3. MD5 como hash de contraseña. MD5 es rápido y no sirve para contraseñas. Remediación: usar bcrypt, scrypt o Argon2.

Estos tres hallazgos coinciden con el escaneo local previo guardado en `evidencias/semgrep.json`. El reporte que se entrega aquí es el del pipeline.

## 7. Resultados reales del análisis SCA

Fuente: artifact `dependency-check-report` de la misma ejecución.

Dependency-Check 13.0.0 descargó la caché NVD del espejo oficial. El log registra `Check for updates complete (57012 ms)` y `Analysis Complete (2 seconds)`. El reporte dice:

- Dependencias identificadas: 10.
- Dependencias con al menos un aviso: 8.
- Vulnerabilidades: 22.
- Origen de todas ellas en el JSON: `NPM`.
- `analysisExceptions`: no hay.
- Metadatos NVD del reporte: última modificación de la caché `2026-11-14T16:17:04Z`; comprobación durante el job `2026-11-15T03:08:33Z`.

Las dos dependencias directas de `app/package.json` son `express@4.17.1` y `lodash@4.17.11`. El resto son transitivas resueltas en el lockfile. `server.js` y `db.js` aparecen en el inventario, sin avisos.

El CVSS es el `baseScore` v3 del JSON, mostrado a un decimal. La versión de corrección solo se anota cuando el texto del propio aviso la menciona.

| Dependencia | Aviso | CVE en el JSON | Severidad | CVSS | Versión citada por el aviso |
| --- | --- | --- | --- | --- | --- |
| lodash 4.17.11 | GHSA-jf85-cpcp-j695 | CVE-2019-10744 | CRITICAL | 9.1 | anteriores a 4.17.12 |
| lodash 4.17.11 | GHSA-r5fr-rjxr-66jc | CVE-2021-23337, CVE-2026-4800 | HIGH | 8.1 | 4.18.0 |
| lodash 4.17.11 | GHSA-p6mc-m468-83gw | CVE-2020-8203 | HIGH | 7.4 | anteriores a 4.17.19 |
| lodash 4.17.11 | GHSA-35jh-r3h4-6jhm | CVE-2021-23337 | HIGH | 7.2 | anteriores a 4.17.21 |
| lodash 4.17.11 | GHSA-xxjr-mmjv-4gpg | CVE-2025-13465 | MODERATE | 6.5 | 4.17.23 en `lodash`; 4.18.0 en paquetes sueltos |
| lodash 4.17.11 | GHSA-29mw-wpgm-hmr9 | CVE-2020-28500 | MODERATE | 5.3 | anteriores a 4.17.21 |
| body-parser 1.19.0 | GHSA-27r3-jxmh-p828 | CVE-2026-111181 | HIGH | 7.5 | 2.4.0 y 1.20.9 |
| body-parser 1.19.0 | GHSA-qwcr-r2fm-qrc7 | CVE-2024-45590 | HIGH | 7.5 | 1.20.3 |
| body-parser 1.19.0 | GHSA-v422-hmwv-36x6 | CVE-2026-12590 | LOW | 3.7 | 2.3.0 y 1.20.6 |
| path-to-regexp 0.1.7 | GHSA-37ch-88jc-xwx2 | CVE-2026-4867 | HIGH | 7.5 | 0.1.13 |
| path-to-regexp 0.1.7 | GHSA-9wv6-86v2-598j | CVE-2024-45296 | HIGH | 7.5 | 0.1.10 en la rama 0.1 |
| path-to-regexp 0.1.7 | GHSA-rhx6-c78j-4q9w | CVE-2024-45296, CVE-2024-52798 | HIGH | 7.5 | 0.1.12 |
| qs 6.7.0 | GHSA-hrpp-h998-j3pp | CVE-2022-24999 | HIGH | 7.5 | anteriores a 6.10.3 |
| qs 6.7.0 | GHSA-6pq8-jhm2-2vcw | CVE-2026-110816, CVE-2026-82417, CVE-2026-8723 | MODERATE | 5.3 | 6.16.1 |
| qs 6.7.0 | GHSA-4mjr-xmp4-gh2g | CVE-2026-82417 | MODERATE | 5.3 | el texto no indica una versión |
| qs 6.7.0 | GHSA-6rw7-vpxm-498p | CVE-2025-15284 | MODERATE | 3.7 | el texto no indica una versión |
| qs 6.7.0 | GHSA-w7fw-mjwx-w883 | CVE-2025-15284, CVE-2026-2391 | LOW | 3.7 | el texto no indica una versión |
| express 4.17.1 | GHSA-rv95-896h-c2vc | CVE-2024-29041 | MODERATE | 6.1 | afecta a versiones anteriores a 4.19.2 |
| express 4.17.1 | GHSA-qw6h-vgh9-j6wx | CVE-2024-43796 | LOW | 5.0 | 4.20.0 |
| cookie 0.4.0 | GHSA-pxg6-pf52-xh8x | no aparece un CVE | LOW | no trae baseScore | 0.7.0 |
| send 0.17.1 | GHSA-m6fv-jmcg-4jfg | CVE-2024-43799 | LOW | 5.0 | 0.19.0 |
| serve-static 1.14.1 | GHSA-cm22-4g7w-348p | CVE-2024-43800 | LOW | 5.0 | 1.16.0 |

Conteo por severidad del JSON: 1 critical, 9 high, 6 moderate y 6 low.

Para las dependencias directas, los avisos de lodash llegan a citar 4.18.0 y los de express citan correcciones en 4.19.2 y 4.20.0. body-parser, path-to-regexp, qs, cookie, send y serve-static entran por el árbol de express. La comprobación correcta después de subir versiones es volver a ejecutar Dependency-Check, no dar por cerrados los avisos solo con el número de versión.

## 8. Resultado de la generación de SBOM

Fuente: artifact `sbom-cyclonedx`.

- Archivo: `sbom.cyclonedx.json`.
- JSON válido.
- `bomFormat`: CycloneDX.
- `specVersion`: 1.6.
- Componentes: 53.
- Incluye, entre otros, `express` 4.17.1, `lodash` 4.17.11, `body-parser` 1.19.0, `qs` 6.7.0, `path-to-regexp` 0.1.7, `send` 0.17.1, `serve-static` 1.14.1 y `cookie` 0.4.0.
- La herramienta registrada en el SBOM es Syft 1.42.3.

El primer SBOM, de 401 bytes, solo tenía el componente raíz `./app`. No se usa como inventario final. El archivo entregado es el de 53 componentes.

## 9. Política de bloqueo por severidad

Umbral: HIGH.

Conversión Semgrep: INFO → LOW, WARNING → MEDIUM, ERROR → HIGH. `MODERATE` de npm se conserva y equivale al nivel de MEDIUM, así que no bloquea cuando el umbral es HIGH.

Sobre los reportes reales el script imprimió:

`Política: bloquear desde HIGH. Hallazgos: 25; bloqueantes: 11.`

`BUILD BLOQUEADO: se superó el umbral de severidad.`

Código de salida guardado en `politica-real.exit`: 1.

Los 11 bloqueantes son el ERROR de Semgrep, el CRITICAL de lodash y los 9 HIGH de SCA. Los LOW, MEDIUM y MODERATE no bloquean con este umbral.

En la misma ejecución, con reportes de ejemplo:

- Hallazgo INFO y SCA limpio: `BUILD APROBADO`, código 0.
- Hallazgo ERROR simulado: `BUILD BLOQUEADO`, código 1.

Un reporte ausente o inválido no se trata como código limpio. El script lanza un error y `main` termina con código 2.

## 10. Resultado de las pruebas

Pruebas locales, antes de publicar: 13 pruebas, resultado OK.

Pruebas del job `Pruebas de la política` en la ejecución 43670979336: 13 pruebas, 0.197 s, resultado OK. Salida completa en `unit-tests.txt`.

Cubren hallazgo HIGH de SAST, hallazgo HIGH de SCA, hallazgo por debajo del umbral, umbral LOW, CRITICAL, reporte inexistente, JSON inválido, reportes incompletos, errores de Semgrep, excepciones de análisis de Dependency-Check y la diferencia entre el código 1 (vulnerabilidad) y el código 2 (error técnico).

## 11. Estado final de GitHub Actions

Ejecución de referencia:

https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline/actions/runs/43670979336

Commit: `04e4bc33e98279d4d8151eaab0c04d635c3f7332` en `main`.

Inicio `2026-11-15T03:08:21Z`, fin `2026-11-15T03:09:54Z`.

| Job | Resultado |
| --- | --- |
| Pruebas de la política | success |
| SAST Semgrep | success |
| SBOM Syft | success |
| SCA Dependency-Check | success |
| Política HIGH/CRITICAL | failure, código 1 |

La conclusión del workflow es `failure` porque la política bloqueó el build. Los cuatro jobs de análisis y pruebas terminaron correctamente. Ese rojo es el comportamiento pedido: no se desactivó el umbral HIGH/CRITICAL.

## 12. Conclusiones y recomendaciones

El pipeline ya ejecuta SAST, SCA y SBOM por separado, publica los reportes y distingue un fallo técnico de una vulnerabilidad. En el código real hay un hallazgo SAST que la política convierte a HIGH y hay avisos SCA CRITICAL y HIGH, así que el build queda bloqueado.

Recomendaciones, sin aplicarlas en esta entrega para no ocultar los hallazgos del laboratorio:

- Sustituir `exec` con entrada de usuario y dejar de usar MD5 para contraseñas.
- Añadir validación CSRF en las rutas que cambian estado.
- Subir `lodash` y `express` a versiones que cubran los avisos de la tabla y regenerar el lockfile. Las transitivas se corrigen al actualizar express, y hay que confirmarlo con otro análisis.
- Reemplazar el secreto `NVD_API_KEY` por una clave vigente de NVD si se quiere dejar el espejo y consultar la API directamente.
- Mantener la caché semanal de la base para no descargar los feeds en cada push.

Pendiente técnico: la clave configurada en GitHub fue rechazada por la API de NVD. El análisis SCA verificado no depende de esa clave; usa el espejo oficial del proyecto Dependency-Check. No queda un reporte SCA falso ni un paso marcado como exitoso sin artifact.
