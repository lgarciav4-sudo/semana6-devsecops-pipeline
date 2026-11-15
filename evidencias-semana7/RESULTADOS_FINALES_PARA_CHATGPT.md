# RESULTADOS FINALES PARA CHATGPT — SEMANA 7

Usar estos datos para el PowerPoint y el guion de 2.5 minutos. No completar huecos con firmas, hashes o índices que no estén aquí.

- Repositorio: https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline
- Rama: `main`
- Commit firmado: `e550ea45c11851a0f41ce244877df8f842e5e8ac`
- Ejecución: https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline/actions/runs/43676948923
- Inicio: 2026-11-15T04:28:53Z. Fin del job: 2026-11-15T04:29:14Z
- Conclusión: `success`
- Evento: `push`
- Actor: `lgarciav4-sudo`
- Cosign: v3.1.4 (`sigstore/cosign-installer@v4.1.3`)
- Runner: `ubuntu-latest`, `github-hosted`

## Artefacto

- Nombre: `semana7-app.zip`
- Tamaño: 3386 bytes
- SHA-256: `446d7a4ce73a357e7b219c24c08933b746358ed408162a3dcf4b19faf8f4ee58`
- Archivos: `Dockerfile`, `README.md`, `package.json`, `src/db.js`, `src/server.js`
- Construcción: `scripts/build_artifact.py`, 2026-11-15T04:29:01Z
- Manifiesto: `provenance.json`, firmado en `provenance.sigstore.json`

## Firma e identidad

- Modo: keyless. Token OIDC de GitHub Actions. Certificado de Fulcio. Registro Rekor.
- Emisor OIDC: `https://token.actions.githubusercontent.com`
- Emisor del certificado: `O=sigstore.dev, CN=sigstore-intermediate`
- Identidad SAN: `https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline/.github/workflows/semana7-cosign.yml@refs/heads/main`
- Workflow: `Semana 7 - Firma Cosign`
- Archivo: `.github/workflows/semana7-cosign.yml`
- Ref: `refs/heads/main`
- Vigencia del certificado: 2026-11-15 04:29:02 GMT a 04:39:02 GMT
- Verificación del ZIP: `Verified OK`
- Verificación de `provenance.json`: `Verified OK`
- Rekor de la firma del ZIP: índice `3894006896` (https://search.sigstore.dev?logIndex=3894006896)
- Rekor de la firma del manifiesto: índice `3894007161`

## Integridad

La copia del ZIP con el texto `manipulado` agregado fue rechazada con código 1:

`invalid signature when validating ASN.1 encoded signature`

El ZIP original sigue verificando. La copia alterada no se publicó.

## Procedencia SLSA

- Acción: `actions/attest-build-provenance@v2`
- Predicado: `https://slsa.dev/provenance/v1`
- buildType: `https://actions.github.io/buildtypes/workflow/v1`
- Builder: `https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline/.github/workflows/semana7-cosign.yml@refs/heads/main`
- Invocación: `https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline/actions/runs/43676948923/attempts/1`
- Fuente: `git+https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline@refs/heads/main`
- gitCommit: `e550ea45c11851a0f41ce244877df8f842e5e8ac`
- repository_id: `1458301352`
- repository_owner_id: `356792479`
- Atestación: https://github.com/lgarciav4-sudo/semana6-devsecops-pipeline/attestations/67706946
- Rekor de la atestación: https://search.sigstore.dev?logIndex=3894007481
- Comprobación posterior con `gh attestation verify` sobre el ZIP descargado: código 0, con el workflow firmante, `refs/heads/main` y el commit `e550ea45`

## Conclusión para la última diapositiva

Una firma válida permite comprobar la integridad del artefacto y la identidad del firmante. Combinarla con una política que solo acepte este workflow y con la evidencia de procedencia ayuda a reducir el riesgo de distribuir software alterado o construido fuera del proceso permitido.

## Qué no mezclar

La ejecución 43676948893 de `Semana 6 - SAST SCA SBOM Gate` quedó en `failure` por la política HIGH/CRITICAL ya documentada. El job de Cosign de la Semana 7 está en `success`. El ZIP generado en una máquina local tiene otro hash y no es el artefacto firmado.
