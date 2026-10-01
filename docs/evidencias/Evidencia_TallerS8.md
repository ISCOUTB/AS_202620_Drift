# DRIFT — Evaluación Serverless: Evidencia, costos, reversión y ADR

**Taller de Arquitecturas Serverless · Arquitectura de software**
**Proyecto DRIFT · API HTTP de búsqueda de videojuegos**
**Autores:** Jerry Buelvas, Mauricio Fernández, Joshua Reyes y Luis Pérez
**Fecha:** 26 de septiembre de 2026

## Resumen ejecutivo

Se evaluó la API HTTP de búsqueda de DRIFT como una pieza candidata a ejecución serverless. El prototipo se desplegó en Vercel como una función Python/FastAPI y se verificó mediante una prueba reproducible con k6. Con 50 usuarios virtuales y una iteración por usuario, la función obtuvo 50/50 respuestas HTTP 200, 0.00% de errores y p95 de 1.66 s, frente al objetivo de p95 ≤ 3 s.

La decisión propuesta es mantener serverless como alternativa viable para esta pieza, sin cambiar la arquitectura Hexagonal de DRIFT ni afirmar que todo el sistema deba ser serverless.

## 1. Escenario, alcance y supuestos

| Elemento | Definición / supuesto |
|---|---|
| Pieza | API HTTP de búsqueda de juegos |
| Contrato | `GET /api/games/search?q=<consulta>` |
| Carga objetivo | Hasta 50 usuarios concurrentes |
| Calidad | p95 ≤ 3 s; errores < 1% |
| Patrón de tráfico | Intermitente; no se exige carga constante |
| Fuente externa | Steam Store API |
| Estado | La función no debe depender de memoria local como almacenamiento persistente |
| Persistencia | No se introduce una base de datos para este prototipo |
| Caché | La función serverless evaluada no usa el caché de 60 s del backend local |
| Costo | Se analiza el plan Hobby vigente y se indican límites que no deben asumirse permanentes |
| Producción | Los resultados de k6 representan una prueba del escenario, no una garantía de producción |

> **Supuesto importante:** el volumen mensual de producción aún no está definido. Por ello, el costo mensual exacto no puede determinarse únicamente a partir de esta prueba de 50 solicitudes.

## 2. Prototipo implementado

Archivos utilizados:

- [`deployment/vercel/api/index.py`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/deployment/vercel/api/index.py) — función FastAPI.
- [`deployment/vercel/requirements.txt`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/deployment/vercel/requirements.txt) — fastapi y httpx.
- [`scripts/k6_baseline.js`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/scripts/k6_baseline.js) — escenario de carga.
- URL pública: https://drift-serverless.vercel.app/api
- Endpoint: https://drift-serverless.vercel.app/api/games/search?q=Minecraft

**Despliegue reproducible:**

```powershell
cd A:\proyectoAS\AS_202620_Drift\deployment\vercel
npx vercel@latest --prod
```

**Prueba funcional reproducible:**

```powershell
curl.exe "https://drift-serverless.vercel.app/api/games/search?q=Minecraft"
```

**Prueba de carga reproducible desde la raíz del repositorio:**

```bash
k6 run scripts/k6_baseline.js
```

## 3. Resultado funcional

La consulta real contra la función pública devolvió cinco resultados de Steam. Se observaron resultados con precios disponibles y otros sin `price_overview`, representados mediante `prices` vacío. Esto se considera una respuesta válida de la fuente y no un fallo de Vercel.

## 4. Resultado de k6

| Métrica | Resultado | Criterio |
|---|---|---|
| Solicitudes | 50 | 50 |
| HTTP 200 | 50/50 | 100% |
| Errores | 0.00% | < 1% |
| Promedio | 1.43 s | Informativo |
| Mediana | 1.49 s | Informativo |
| p90 | 1.63 s | Informativo |
| p95 | 1.66 s | ≤ 3 s |
| Máximo | 1.93 s | Informativo |
| Throughput | 23.15421 req/s | Informativo |

**Conclusión de la prueba:** el prototipo serverless cumple los dos umbrales definidos para el escenario.

## 5. Comparación con el backend local

| Métrica | Local | Vercel | Interpretación |
|---|---|---|---|
| Solicitudes | 50 | 50 | Mismo tamaño de prueba |
| Errores | 0% | 0% | Ambos cumplen |
| Promedio | 1.03 s | 1.43 s | No atribuir diferencia solo a infraestructura |
| p95 | 1.04 s | 1.66 s | Ambos cumplen ≤ 3 s |
| Máximo | 1.04 s | 1.93 s | Vercel presenta mayor variación |

La comparación no es un experimento perfectamente controlado: el backend local original tiene un caché de Steam de 60 segundos, mientras que la función Vercel evaluada realiza la consulta sin ese caché. Por tanto, se usa como referencia de comportamiento, no como prueba causal de superioridad de una infraestructura.

## 6. Evaluación de los siete criterios

| Criterio | Evidencia | Lectura |
|---|---|---|
| 1. Forma del tráfico | Escenario intermitente y 50 VUs en prueba | Compatible con función bajo demanda |
| 2. Latencia | p95 = 1.66 s; umbral = 3 s | Cumple el escenario medido |
| 3. Duración/estado | Operación HTTP acotada; sin estado persistente en memoria | Compatible |
| 4. Dependencias | Steam vía HTTP | Debe contemplarse su latencia/disponibilidad |
| 5. Costo | Hobby: límites de invocaciones, CPU activa y memoria | El límite real depende del patrón de uso |
| 6. Reversibilidad | FastAPI + HTTP; proveedor aislado en `deployment/vercel` | Alta |
| 7. Operación del equipo | CLI y archivos versionados | Debe quedar documentado para todo el equipo |

## 7. Estimación de costo y punto de ruptura

Para esta evaluación se verificó la página oficial de precios de Vercel el 26/09/2026. El plan Hobby aparece con costo de USD 0/mes. La página actual muestra para Vercel Functions con Fluid Compute 1 millón de invocaciones/mes incluidas, 4 horas/mes de Active CPU y 360 GB-horas/mes de memoria provisionada. También muestra 100 GB/mes de transferencia rápida. Los límites y precios pueden cambiar, por lo que esta cifra debe registrarse con su fecha de consulta.

| Recurso Hobby | Incluido/mes | Punto de ruptura |
|---|---|---|
| Invocaciones | 1,000,000 | Al superar el límite no se puede comprar uso adicional en Hobby; se requiere cambiar de plan o reducir uso. |
| Active CPU | 4 h | Cuando el consumo de CPU activa supere 4 h/mes, el límite de cómputo es el primero que debe revisarse. |
| Memoria provisionada | 360 GB-h | Se rompe si el uso acumulado supera 360 GB-h/mes. |
| Fast Data Transfer | 100 GB | Se rompe si el tráfico de salida incluido supera 100 GB/mes. |

### Estimación conservadora con los datos medidos

Si se tomara, de forma deliberadamente conservadora, toda la duración media observada de 1.43 s como si fuera Active CPU facturable, 4 horas equivaldrían aproximadamente a 10,070 invocaciones por mes. Esta cifra **NO** es el límite real esperado, porque Fluid Compute separa Active CPU del tiempo de espera de I/O; la función consulta Steam y buena parte de su tiempo puede ser espera de red. El valor real debe verificarse en Observability/Usage de Vercel.

Por tanto, el punto de ruptura que debe reportarse como dato verificable es: 1 millón de invocaciones, 4 horas de Active CPU, 360 GB-h de memoria y 100 GB de transferencia mensual incluidos en Hobby. Para convertirlos en "usuarios/mes" hace falta conocer cuántas invocaciones genera cada búsqueda y el consumo real de CPU/memoria de la función.

## 8. Procedimiento reproducible completo

1. Clonar el repositorio y entrar en `deployment/vercel`.
2. Confirmar que `api/index.py` y `requirements.txt` contienen la implementación serverless.
3. Ejecutar `npx vercel@latest --prod`.
4. Abrir el endpoint público y comprobar una consulta real con `curl.exe`.
5. Configurar `scripts/k6_baseline.js` para apuntar a `https://drift-serverless.vercel.app/api/games/search?q=Minecraft`.
6. Ejecutar `k6 run scripts/k6_baseline.js` desde la raíz.
7. Registrar p95, errores, promedio, máximo y número de solicitudes.
8. Comparar contra el escenario: p95 ≤ 3 s y errores < 1%.
9. Consultar Usage/Observability de Vercel para registrar invocaciones, Active CPU y memoria.
10. Guardar capturas de la URL pública, respuesta funcional, k6 y Usage como evidencia.

## 9. Procedimiento de reversión

La reversión se diseña para no depender de una reescritura del dominio ni del caso de uso. El backend local/contenedor permanece disponible como alternativa.

1. Mantener el despliegue local/contenedor del backend como ruta alternativa.
2. Retirar el uso de la URL de Vercel en el consumidor que corresponda y apuntarlo al endpoint del backend convencional.
3. No modificar `SearchGames`, `GameRepository` ni el modelo de dominio únicamente para retirar Vercel.
4. Eliminar o conservar `deployment/vercel` como prototipo según la decisión posterior; su existencia no afecta al dominio.
5. Verificar nuevamente `GET /games/search` y ejecutar el k6 baseline contra el backend convencional.
6. Si la reversión es por degradación, conservar los resultados de k6 y los logs para justificar la decisión.

## 10. ADR propuesto

El ADR asociado debe registrar la decisión como una decisión de despliegue para una pieza, no como un cambio de arquitectura global. El archivo propuesto es [`docs/adr/0006-despliegue-serverless-api-busqueda.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0006-despliegue-serverless-api-busqueda.md).

## 11. Conclusión

El prototipo demuestra que la API de búsqueda puede ejecutarse en Vercel para el escenario evaluado: 50 usuarios concurrentes, p95 ≤ 3 s y errores < 1%. La decisión es técnicamente viable para esta pieza, pero queda condicionada a la evolución del volumen, consumo real de Active CPU/memoria, dependencia de Steam y límites del plan. La solución es reversible porque el contrato HTTP y la lógica de aplicación permanecen independientes del proveedor.
