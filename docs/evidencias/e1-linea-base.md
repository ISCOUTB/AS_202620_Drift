# Evidencia E1 — Rendimiento de búsqueda

**Fecha:** 2026-09-13
**Herramienta:** k6 v2.2.0
**Endpoint evaluado:** `GET /games/search?q=Minecraft`

## Configuración de la prueba

- 50 usuarios virtuales concurrentes.
- Una solicitud por cada usuario virtual.
- Total: 50 solicitudes.
- Umbral de aceptación: p95 menor a 3 segundos.
- Script utilizado: `scripts/k6_baseline.js`.

## Medición inicial

| Métrica | Resultado |
|---|---:|
| Solicitudes exitosas | 50 de 50 |
| Solicitudes fallidas | 0 % |
| Tiempo mínimo | 13.33 s |
| Tiempo promedio | 14.19 s |
| p95 | 14.63 s |
| Tiempo máximo | 14.92 s |

La medición inicial no cumplía el escenario E1, aunque todas las solicitudes respondieron correctamente.

## Optimización aplicada

Se optimizó `SteamGameRepository` mediante:

- Caché de resultados de búsqueda durante 60 segundos.
- Límite de cinco resultados por consulta.
- Consulta paralela de los detalles de los videojuegos en Steam.

## Medición posterior a la optimización

| Métrica | Resultado |
|---|---:|
| Solicitudes exitosas | 50 de 50 |
| Solicitudes fallidas | 0 % |
| Tiempo mínimo | 1.22 s |
| Tiempo promedio | 1.23 s |
| p95 | 1.24 s |
| Tiempo máximo | 1.24 s |

## Conclusión

El escenario E1 cumple el objetivo de rendimiento: la búsqueda respondió con un p95 de 1.24 segundos bajo 50 usuarios concurrentes, menor al límite de 3 segundos.