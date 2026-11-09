# Evidencia S14 — Medición del escenario E1 en el despliegue

> Esta es la evidencia vigente de E1. La [medición local con fuentes simuladas](s14-medicion-e1.md) la complementa.

**Fecha:** 2026-11-08, de 19:28 a 19:54, hora de Colombia
**Herramienta:** k6 v2.2.0
**Endpoint evaluado:** `GET https://drift.iscoutb.dev/api/games/search?q=<consulta>`
**Commit de `master` al medir:** `be72a2f`

## Conclusión

**E1 no cumple su umbral en el caso general.** Con 50 usuarios buscando juegos distintos, el p95 fue de **9,05 s frente a un máximo de 3 s** y falló en las 3 corridas.

Solo cumple bajo una condición: cuando los 50 usuarios buscan lo mismo y comparten una sola consulta a las fuentes. Aun así, fue inestable: cumplió en 2 de 3 corridas.

## Escenario y umbral

| Elemento | Valor |
|---|---|
| Escenario | E1, Rendimiento ([arc42 §10.2](../arc42/arc42_10_Requisitos_Calidad.md)) |
| Entorno declarado | Hasta 50 usuarios concurrentes, operación normal |
| Umbral | **≤ 3 s en el percentil 95** |
| ¿Cambió el umbral? | No. Se juzga contra el valor ya declarado |

## Entorno de la medición

| Elemento | Valor |
|---|---|
| Sistema medido | **Desplegado**, servidor del laboratorio (Dokploy) |
| Límites declarados | 0,5 CPU y 192 MB por contenedor, en [`deploy/compose.lab.yaml`](../../deploy/compose.lab.yaml) |
| Generador de carga | Un PC con Windows, por internet desde una conexión doméstica en Colombia, con k6 en esa misma máquina |
| Fuentes externas | **Reales**: Steam, CheapShark y PlayStation. Sus tiempos no se controlan |
| Red | Mediana de `/health` antes de cada corrida: 0,10 s, salvo `misma-3` (0,71 s) |
| Límite de tasa | Activo. Cada corrida (50 búsquedas) cabe en el valor por defecto de 60 por minuto, y no hubo ningún 429 |
| Plazo total de Steam | 5 s por defecto en el código de ese momento. No se pudo comprobar si el despliegue lo cambia por variable de entorno. Después de medir, el código pasó a 4 s ([ADR-0013](../adr/0013-plazo-total-en-la-busqueda-de-steam.md)), y ese valor falta medirlo aquí |

**Versión desplegada:** la API no expone su commit, así que no se pudo confirmar que fuera exactamente `be72a2f`. `/api/metrics` respondió 401 sin token, lo que indica que ya tenía la autenticación de ADR-0011.

## Procedimiento

Desde la raíz del repositorio, con k6 y Python instalados:

```bash
python scripts/s14_e1_corridas.py
```

El comando sobrescribe los archivos de [`s14-resultados/`](s14-resultados/) y tarda unos 26 minutos. Usa [`scripts/k6_s14_e1_busqueda.js`](../../scripts/k6_s14_e1_busqueda.js).

| Parámetro | Valor |
|---|---|
| Carga | 50 usuarios virtuales, 1 búsqueda cada uno, todos a la vez (50 solicitudes por corrida) |
| Modo `distintas` | Un título real distinto por usuario. Es el peor caso: no comparten caché |
| Modo `misma` | Los 50 buscan `Minecraft`, como la [línea base de E1](e1-linea-base.md) |
| Repeticiones | 3 por modo, intercaladas (6 corridas, 300 solicitudes) |
| Espera entre corridas | 5 minutos, para que venzan la caché de búsqueda (60 s) y la ventana del límite de tasa (60 s), y para no acumular llamadas a Steam |
| Métrica | `busqueda_ms`: duración de las búsquedas, sin contar `/health`. Percentiles calculados por k6 |

## Resultados

Tiempos en segundos. Los archivos originales están en [`s14-resultados/`](s14-resultados/).

| Corrida | Respuestas 200 | p50 | p90 | **p95** | Máximo | Sin CheapShark | Sin Steam | Vacías | Cumple ≤ 3 s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `distintas-1` | 50 de 50 | 6,53 | 8,89 | **9,10** | 9,18 | 14 | 1 | 6 | No |
| `distintas-2` | 50 de 50 | 7,22 | 8,96 | **9,05** | 9,29 | 15 | 1 | 1 | No |
| `distintas-3` | 50 de 50 | 6,44 | 8,63 | **8,93** | 9,10 | 15 | 1 | 5 | No |
| `misma-1` | 50 de 50 | 2,32 | 2,38 | **2,40** | 2,44 | 0 | 0 | 0 | Sí |
| `misma-2` | 50 de 50 | 1,96 | 2,03 | **2,06** | 2,08 | 0 | 0 | 0 | Sí |
| `misma-3` | 49 de 50 | 0,71 | 2,57 | **5,86** | 9,97 | 0 | 0 | 0 | No |

| Modo (3 corridas) | p95 mediano | Peor p95 | Frente al umbral de 3 s |
|---|---:|---:|---|
| `distintas` | **9,05 s** | 9,10 s | **No cumple:** tres veces el máximo permitido, en 3 de 3 corridas |
| `misma` | **2,40 s** | 5,86 s | **Cumple con condiciones:** en 2 de 3 corridas |

No hubo respuestas 429 ni PlayStation faltó en ninguna corrida.

## Interpretación

**Lo que muestran los datos:**

- **La red no explica la demora.** `/health` tardó 0,10 s y las búsquedas tardaron de 6 a 9 s. Tres búsquedas sueltas hechas el mismo día, sin carga, tardaron de 0,55 a 1,76 s.
- **La demora no aparece en la lógica de la búsqueda por sí sola.** En la [medición local](s14-medicion-e1.md), con fuentes simuladas, sin TLS por cliente y sin el límite de 0,5 CPU, el p95 fue de 0,63 s. La diferencia está en lo que esa prueba deja fuera, pero no se ha medido cuánto pesa cada parte.
- **La caché compartida ayuda mucho.** Con la misma consulta, el p95 mejoró de 9,05 s a 2,40 s.
- **Bajo carga se pierde información.** En cerca del 30 % de las búsquedas distintas faltó CheapShark, y la respuesta lo avisó. El plazo de 3 s de esa fuente pudo vencerse por la carga.
- **Algunas respuestas llegan vacías sin explicación.** Con los mismos títulos, las vacías fueron 6, 1 y 5. Una respuesta vacía no puede llevar aviso (S11-F13), así que no se distingue un «no hay resultados» de un fallo.

**Hipótesis no comprobadas:** el cuello de botella puede estar en el límite de 0,5 CPU, sumado a la creación de un cliente HTTP por llamada, ya registrada como deuda en [arc42 §11.7](../arc42/arc42-11-riesgos-y-deuda-tecnica.md). Para confirmarlo hacen falta los registros y `/metrics` del despliegue, que no se consultaron.

**La corrida `misma-3` se conserva.** Duró 36 s, frente a unos 3 s de las otras dos corridas del mismo modo. `/health` ya estaba lento antes de empezar la carga (0,71 s) y una solicitud falló por un error de conexión. No se pudo determinar si la causa fue la red, el servidor o la propia carga. Quitarla habría mejorado el resultado sin justificación. La solicitud fallida se registró con duración 0 en `busqueda_ms`, así que esa corrida no refleja del todo el peor caso.

## Comparación con la línea base de septiembre

La [evidencia E1](e1-linea-base.md) informó un p95 de 1,24 s y concluyó que cumplía. **Las dos cifras no son directamente comparables:**

| | Línea base (13 de septiembre) | Esta medición |
|---|---|---|
| Destino | No declarado en el documento; su script apunta al despliegue serverless de Vercel | Servidor del laboratorio |
| Consultas | Una sola, repetida | Distintas y repetida |
| Repeticiones | No declaradas | 3 por modo |
| Código | Anterior a CheapShark y PlayStation en la búsqueda combinada | Con todas las fuentes y mitigaciones de S13 |

El «cumple» de E1 ya no describe el sistema actual. Esa evidencia se conserva como registro histórico.

## Límites de validez

- Son 50 solicitudes por corrida: el p95 de cada corrida se apoya en pocas muestras.
- Las fuentes reales varían con la hora. Todo se midió en una sola franja de 26 minutos, de noche.
- La carga es un pico de una sola búsqueda por usuario, no tráfico sostenido.
- No se midió caché caliente con 50 consultas distintas: repetir dentro de los 60 s de la caché superaría el límite de 60 búsquedas por minuto.
- El tiempo incluye la red del generador de carga. No incluye el frontend ni el dibujado en el navegador.
- Otras personas pudieron usar el servidor durante la medición.

## Qué se hace con este resultado

El umbral no se cambia para hacerlo cumplir. El incumplimiento queda registrado como **pendiente** en [arc42 §11.10](../arc42/arc42-11-riesgos-y-deuda-tecnica.md), con los siguientes pasos y sin corrección de la demora en esta entrega.

## Lista de cierre antes del proyecto final

| Pendiente | Estado |
|---|---|
| Revisión entre pares en arc42 §11, con estado por señalamiento | **Pendiente:** falta que el equipo aporte el texto de los señalamientos |
| Diagnosticar y atender E1 con búsquedas distintas | Pendiente |
| Aceptar [ADR-0013](../adr/0013-plazo-total-en-la-busqueda-de-steam.md), desplegar el plazo de 4 s y volver a medir E1 | Pendiente: el cambio ya está en el código |
| Registro de IA de la semana 12 en [`ia.md`](../ia.md) | Pendiente: debe escribirlo quien usó la IA esa semana |
| Registro de IA de la [medición local](s14-medicion-e1.md), si se usó IA para hacerla | Pendiente: debe escribirlo quien la hizo |
| Repetir la [medición S12](s12-steam-degradado.md) con las dependencias reales | Pendiente |
| arc42 completo con glosario | Están las 12 secciones; falta revisar que el contenido esté al día |
| C4 de los tres niveles | Están los tres archivos; falta revisar que coincidan con el código |
| Tabla de aspectos recorrible de punta a punta | Las 6 filas tienen enlace en Evidencia; falta recorrer todos los eslabones |
