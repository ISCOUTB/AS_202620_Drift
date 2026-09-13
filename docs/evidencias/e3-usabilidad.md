# Evidencia E3 — Identificación de la mejor opción

**Fecha de validación:** 2026-09-12
**Entorno:** ejecución local de DRIFT en `http://localhost:3000`.

## Procedimiento

1. Se inició el backend FastAPI y el frontend Next.js mediante `python scripts/start.py`.
2. Se abrió DRIFT en el navegador.
3. Se buscó el videojuego `Portal 2`.
4. Se verificó que cada resultado mostrara la plataforma y el precio disponible.
5. Se verificó que la tarjeta mostrara el mensaje `Mejor opción disponible: <plataforma>`.

## Resultado

La recomendación se muestra inmediatamente después de realizar la búsqueda, sin requerir pasos adicionales para identificar la mejor opción disponible.

## Alcance

La recomendación se calcula con los precios disponibles en la respuesta. La comparación entre múltiples tiendas reales queda sujeta a la incorporación futura de adaptadores adicionales.