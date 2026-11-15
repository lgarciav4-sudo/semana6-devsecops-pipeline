# Informe Semana 7 — Firma digital y procedencia con Sigstore (Cosign)

## Objetivo

Firmar un artefacto de software, comprobar después su integridad y la identidad de quien lo firmó, y revisar dónde y cómo fue construido. El ejercicio usa el repositorio de la Semana 6 y GitHub Actions. No se creó una imagen Docker ni se guardó una clave privada en el repositorio.

## Ejecución usada como evidencia

| Dato | Valor |
| --- | --- |
| Repositorio | https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline |
| Rama | `main` |
| Commit | `e550ea45c11851a0f41ce244877df8f842e5e8ac` |
| Workflow | Semana 7 - Firma Cosign |
| Ejecución | https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline/actions/runs/43676948923 |
| Evento | `push` |
| Inicio | 2026-11-15T04:28:53Z |
| Fin del job | 2026-11-15T04:29:14Z |
| Conclusión | `success` |
| Cosign | v3.1.4, instalado con `sigstore/cosign-installer@v4.1.3` |
| Runner | `ubuntu-latest`, entorno `github-hosted` |

El job `Firmar, verificar y comprobar integridad` terminó en verde. Firmó el ZIP, verificó la firma, rechazó una copia modificada, publicó la atestación de GitHub y subió las evidencias.

## 1. Construcción del artefacto

`scripts/build_artifact.py` empaqueta la carpeta `app/` en `dist/semana7-app.zip` y escribe `dist/provenance.json`. El ZIP de esta ejecución pesa 3386 bytes y contiene cinco archivos: `Dockerfile`, `README.md`, `package.json`, `src/db.js` y `src/server.js`.

SHA-256 del ZIP firmado:

`446d7a4ce73a357e7b219c24c08933b746358ed408162a3dcf4b19faf8f4ee58`

El manifiesto de procedencia declara repositorio, commit, rama, workflow, número de ejecución, actor `lgarciav4-sudo`, evento `push`, sistema Linux x64 y la hora `2026-11-15T04:29:01Z`. También deja escrita la identidad OIDC que después debe aparecer en el certificado.

## 2. Firma digital

Cosign firmó dos blobs con `cosign sign-blob --yes --bundle`:

- `semana7-app.zip` → `artefacto.sigstore.json`
- `provenance.json` → `provenance.sigstore.json`

El modo es keyless. GitHub Actions entrega un token OIDC del emisor `https://token.actions.githubusercontent.com`. Fulcio emite un certificado de corta duración y la firma queda en el registro público Rekor. No hay una clave privada permanente en el repositorio.

El certificado del ZIP, resumido en `identidad-firma.txt`, dice:

| Campo | Valor |
| --- | --- |
| Emisor del certificado | `O=sigstore.dev, CN=sigstore-intermediate` |
| Uso | firma digital y code signing |
| Vigencia | 2026-11-15 04:29:02 GMT a 04:39:02 GMT (10 minutos) |
| Identidad (SAN URI) | `https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline/.github/workflows/semana7-cosign.yml@refs/heads/main` |
| Emisor OIDC | `https://token.actions.githubusercontent.com` |
| Evento | `push` |
| Commit | `e550ea45c11851a0f41ce244877df8f842e5e8ac` |
| Nombre del workflow | `Semana 7 - Firma Cosign` |
| Repositorio | `lgarciav4-sudo/semana6-devsecops-pipeline` |
| Ref | `refs/heads/main` |
| Runner | `github-hosted` |
| Entrada Rekor de la firma del ZIP | índice `3894006896` |
| Entrada Rekor de la firma de `provenance.json` | índice `3894007161` |

La identidad del firmante es el workflow concreto en la rama `main`, no el nombre de una persona ni una clave suelta.

## 3. Verificación de autenticidad e integridad

`cosign verify-blob` comprobó el ZIP exigiendo, al mismo tiempo:

- el bundle de la firma;
- la identidad exacta del workflow;
- el emisor OIDC de GitHub Actions;
- el repositorio, el nombre del workflow, la rama y el commit.

La salida guardada en `verificacion-original.txt` es `Verified OK`. La firma de `provenance.json` también devolvió `Verified OK`.

Eso significa que los bytes del ZIP coinciden con los que se firmaron y que el certificado pertenece a ese workflow, en ese commit.

## 4. Rechazo del archivo manipulado

El workflow copió el ZIP, le añadió el texto `manipulado` y volvió a verificar la copia con el mismo bundle. Cosign respondió:

`invalid signature when validating ASN.1 encoded signature`

El código de salida fue 1. `verificacion-manipulado.txt` deja constancia. La copia alterada se borró antes de publicar el artefacto, así que el ZIP descargado sigue siendo el original. La firma permanece atada al digest `446d7a4c…` y no cubre los bytes nuevos.

## 5. Procedencia

Hay dos capas.

La primera es `provenance.json`, generada por el script de construcción y firmada con el mismo certificado. Ahí se lee el repositorio, el commit, el workflow `.github/workflows/semana7-cosign.yml`, la ejecución `43676948923`, el evento `push` y el entorno Linux. Si alguien cambia ese JSON después, la verificación de `provenance.sigstore.json` falla igual que falló el ZIP manipulado.

La segunda es la atestación SLSA que publicó GitHub con `actions/attest-build-provenance@v2`. El predicado es `https://slsa.dev/provenance/v1` y el tipo de build es `https://actions.github.io/buildtypes/workflow/v1`. GitHub registró:

- sujeto `semana7-app.zip` con el mismo SHA-256;
- builder `https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline/.github/workflows/semana7-cosign.yml@refs/heads/main`;
- invocación `https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline/actions/runs/43676948923/attempts/1`;
- código fuente `git+https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline@refs/heads/main`, commit `e550ea45c11851a0f41ce244877df8f842e5e8ac`;
- página de la atestación: https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline/attestations/67706946
- Rekor: https://search.sigstore.dev?logIndex=3894007481

La comprobación posterior, con `gh attestation verify` sobre el ZIP descargado, aceptó ese workflow firmante, la rama `main` y ese commit. El detalle está en `atestacion-github.txt`.

## Cómo reduce el riesgo de software manipulado

Una firma válida responde dos preguntas a la vez: si el archivo es exactamente el que se firmó y quién lo firmó. En este laboratorio el firmante permitido es el workflow de GitHub Actions en `main`. Un ZIP modificado deja de verificar. Una firma hecha con otra identidad, aunque cubra los mismos bytes, tampoco cumple la política, porque la verificación exige la URI de este workflow y el emisor OIDC de GitHub. El certificado dura diez minutos y no queda una clave privada reutilizable en el repositorio. Rekor deja una copia pública de la firma, así que no se puede borrar en silencio. La procedencia agrega el lugar y el modo de construcción: repositorio, commit, workflow, ejecución y runner de GitHub. Juntas, la firma, la lista de emisores autorizados y la procedencia permiten rechazar software alterado o construido fuera de este proceso.

## Archivos de evidencia

| Archivo | Qué demuestra |
| --- | --- |
| `semana7-app.zip` | Artefacto original firmado |
| `artefacto.sigstore.json` | Bundle de la firma del ZIP |
| `provenance.json` | Datos declarados de la construcción |
| `provenance.sigstore.json` | Firma de ese manifiesto |
| `verificacion-original.txt` | `Verified OK` del ZIP |
| `verificacion-procedencia.txt` | `Verified OK` del manifiesto |
| `verificacion-manipulado.txt` | Rechazo de la copia alterada, código 1 |
| `identidad-firma.txt` | Certificado, identidad OIDC y entrada Rekor |
| `atestacion-github.txt` | Procedencia SLSA verificada |

## Nota sobre el workflow de la Semana 6

El mismo push también disparó `Semana 6 - SAST SCA SBOM Gate` (ejecución 43676948893). Ese workflow queda en rojo porque la política HIGH/CRITICAL sigue bloqueando los hallazgos ya documentados en la Semana 6. Ese rojo no pertenece a Cosign. El job de la Semana 7 terminó en verde.
