# S13 — Análisis de dependencias: ejecución, hallazgos y decisiones

- **Commit de referencia:** `7d045f9` (merge del PR #36, 1 de noviembre de 2026)
- **Responsable de la revisión:** JerryDBM
- **Relación:** amenazas A1 y A11 del [modelo de amenazas](../seguridad/modelo-amenazas.md)

## 1. Herramientas y dónde se ejecutan


| Herramienta        | Qué analiza                                                                      | Dónde corre                                                                                                                                  | Criterio de fallo                                               |
|--------------------|-----------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| `pip-audit` 2.10.1 | `backend/requirements.lock`, el mismo lock con hashes que instala el `Dockerfile` | Job `dependency-audit` de [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml), paso «Auditar dependencias del backend (pip-audit)» | Cualquier vulnerabilidad conocida (`--strict --require-hashes`) |
| `npm audit`        | Dependencias de producción del frontend (`frontend/package-lock.json`)           | Mismo job, paso «Auditar dependencias del frontend (npm audit)»                                                                             | Severidad alta o crítica (`--omit=dev --audit-level=high`)     |
| Dependabot         | `pip` (`/backend`), `npm` (`/frontend`) y `github-actions`                        | [`.github/dependabot.yml`](../../.github/dependabot.yml), revisión semanal                                                                   | Abre un PR por cada actualización                              |


El job corre en cada push a `master` y en cada pull request hacia `master`, así que una dependencia vulnerable bloquea la integración.

>
> El análisis de dependencias es distinto del análisis estático del código, que ya hace SonarQube Cloud desde el segundo corte.
>

**Ejecución verificada:** [run #280 — job «Análisis de dependencias»](https://github.com/ISCOUTB/AS_202620_Drift/actions/runs/41276233533/job/124758845436?pr=36),
*succeeded* en el PR #36 (commit `01263f8`).

## 2. Hallazgos y decisión sobre cada uno

El análisis se ejecutó primero de forma local sobre `d9a1816` (estado de `master` antes de S13). La salida completa está en [`s13-resultados/`](s13-resultados/).


| #  | Paquete                                     | Versión afectada | Aviso                                                                  | Severidad             | ¿Afecta a DRIFT?                                                                                                                                                                                                           | Decisión                                                                                                                        | Evidencia |
|----|---------------------------------------------|-------------------|------------------------------------------------------------------------|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------|-----------|
| H1 | `next` (frontend)                           | 16.3.2            | 13 avisos: 5 críticos, 2 altos, 5 moderados y 1 bajo (detalle en §3) | Crítica              | Sí. El endpoint `/_next/image` existe por defecto en el servidor autocontenido aunque DRIFT no use `next/image`, y el frontend está expuesto a Internet en Vercel y en Dokploy.                                           | **Corregido:** actualizado a 16.4.3. Además, `next`, `react` y `react-dom` dejan de usar `latest` y quedan con versión exacta. | PR #33    |
| H2 | `sharp` (indirecta, vía `next`)            | < 0.35.5       | GHSA-rgj7-g3m4-5g8c, GHSA-wq5f-xc86-pv6w (libheif, librsvg)            | Alta                  | Sí, a través de la optimización de imágenes de Next.                                                                                                                                                                    | **Corregido:** sube a 0.35.5 con `next` 16.4.3.                                                                                  | PR #33    |
| H3 | `source-map-js` (indirecta, vía `postcss`) | 1.2.1             | GHSA-68fv-2mgg-jv7q (DoS del bucle de eventos)                         | Alta                  | Bajo: solo procesa mapas de código en la compilación.                                                                                                                                                                     | **Corregido:** sube a 1.2.2 con `npm audit fix`, sin `--force`.                                                                  | PR #33    |
| H4 | `certifi` (backend)                         | 2026.7.22         | PYSEC-2026-4320 / GHSA-6q48-6c7w-9gw2                                  | — (sin puntuación) | Sí. El almacén de certificados incluía la raíz `emSign ECC Root CA - G3`, con intermedias comprometidas: alguien con uno de esos certificados podría suplantar por TLS a Steam, CheapShark, PlayStation o open.er-api. | **Corregido:** actualizado a 2026.10.18 en `requirements.txt` y `requirements.lock` (con hashes nuevos).                         | PR #34    |
| H5 | `certifi` (despliegue serverless de Vercel) | 2026.7.22         | PYSEC-2026-4320                                                        | —                   | Sí, por el mismo motivo, en `deployment/vercel/uv.lock` (ADR-0006).                                                                                                                                                        | **Corregido:** actualizado a 2026.10.23 con `uv lock --upgrade-package certifi`.                                                 | PR #35    |


**Resultado después de las correcciones:** `npm audit` → `found 0 vulnerabilities`; `pip-audit` → `No known vulnerabilities found`. Están en `s13-resultados/npm-audit-despues.json` y `s13-resultados/pip-audit-despues.json`. Las 190 pruebas del backend y la compilación del frontend pasan.

**Hallazgos aceptados:** ninguno. Todos tenían corrección disponible y compatible.

## 3. Detalle de los avisos de `next` 16.3.2 (H1)


| Severidad | Aviso                                    | Resumen                                             | ¿DRIFT usa la función?                                |
|-----------|------------------------------------------|-----------------------------------------------------|---------------------------------------------------------|
| Crítica  | GHSA-p293-qw3h-jr36                      | RCE en servidores alojados en Windows               | No: los contenedores corren en Linux (`node:22-alpine`) |
| Crítica  | GHSA-2xp9-vwfh-vxw4                      | RCE en Image Optimization con AVIF                  | El endpoint existe por defecto                          |
| Crítica  | GHSA-2464-fhr4-w9xw                      | RCE en Image Optimization con SVG                   | El endpoint existe por defecto                          |
| Crítica  | GHSA-vcvr-r3jv-pc5j                      | RCE en `next/og`                                    | No                                                      |
| Crítica  | GHSA-673q-mjm6-r5xr                      | RCE en funciones `use cache`                        | No                                                      |
| Alta      | GHSA-cjq9-62q9-8jv4                      | SSRF en Image Optimization                          | El endpoint existe por defecto                          |
| Alta      | GHSA-p3m5-59mp-jv5r                      | DoS en App Router con Server Actions                | No usa Server Actions                                   |
| Moderada  | GHSA-4jqv-mc3x-m676, GHSA-mcj8-r9mp-w47p | Envenenamiento de caché SSG/ISR en autoalojamiento | La portada es estática y se sirve en Dokploy           |
| Moderada  | GHSA-3w37-wq28-93x7, GHSA-h694-7cp9-m8p3 | Fugas con `use cache`                               | No                                                      |
| Moderada  | GHSA-f87g-xv8r-7p7x                      | Fuga de información en rutas de metadatos          | No                                                      |
| Baja      | GHSA-39w2-rjm5-chcv                      | Fuga en el servidor de desarrollo                   | Solo en local                                           |


Aunque varias funciones no se usan, se actualizó igual: Image Optimization queda activo por defecto y la corrección no cambia el comportamiento de la aplicación.

## 4. Política para los hallazgos futuros

- **Altos y críticos:** el pipeline falla. Se corrigen antes de integrar, o se aceptan con motivo en [arc42 §11](../arc42/arc42-11-riesgos-y-deuda-tecnica.md) y se excluyen de forma explícita en el job.
- **Moderados y bajos:** no bloquean. Llegan como PR de Dependabot y se revisan cada semana.
- **PR de Dependabot:** no se integran sin que el CI pase. Cada uno se trata como un hallazgo: se actualiza o se deja una razón en el PR.

 
