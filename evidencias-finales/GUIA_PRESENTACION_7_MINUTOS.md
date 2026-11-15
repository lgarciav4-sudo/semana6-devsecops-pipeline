# Guía de presentación — 7 minutos

Tono: estudiante, en primera persona. Los tiempos suman unos 6 minutos y medio. La ejecución que se muestra es https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline/actions/runs/43670979336

## Diapositiva 1 — Portada y objetivo

**En pantalla:** Semana 6. Pipeline SAST + SCA + SBOM. Objetivo: detectar vulnerabilidades en el código y en las dependencias, inventariar los componentes y bloquear el build desde HIGH.

**Speech (40 s):** Hola. En este laboratorio armé un pipeline de seguridad para una aplicación demo que ya trae fallos a propósito. El objetivo no era dejar el repositorio en verde a cualquier costo. Era analizar el código con Semgrep, las dependencias con Dependency-Check, generar un SBOM con Syft y hacer que el build se detenga si aparece algo HIGH o CRITICAL. Les voy a mostrar lo que realmente salió en GitHub Actions.

## Diapositiva 2 — Repositorio y entorno

**En pantalla:** Repositorio `lgarciav4-sudo/semana6-devsecops-pipeline`, rama `main`, commit `04e4bc33`. Enlace de la ejecución 43670979336. Runner `ubuntu-latest`.

**Speech (40 s):** El trabajo está en mi repositorio de GitHub, en la rama main. La ejecución que uso como evidencia empezó a las 03:08 UTC y terminó a las 03:09 UTC del 15 de noviembre de 2026. El workflow se llama Semana 6 - SAST SCA SBOM Gate. Abajo se ve en rojo, y en un momento les explico por qué ese rojo es el resultado de la política y no un crash de las herramientas.

## Diapositiva 3 — Arquitectura del pipeline

**En pantalla:** Cinco jobs. Pruebas, Semgrep, Syft y Dependency-Check en paralelo. Después, la política, que necesita los JSON de Semgrep y de Dependency-Check. El SBOM no espera al SCA.

**Speech (50 s):** Organicé el pipeline en jobs separados. Semgrep, Syft y Dependency-Check arrancan al mismo tiempo, y las pruebas de la política también. Así, si Dependency-Check falla, el SBOM igual se genera. Al final hay un job que descarga los dos reportes y aplica el umbral. Si el JSON no existe o viene roto, el script sale con código 2 y no dice que el código está limpio. Si hay un hallazgo HIGH o CRITICAL, sale con código 1.

## Diapositiva 4 — SAST con Semgrep

**En pantalla:** 209 reglas, 5 archivos, 3 hallazgos. Tabla: INFO en la línea 18, ERROR en la 40, WARNING en la 48. Conversión: INFO a LOW, WARNING a MEDIUM, ERROR a HIGH.

**Speech (70 s):** Semgrep 1.185.0 corrió el paquete de reglas por defecto. Fueron 209 reglas sobre cinco archivos y encontró tres cosas, todas en `app/src/server.js`. La primera es informativa: no hay un middleware CSRF. La política la trata como LOW y no bloquea. La segunda es un ERROR: hay una llamada a `child_process` con datos que vienen del request, en la ruta de ping. Eso se convierte a HIGH y sí bloquea. La tercera es un WARNING: la contraseña se hashea con MD5. Eso queda como MEDIUM y no alcanza el umbral. El riesgo del segundo hallazgo es inyección de comandos; la corrección es no pasar la entrada del usuario a un shell. El del tercero es usar bcrypt, scrypt o Argon2 en lugar de MD5.

## Diapositiva 5 — SCA con Dependency-Check

**En pantalla:** Dependency-Check 13.0.0. 10 dependencias, 8 con avisos, 22 vulnerabilidades. 1 critical, 9 high, 6 moderate, 6 low. Destacar lodash 4.17.11, CVE-2019-10744, CVSS 9.1, y express 4.17.1.

**Speech (80 s):** Dependency-Check analizó el `package.json` y el lockfile. Identificó 10 dependencias y 22 avisos en ocho de ellas. Todas vienen del analizador NPM del propio Dependency-Check; el JSON marca el origen como NPM. La más grave es lodash 4.17.11, el aviso GHSA-jf85-cpcp-j695, que corresponde a CVE-2019-10744, con CVSS 9.1. El texto del aviso dice que afecta a versiones anteriores a 4.17.12. Express 4.17.1 trae dos avisos, y por el árbol aparecen body-parser, qs, path-to-regexp, cookie, send y serve-static. En la tabla del informe dejé el CVE solo cuando el reporte lo trae. Hay un aviso de cookie, GHSA-pxg6-pf52-xh8x, que no incluye CVE. La primera ejecución con Docker falló a los cuarenta minutos por el bloqueo de la base H2. Después, la API de NVD rechazó el secreto configurado. La ejecución válida descargó la caché oficial del proyecto Dependency-Check, sin reenviar esa clave. La actualización tardó 57 segundos y el análisis, 2 segundos.

## Diapositiva 6 — SBOM CycloneDX

**En pantalla:** `sbom.cyclonedx.json`. bomFormat CycloneDX, specVersion 1.6, 53 componentes. Syft 1.42.3.

**Speech (40 s):** Syft generó el inventario en CycloneDX 1.6. El archivo es JSON válido y tiene 53 componentes. Ahí están express 4.17.1 y lodash 4.17.11, además de las transitivas que después marcó Dependency-Check. El primer intento solo describía la carpeta app, porque no existía el lockfile. Por eso el job ahora instala las dependencias antes de inventariar. Ese SBOM corto no lo presento como resultado final.

## Diapositiva 7 — Política y ejecución

**En pantalla:** Umbral HIGH. Captura o texto: `Hallazgos: 25; bloqueantes: 11` y `BUILD BLOQUEADO`. Código 1. Al lado, 13 pruebas OK. Jobs en verde: pruebas, SAST, SBOM y SCA. Job de política en rojo.

**Speech (70 s):** La política bloquea desde HIGH. Sobre los reportes reales contó 25 hallazgos y 11 bloqueantes: el ERROR de Semgrep, el CRITICAL de lodash y nueve HIGH de dependencias. El mensaje fue BUILD BLOQUEADO y el código de salida fue 1. Por eso el workflow queda en rojo. Los otros cuatro jobs sí terminaron bien. También corrí los ejemplos: con un hallazgo bajo, el build se aprueba; con un HIGH simulado, se bloquea. Las pruebas unitarias, trece en total, pasaron en local y otra vez dentro de Actions. Una de ellas comprueba que un archivo ausente da error técnico, código 2, y no un aprobado.

## Diapositiva 8 — Resultados, remediaciones y cierre

**En pantalla:** Tres acciones: quitar el `exec` con entrada de usuario, sustituir MD5, subir lodash y express y repetir el SCA. Pendiente: reemplazar `NVD_API_KEY` si se quiere usar la API directa.

**Speech (50 s):** Para cerrar: el laboratorio sí ejecutó los tres análisis y la puerta de severidad. El build queda bloqueado por hallazgos reales, no porque se haya inventado un reporte. Lo que yo corregiría después, sin borrar esta evidencia, es dejar de concatenar el host en `exec`, hashear contraseñas con una función adecuada y subir lodash y express a versiones que cubran los avisos, volviendo a correr Dependency-Check para comprobarlo. El secreto de NVD que está en GitHub fue rechazado por la API; el análisis que presento usó el espejo oficial. Si quiero la API directa, tengo que sustituir esa clave en los secretos del repositorio, sin pegarla en la presentación. Gracias.

## Notas para no salirme del tiempo

- No abrir el HTML completo de Dependency-Check. Mostrar el resumen del job y una fila de la tabla.
- No decir que el workflow está en verde.
- No atribuir los 22 avisos al motor NVD: el campo `source` del JSON es NPM. La caché NVD sí se descargó y quedó registrada en `scanInfo`.
- Si preguntan por la clave, responder que está en GitHub, que NVD la rechazó y que no se va a mostrar.
