# Evidencia S14 — Nueva medición local de E1 y E6 tras los cambios de búsqueda

**Fecha:** 13 de noviembre de 2026. **Código medido:** `2d86f2d` con los cambios sin commit de la rama `claude/revision-archivo-proyecto-53f631` (el registro de entorno lo marca como `2d86f2d-dirty`).

## 1. Por qué se volvió a medir

Desde las mediciones anteriores ([E1 local](s14-medicion-e1.md) y [E6](e6-degradacion-bajo-carga.md)), la búsqueda cambió:

- consulta la tienda de Xbox como fuente adicional, con dos buscadores y un catálogo de precios;
- usa la copia de respaldo de las fuentes (ADR-0015) y puede usar IsThereAnyDeal (ADR-0016);
- agrega el filtro por plataforma, los descuentos y los juegos que solo existen en una consola;
- desde esta revisión, descarta los productos de PlayStation que solo corren en PS3 o PS Vita.

Una fuente más dentro del mismo plazo podía subir el p95. Esta medición comprueba si los dos escenarios siguen dentro de su umbral.

## 2. Cambios en el montaje

El simulador de fuentes (`scripts/stub_upstream.py`) no tenía la tienda de Xbox: cada búsqueda la habría contado como caída. Se añadieron sus tres servicios, sin degradación:

| Servicio simulado | Latencia fija |
|---|---|
| Buscador de sugerencias de Xbox | 0,20 s |
| Búsqueda completa de Xbox | 0,20 s |
| Catálogo de precios de Xbox | 0,25 s |

`scripts/e6_backend.py` redirige esas tres direcciones al simulador. Las demás latencias, la degradación de E6 (CheapShark tarda 6 s en 18 de 50 consultas), los scripts de k6 y los umbrales **no cambiaron**. Antes de medir se comprobó una búsqueda: trae precios de Steam, CheapShark, PlayStation y Xbox, y `unavailable_sources` vacío.

Sin la llave de IsThereAnyDeal, las tiendas de PC salen de CheapShark, como en las mediciones anteriores. La copia de respaldo vive en memoria.

## 3. Cómo se midió

```bash
for i in 1 2 3 4 5; do python scripts/s14_corrida.py tras-cambios-$i; done
for i in 1 2 3; do python scripts/e6_corrida.py backend tras-cambios-$i; done
```

Cada corrida arranca procesos nuevos (caché fría), un worker de uvicorn y el límite de tasa desactivado. Entorno: Windows 11, 16 CPU, Python 3.12.1, en `127.0.0.1`. **Es local, no el sistema desplegado.**

## 4. Resultados

### E1 — búsqueda en operación normal (umbral: p95 ≤ 3000 ms, fallidas < 1 %)

50 usuarios virtuales, 4 búsquedas cada uno.

| Corrida | Solicitudes | Fallidas | p50 | p90 | p95 | Máximo | Cumple |
|---|---|---|---|---|---|---|---|
| tras-cambios-1 | 200 | 0 | 547 ms | 921 ms | 938 ms | 1021 ms | Sí |
| tras-cambios-2 | 200 | 0 | 532 ms | 889 ms | 962 ms | 1047 ms | Sí |
| tras-cambios-3 | 200 | 0 | 543 ms | 886 ms | 955 ms | 1079 ms | Sí |
| tras-cambios-4 | 200 | 0 | 541 ms | 899 ms | 969 ms | 1076 ms | Sí |
| tras-cambios-5 | 200 | 0 | 531 ms | 879 ms | 926 ms | 1072 ms | Sí |

**Mediana del p95: 955 ms**, con 2,0 s de margen. Datos en `s14-resultados/tras-cambios-*.json`.

### E6 — degradación bajo carga (umbral: p95 ≤ 5 s, fallidas < 1 %, degradadas sin aviso = 0)

| Corrida | Solicitudes | Fallidas | p50 | p95 | Máximo | Degradadas | Sin aviso | Cumple |
|---|---|---|---|---|---|---|---|---|
| tras-cambios-1 | 50 | 0 | 824 ms | 3407 ms | 3604 ms | 18 | 0 | Sí |
| tras-cambios-2 | 50 | 0 | 602 ms | 3538 ms | 3567 ms | 18 | 0 | Sí |
| tras-cambios-3 | 50 | 0 | 836 ms | 3405 ms | 3619 ms | 18 | 0 | Sí |

**Mediana del p95: 3,41 s.** Las 18 consultas lentas siguen avisando la fuente faltante. Datos en `e6-resultados/tras-cambios-*.json`.

## 5. Conclusión

**Los dos escenarios siguen cumpliendo en local tras añadir Xbox y los demás cambios.** E1 queda por debajo de 1 s; E6 sigue cerca de 3,4 s porque las búsquedas afectadas esperan el plazo de 3 s de la fuente lenta.

**Lo que esta medición no permite afirmar:**

- **No es comparable con las cifras anteriores.** La medición previa de E1 (p95 de 632 ms) corrió en Linux con 2 CPU; esta, en Windows con 16 CPU. La diferencia de 632 a 955 ms mezcla el cambio de código con el cambio de equipo. Lo mismo vale para E6 (3,61 s antes).
- **No dice nada del despliegue.** Allí E1 no se cumple (p95 de 9,05 s, [medición del despliegue](s14-e1-medicion.md)), y esta medición no cambia esa conclusión.
- **Xbox y PlayStation responden siempre rápido en el simulador.** No se midió una tienda de Xbox lenta; su plazo es el mismo de 3 s que el de las otras fuentes secundarias.
- Son pocas muestras por corrida (200 en E1, 50 en E6).
