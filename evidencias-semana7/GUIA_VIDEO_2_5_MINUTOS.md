# Guion del videoresumen — 2.5 minutos

Tono: estudiante, en primera persona. Cinco diapositivas. La ejecución que se muestra es https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline/actions/runs/43676948923

## Diapositiva 1 — Qué es y para qué (0:00–0:25)

**En pantalla:** Semana 7. Sigstore y Cosign. Firma keyless de `semana7-app.zip`. Identidad de GitHub Actions, certificado de 10 minutos.

**Speech:** Hola. En la semana 7 firmé el ZIP de la aplicación con Sigstore, usando Cosign. Quiero mostrar que el archivo sigue intacto y que quien lo firmó fue el workflow de GitHub Actions. El certificado dura diez minutos y no guardé una clave privada en el repositorio. Después enseño el rechazo de una copia modificada y la procedencia de la construcción.

## Diapositiva 2 — Generación del artefacto (0:25–0:55)

**En pantalla:** Ejecución 43676948923, commit `e550ea45`, ZIP de 3386 bytes. SHA-256 `446d7a4ce73a357e7b219c24c08933b746358ed408162a3dcf4b19faf8f4ee58`. Cinco archivos: Dockerfile, README, package.json, src/db.js, src/server.js.

**Speech:** El workflow construye `semana7-app.zip` desde la carpeta app. En esta ejecución pesa 3386 bytes y su SHA-256 empieza por 446d7a4c. Lleva el Dockerfile, el README, el package.json y los dos archivos de src. El mismo script escribe `provenance.json` con el repositorio, el commit e550ea45, la rama main, el workflow y la hora 04:29 UTC del 15 de noviembre de 2026.

## Diapositiva 3 — Firma e identidad (0:55–1:25)

**En pantalla:** Cosign v3.1.4. `Verified OK`. Identidad `semana7-cosign.yml@refs/heads/main`. Emisor `token.actions.githubusercontent.com`. Rekor `3894006896`. Vigencia 04:29:02 a 04:39:02 GMT.

**Speech:** Cosign 3.1.4 firma el ZIP con la identidad OIDC de GitHub. Fulcio pone en el certificado la URI del workflow semana7-cosign.yml en la rama main. La verificación pide esa identidad, el emisor de GitHub, el repositorio, el nombre del workflow y el commit. El resultado fue Verified OK. La firma quedó en Rekor, índice 3894006896, y el certificado solo vale de las 04:29 a las 04:39 UTC.

## Diapositiva 4 — Archivo manipulado (1:25–1:55)

**En pantalla:** Copia con la palabra `manipulado`. Código 1. Texto: `invalid signature when validating ASN.1 encoded signature`. El ZIP original sigue en `Verified OK`.

**Speech:** Luego el workflow copió el ZIP y le agregó la palabra manipulado. Al verificar esa copia con la misma firma, Cosign respondió invalid signature y salió con código 1. El ZIP original sigue verificando. La firma cubre exactamente esos bytes: si el archivo cambia, la comprobación se rechaza.

## Diapositiva 5 — Procedencia y cierre (1:55–2:25)

**En pantalla:** Repo, commit, workflow, run 43676948923, runner github-hosted. Atestación https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline/attestations/67706946. Rekor https://search.sigstore.dev?logIndex=3894007481

**Speech:** La procedencia dice dónde y cómo se construyó: este repositorio, el commit e550ea45, un push, un runner de GitHub y la ejecución 43676948923. GitHub publicó además una atestación SLSA, visible en la página 67706946 y en Rekor, índice 3894007481. La verificación aceptó ese workflow, la rama main y ese commit. Con la firma, una política de emisores autorizados y esta evidencia de procedencia se puede detectar software alterado o construido fuera del proceso permitido. Gracias.

## Qué mostrar si hay tiempo de sobra

- El job en verde, de 04:28:56 a 04:29:14 UTC.
- Las dos líneas `Verified OK` y el archivo `verificacion-manipulado.txt`.
- La URI de identidad dentro de `identidad-firma.txt`.

## Qué dejar fuera

- El workflow rojo de la Semana 6. Sigue bloqueando por hallazgos HIGH y CRITICAL; no forma parte de este ejercicio.
- El certificado completo en PEM. Basta la identidad, la vigencia y el índice de Rekor.
- El ZIP local generado en Windows. Tiene otro SHA-256 y el evento `local`; la evidencia es el ZIP firmado en Actions.
