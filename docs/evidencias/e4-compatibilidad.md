# Evidencia E4 — Compatibilidad de PC

**Fecha de validación:** 2026-09-13
**Entorno:** ejecución local de DRIFT.

## Implementación

La compatibilidad se calcula mediante un caso de uso independiente (`EstimateCompatibility`) y un catálogo local controlado de requisitos.

Para esta etapa, la escala de GPU es:

* 1 = básica
* 2 = media
* 3 = alta

El catálogo incluye requisitos controlados para Portal 2 (ID 620).

## Prueba automatizada

Se ejecutó:

```powershell
python -m pytest tests -q