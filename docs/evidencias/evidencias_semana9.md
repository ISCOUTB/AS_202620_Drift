# 1. Evidencia S9 — Generación verificada y trazable

## 2. Matriz de evaluación

| Criterio de evaluación | Evidencia documentada |
|---|---|
| 2.1 Porción real del sistema construida con apoyo de IA | Ver sección 2.1 |
| 2.2 Cadena completa navegable para esa porción | Ver sección 2.2 |
| 2.3 ADR con la decisión argumentada por el equipo | Ver sección 2.3 |
| 2.4 Prueba que falla ante el defecto que cubre | Ver sección 2.4 |
| 2.5 Medición del escenario asociado | Ver sección 2.5 |
| 2.6 `docs/ia.md` con lo aceptado, lo corregido y lo rechazado con motivo | Ver sección 2.6 |
| 2.7 Auditoría de erosión sobre límites de contexto y propiedad de datos | Ver sección 2.7 |
| 2.8 Dependencias propuestas verificadas en su registro oficial | Ver sección 2.8 |
| 2.9 Sin credenciales en código, ejemplos ni documentación generada | Ver sección 2.9 |
| 2.10 Componente generativo evaluado, con costo y latencia, o ADR de no incorporarlo | Ver sección 2.10 |

## 2.1 Porción real del sistema construida con apoyo de IA

### 2.1.1 Porción del sistema identificada

La porción seleccionada para la evidencia corresponde al adaptador encargado de realizar las búsquedas de juegos en Steam:

```text
backend/app/infrastructure/external/steam/steam_game_repository.py
```

Esta porción forma parte del backend de DRIFT y corresponde a la integración con la fuente externa Steam.

### 2.1.2 Historial del archivo

Para identificar los commits relacionados con la porción seleccionada se ejecutó:

```bash
git log --all --oneline -- backend/app/infrastructure/external/steam/steam_game_repository.py
```

Resultado:

```text
a4b2d3c feat: agregar resiliencia y compatibilidad backend
b9ff5b0 Mi cambio
```

Esto permite identificar dos modificaciones relevantes en la historia del archivo.

### 2.1.3 Commit de creación

El archivo `steam_game_repository.py` fue creado en el commit:

```text
b9ff5b05b47e9e4e27cc6ba5d5c2f92bebc3a3b2
```

Mensaje del commit:

```text
Mi cambio
```

El commit incorporó inicialmente el archivo:

```text
backend/app/infrastructure/external/steam/steam_game_repository.py
```

### 2.1.4 Commit de modificación

Posteriormente, el archivo fue modificado mediante el commit:

```text
a4b2d3ce8ffc935c068c6b99c5a82acbf7bd1140
```

Fecha:

```text
2026-09-13
```

Mensaje:

```text
feat: agregar resiliencia y compatibilidad backend
```

La modificación se verificó mediante:

```bash
git show a4b2d3c -- backend/app/infrastructure/external/steam/steam_game_repository.py
```

Entre los elementos incorporados en esta modificación se encuentran:

```python
import time
from concurrent.futures import ThreadPoolExecutor
```

También se verificó directamente el estado del archivo dentro de dicho commit mediante:

```bash
git show a4b2d3c:backend/app/infrastructure/external/steam/steam_game_repository.py
```

El resultado confirmó la existencia del archivo y de la implementación modificada de `SteamGameRepository` en ese commit.

### 2.1.5 Relación con la documentación del uso de IA

La documentación del uso de inteligencia artificial del proyecto se encuentra en:

```text
docs/ia.md
```

Su historial fue consultado mediante:

```bash
git log --all --oneline -- docs/ia.md
```

Resultado:

```text
74709aa Add deployment planning section to ia.md
8673f21 Update ia.md
0129608 Document automated contract testing and validation process
978db54 Add documentation for new API integration in DRIFT
5f7fa4c Fix spacing issue in documentation
e1e2873 Fix formatting in Registro 4 section of ia.md
d142787 docs: registrar evidencia S6 y calidad continua
0c5bea9 Update ia.md
c12dda8 Document vertical cut test process in ia.md
d3d0ab7 Revise usage section for DRIFT command execution
770923e Update ia.md with script organization and command usage
6225591 Revise ia.md for new execution command
aa32ae1 Update ia.md for single command execution
```

La documentación `docs/ia.md` contiene los registros del uso de IA realizado durante el desarrollo del proyecto. La correspondencia específica entre dichos registros y la modificación de `SteamGameRepository` se comprobará posteriormente mediante la evidencia documental correspondiente.

### 2.1.6 Evidencia técnica reunida

La porción queda identificada mediante:

```text
Archivo:
backend/app/infrastructure/external/steam/steam_game_repository.py

Commit de creación:
b9ff5b05b47e9e4e27cc6ba5d5c2f92bebc3a3b2

Commit de modificación:
a4b2d3ce8ffc935c068c6b99c5a82acbf7bd1140

Fecha de modificación:
2026-09-13

Documentación relacionada:
docs/ia.md
```

Estas evidencias permiten localizar en el repositorio la porción concreta del sistema y reconstruir su historial mediante Git.

## 2.2 Cadena navegable desde el aspecto de calidad hasta la evidencia

### 2.2.1 Punto de entrada: aspecto de calidad

En [`docs/aspectos.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/aspectos.md) se encuentra el aspecto de calidad:

**E1 — Eficiencia de desempeño**

El escenario establece:

- **Fuente:** Usuario de DRIFT.
- **Estímulo:** búsqueda de un videojuego para comparar su precio.
- **Artefacto:** módulo de búsqueda y comparación de precios de DRIFT.
- **Entorno:** sistema funcionando normalmente con hasta 50 usuarios concurrentes.
- **Respuesta:** DRIFT consulta y muestra los precios disponibles del videojuego en las diferentes tiendas digitales.
- **Medida verificable:** p95 ≤ 3 segundos.

La fila E1 enlaza con el escenario correspondiente en [`docs/escenarios.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/escenarios.md).

### 2.2.2 Escenario asociado

El escenario se encuentra en:

```text
docs/escenarios.md#escenario-1
```

El Escenario 1 corresponde a:

- **Atributo:** Eficiencia de desempeño
- **Fuente:** Usuario de DRIFT
- **Estímulo:** búsqueda de un videojuego
- **Artefacto:** módulo de búsqueda y comparación de precios
- **Entorno:** hasta 50 usuarios concurrentes
- **Respuesta:** consulta y muestra de precios
- **Medida verificable:** p95 ≤ 3 segundos

El método de verificación definido consiste en realizar una prueba de carga sobre el endpoint de búsqueda, simulando hasta 50 usuarios concurrentes, registrar los tiempos de respuesta y calcular el percentil 95.

### 2.2.3 Decisión arquitectónica relacionada

La trazabilidad también se relaciona con los ADR documentados en `docs/adr/`.

En particular, [`docs/adr/0006-despliegue-serverless-api-busqueda.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0006-despliegue-serverless-api-busqueda.md) documenta el escenario de evaluación de la API de búsqueda y establece:

- Hasta 50 usuarios concurrentes
- p95 ≤ 3 segundos

El ADR especifica que la prueba se realiza mediante k6 utilizando 50 usuarios virtuales y define como condición de medición:

```text
p95 < 3000 ms
```

El ADR también vincula el escenario con el endpoint:

```text
GET /games/search?q=<consulta>
```

Además, el ADR documenta el despliegue de la API de búsqueda como una pieza serverless y mantiene esta decisión como una alternativa de despliegue para la pieza evaluada, sin plantearla como un cambio de la arquitectura Hexagonal global de DRIFT.

### 2.2.4 Artefacto de prueba

La implementación del método de verificación se encuentra en:


[`scripts/k6_baseline.js`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/scripts/k6_baseline.js)


El script define:

```javascript
vus: 50
iterations: 1
maxDuration: "30s"
```

y establece los umbrales:

```javascript
http_req_duration: ["p(95)<3000"]
http_req_failed: ["rate<0.01"]
```

La prueba realiza la solicitud sobre:

[`https://drift-serverless.vercel.app/api/games/search?q=Minecraft`](https://drift-serverless.vercel.app/api/games/search?q=Minecraft)


También verifica que la respuesta HTTP tenga código 200.

El historial del script fue consultado mediante:

```bash
git log --all --oneline -- scripts/k6_baseline.js
```

Resultado:

```text
1b8a51b perf: actualizar baseline de k6
3c816ed feat: integrar compatibilidad en frontend y evidencias
```

### 2.2.5 Evidencia de ejecución y optimización

Los resultados de la prueba y la evolución del rendimiento se encuentran documentados en:

[`docs/evidencias/e1-linea-base.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/evidencias/e1-linea-base.md)

El documento registra la configuración de la prueba con:

- 50 usuarios virtuales concurrentes
- 1 solicitud por usuario virtual
- 50 solicitudes totales
- p95 menor a 3 segundos
- `scripts/k6_baseline.js`

También registra una medición inicial:

- **Solicitudes exitosas:** 50 de 50
- **Solicitudes fallidas:** 0 %
- **p95:** 14.63 s

Posteriormente documenta la medición después de la optimización:

- **Solicitudes exitosas:** 50 de 50
- **Solicitudes fallidas:** 0 %
- **p95:** 1.24 s

### 2.2.6 Evidencia del despliegue serverless

Como evidencia complementaria de la ejecución de la API de búsqueda desplegada en Vercel se encuentra:

[`docs/evidencias/Evidencia_TallerS8.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/evidencias/Evidencia_TallerS8.md)


Este documento corresponde al taller de evaluación serverless de DRIFT y documenta el prototipo desplegado como una función Python/FastAPI en Vercel.

La evidencia utiliza el mismo escenario general de evaluación:

- **Carga objetivo:** hasta 50 usuarios concurrentes.
- **Contrato evaluado:** `GET /api/games/search?q=<consulta>`.
- **Calidad:** p95 ≤ 3 segundos y errores < 1 %.
- **Herramienta:** k6.

La prueba contra el endpoint público:


[`https://drift-serverless.vercel.app/api/games/search?q=Minecraft`](https://drift-serverless.vercel.app/api/games/search?q=Minecraft)


registró:

| Métrica | Resultado |
|---|---|
| Solicitudes | 50 |
| HTTP 200 | 50/50 |
| Errores | 0.00 % |
| Promedio | 1.43 s |
| Mediana | 1.49 s |
| p90 | 1.63 s |
| p95 | 1.66 s |
| Máximo | 1.93 s |
| Throughput | 23.15421 req/s |

El documento también registra una comparación entre la ejecución local y la ejecución en Vercel. Esta comparación se presenta como referencia de comportamiento y no como un experimento causal de superioridad de una infraestructura.

### 2.2.7 Relación entre medición y código

[`docs/evidencias/e1-linea-base.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/evidencias/e1-linea-base.md) documenta tres modificaciones aplicadas a `SteamGameRepository`:

- Caché de resultados de búsqueda durante 60 segundos.
- Límite de cinco resultados por consulta.
- Consulta paralela de los detalles de los videojuegos en Steam.

El archivo correspondiente es:


[`backend/app/infrastructure/external/steam/steam_game_repository.py`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/backend/app/infrastructure/external/steam/steam_game_repository.py)


El historial de este archivo muestra:

```text
a4b2d3c feat: agregar resiliencia y compatibilidad backend
b9ff5b0 Mi cambio
```

El commit `a4b2d3c` fue fechado el 2026-09-13 y modificó el adaptador de Steam. La inspección del diff permitió verificar la incorporación de cambios relacionados con la implementación del repositorio, incluyendo el uso de `time` y `ThreadPoolExecutor`.

La evidencia [`docs/evidencias/Evidencia_TallerS8.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/evidencias/Evidencia_TallerS8.md) documenta adicionalmente la ejecución de la pieza serverless desplegada en Vercel, manteniendo el contrato HTTP de búsqueda y utilizando el mismo escenario de carga definido para E1.

### 2.2.8 Trazabilidad de la evidencia

La cadena documental y técnica queda distribuida entre:


[docs/aspectos.md](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/aspectos.md)
    ↓
E1 — Eficiencia de desempeño
    ↓
[docs/escenarios.md](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/escenarios.md)
    ↓
Escenario 1
    ↓
[docs/adr/0006-despliegue-serverless-api-busqueda.md](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0006-despliegue-serverless-api-busqueda.md)
    ↓
Prueba mediante k6
    ↓
[scripts/k6_baseline.js](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/scripts/k6_baseline.js)
    ↓
[docs/evidencias/e1-linea-base.md](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/evidencias/e1-linea-base.md)
    ↓
[backend/app/infrastructure/external/steam/steam_game_repository.py](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/backend/app/infrastructure/external/steam/steam_game_repository.py)


Como evidencia complementaria de la ejecución desplegada:

```text
docs/evidencias/Evidencia_TallerS8.md
    ↓
deployment/vercel/api/index.py
    ↓
GET /api/games/search?q=Minecraft
    ↓
50 solicitudes
0.00 % de errores
p95 = 1.66 s
```

Los resultados documentados incluyen la medición inicial de 14.63 segundos de p95, la medición posterior de 1.24 segundos de p95 después de la optimización y la evaluación del prototipo serverless en Vercel con p95 de 1.66 segundos.


## 2.3 ADR con la decisión argumentada por el equipo

La estrategia de integración con fuentes externas de DRIFT está documentada en el [**ADR-0004 — Estrategia de integración**](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0004-estrategia-de-integracion.md), cuyo estado es Aceptado y cuyos decisores se identifican como el **Equipo DRIFT**.

El ADR plantea el problema de integrar fuentes externas manteniendo la mantenibilidad del sistema y aislando las dependencias de proveedores externos. Para ello se analizaron tres alternativas:

- integración completamente síncrona;
- integración completamente asíncrona;
- estrategia híbrida.

La decisión documentada fue adoptar una estrategia híbrida: operaciones síncronas para las consultas inmediatas de los usuarios y mecanismos asíncronos para actualizaciones periódicas de las fuentes externas. El ADR establece además que cada fuente externa debe estar encapsulada mediante un adaptador, evitando que la lógica del sistema dependa directamente del proveedor externo.

**Evidencia:** [`docs/adr/0004-estrategia-de-integracion.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0004-estrategia-de-integracion.md)

La relación con la implementación seleccionada se observa en `backend/app/infrastructure/external/steam/steam_game_repository.py`. Este componente implementa el puerto `GameRepository` y concentra la comunicación HTTP con la API de Steam mediante las operaciones `storesearch` y `appdetails`. La información externa se transforma al modelo `Game`, manteniendo la integración con Steam localizada en infraestructura.

La documentación arquitectónica también identifica explícitamente a `SteamGameRepository` como responsable de la integración con Steam y ubica el precio de Steam y la caché temporal dentro del contexto de **Integración de fuentes externas**.

**Evidencia complementaria:** [`docs/adr/0003-reajuste-contextos-dominio.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0003-reajuste-contextos-dominio.md)

ADR-0003 incluye explícitamente `SteamGameRepository` dentro de la decisión de reajuste de responsabilidades y lo relaciona con el contexto de Integración de fuentes externas. La decisión mantiene la arquitectura Hexagonal y define responsabilidades específicas para `SearchGames`, `SteamGameRepository`, `InMemoryGameRepository` y `ResilientGameRepository`.

**Trazabilidad documental y de implementación:**

- ADR-0004: `eb79b7f` — `Add ADR-0004 for hybrid integration strategy`
- Implementación de `SteamGameRepository`: `b9ff5b0` — `Mi cambio`
- Modificación posterior de `SteamGameRepository`: `a4b2d3c` — `feat: agregar resiliencia y compatibilidad backend`

La trazabilidad histórica muestra que `SteamGameRepository` existía antes de la creación de ADR-0004; por ello, la evidencia no presenta el ADR como el commit que originó el adaptador, sino como la decisión arquitectónica documentada sobre la estrategia de integración con fuentes externas. ADR-0003 proporciona la relación explícita entre esa responsabilidad arquitectónica y `SteamGameRepository`.


## 2.4 Prueba que falla ante el defecto que cubre

La evidencia de regresión se encuentra en una ruptura intencional del contrato de la API introducida en el commit **`9c102df49a54153ca3b4b8c302fb9da59785f58f`**, con mensaje `test: introducir ruptura intencional del contrato`.

En `backend/app/main.py`, el commit modifica deliberadamente el nombre del campo de respuesta de la búsqueda:

- **Antes:** `"name": game.name`
- **Defecto introducido:** `"tittle": game.name`

El cambio se realizó sobre el endpoint de búsqueda y altera el contrato esperado de la respuesta.

**Commit que introduce el defecto:** `9c102df`

**Evidencia del cambio:**

```diff
- "name": game.name,
+ "tittle": game.name,
```

La ruptura fue ejecutada contra el pipeline de integración continua y produjo una ejecución fallida:

**CI fallido:** [`36301332490`](https://github.com/ISCOUTB/AS_202620_Drift/actions/runs/36301332490)

Posteriormente, el commit `97508788fe2e9cad0f78b96eabac518da943a353`, con mensaje [`fix: restaurar contrato de la API DRIFT`](https://github.com/ISCOUTB/AS_202620_Drift/actions/runs/36301421472), revierte exactamente el cambio:

```diff
- "tittle": game.name,
+ "name": game.name,
```

La secuencia histórica documentada es:

`9c102df` → ruptura intencional del contrato → CI fallido `36301332490` → `9750878` → restauración de `"name"`.

El historial de `backend/tests/` también registra pruebas automatizadas del backend, incluyendo el recorrido vertical de búsqueda y las pruebas de contrato con Schemathesis:

- `d110d6d` — `test: add vertical slice search test`
- `9f238ab` — `feat: add contract testing with schemathesis`
- `6bc661e` — `test: actualizar expectativas de identificadores`

**Evidencia complementaria:** historial de commits de `backend/tests/`.


## 2.5 Medición escenario asociado

El componente seleccionado está asociado al **Escenario E1 — Eficiencia de desempeño**, documentado en [`docs/escenarios.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/escenarios.md).

E1 establece una condición de hasta **50 usuarios concurrentes** y una medida verificable de **p95 ≤ 3 segundos**. El procedimiento de verificación se encuentra definido mediante una prueba de carga sobre el endpoint de búsqueda.

**Evidencia:** [`docs/escenarios.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/escenarios.md)

El procedimiento de medición está implementado en:

[`scripts/k6_baseline.js`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/scripts/k6_baseline.js)

Los resultados de la medición del escenario se encuentran registrados en:

[`docs/evidencias/e1-linea-base.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/evidencias/e1-linea-base.md)

Esta evidencia contiene la medición inicial y la medición posterior a las modificaciones realizadas en `SteamGameRepository`, incluyendo los valores de p95 correspondientes.

Adicionalmente, los resultados obtenidos en el **servidor/despliegue serverless** se encuentran documentados en:

[`docs/evidencias/Evidencia_TallerS8.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/evidencias/Evidencia_TallerS8.md)

Esta evidencia complementa la medición principal con los resultados obtenidos sobre el despliegue del sistema.

La trazabilidad del escenario queda establecida como:

`E1 → docs/escenarios.md → scripts/k6_baseline.js → docs/evidencias/e1-linea-base.md → SteamGameRepository`

Con evidencia complementaria del despliegue en:

`docs/evidencias/Evidencia_TallerS8.md`


## 2.6 `docs/ia.md` — Registro de uso de IA con validación técnica

El uso de Inteligencia Artificial durante el desarrollo de DRIFT está documentado en:

[`docs/ia.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/ia.md)

El documento establece que ChatGPT fue utilizado como apoyo para comprender conceptos, proponer alternativas, revisar documentación, orientar implementaciones y detectar inconsistencias. También establece que las decisiones arquitectónicas, los cambios aplicados y la validación final fueron responsabilidad del equipo.

**Evidencia:** [`docs/ia.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/ia.md)

El registro documenta consultas realizadas durante el desarrollo y especifica el uso dado a las respuestas de IA, junto con la validación realizada por el equipo y, cuando corresponde, las alternativas descartadas por razones técnicas.

Entre los registros relacionados con el trabajo evaluado se encuentran:

- **Registro 24:** revisión de la arquitectura Hexagonal y separación de responsabilidades.
- **Registro 25:** revisión y optimización de `SteamGameRepository`.
- **Registro 29:** configuración de la prueba de rendimiento con k6 para E1.
- **Registro 30:** análisis de la medición inicial de rendimiento.
- **Registro 31:** validación posterior de E1 frente al umbral establecido.
- **Registro 32:** revisión del contrato de búsqueda.
- **Registro 33:** introducción de una ruptura controlada del contrato.
- **Registro 34:** documentación del fallo de CI producido por el defecto.
- **Registro 36:** relación entre ADR-0004 y `SteamGameRepository`.
- **Registro 37:** trazabilidad del componente seleccionado.
- **Registro 38:** organización de las evidencias de la evaluación S9.
- **Registro 39:** diferenciación entre la medición principal de E1 y las mediciones complementarias del despliegue.
- **Registro 40:** organización de las evidencias S9 a partir de archivos, commits, pruebas y resultados verificables.

Los registros incluyen decisiones, validaciones y alternativas descartadas con su justificación técnica. Por ejemplo, en el Registro 31 se documenta que el umbral de E1 no fue modificado para aceptar la medición inicial, sino que se volvió a ejecutar la prueba después de optimizar la implementación. :contentReference[oaicite:0]{index=0}

La trazabilidad del uso de IA queda respaldada directamente por el historial y contenido de `docs/ia.md`, incluyendo los registros correspondientes al componente seleccionado, su medición de rendimiento, las pruebas de contrato y la preparación de la evidencia S9. 

## 2.7 Auditoría de erosión arquitectónica

Se realizó una auditoría de dependencias entre las capas de la arquitectura Hexagonal, revisando específicamente las importaciones existentes entre `domain`, `application` e `infrastructure`.

### Hallazgo identificado

La auditoría inicial encontró una dependencia directa desde la capa de aplicación hacia infraestructura en:

`backend/app/application/usecases/sync_playstation_catalog.py`

El componente `SyncPlayStationCatalog` recibía como dependencia concreta `InMemoryPlayStationCatalog`, importada directamente desde:

`app.infrastructure.persistence.in_memory_playstation_catalog`

Esto introducía conocimiento de infraestructura dentro del caso de uso de aplicación y constituía una erosión de la separación de responsabilidades establecida por la arquitectura.

### Corrección aplicada

Para eliminar la dependencia concreta de infraestructura se creó el puerto:

`backend/app/domain/ports/game_catalog_repository.py`

El nuevo puerto `GameCatalogRepository` define la operación `replace()` requerida por el caso de uso.

Posteriormente, `SyncPlayStationCatalog` fue modificado para depender del puerto:

`GameCatalogRepository`

en lugar de depender directamente de:

`InMemoryPlayStationCatalog`

La implementación concreta `InMemoryPlayStationCatalog` permanece en infraestructura y ahora implementa tanto `GameRepository` como `GameCatalogRepository`.

La estructura resultante mantiene la dirección de dependencias de la arquitectura:

`Application → Domain Port ← Infrastructure Adapter`

### Verificación de la auditoría

Después de la corrección se verificó que no existieran importaciones de infraestructura desde la capa de aplicación mediante:

`git grep -nE "^from app\.infrastructure|^import app\.infrastructure" app/application`

La búsqueda no produjo resultados.

También se verificó que `SyncPlayStationCatalog` recibiera `GameCatalogRepository` y que la importación directa de infraestructura hubiera sido eliminada.

La importación de los componentes modificados fue comprobada mediante una prueba directa, obteniendo:

`OK`

Finalmente, se ejecutó la suite automatizada completa del backend con el servidor necesario para las pruebas de contrato activo:

`pytest -q`

Resultado:

`14 passed in 583.64s`

### Trazabilidad de la corrección

La corrección quedó registrada en el commit:

`0ebb19e` — `fix: remove infrastructure dependency from application layer`

El commit fue enviado correctamente a `origin/master`.

La secuencia de evidencia queda establecida como:

`hallazgo en SyncPlayStationCatalog → creación de GameCatalogRepository → eliminación de dependencia de infrastructure → implementación del puerto por InMemoryPlayStationCatalog → auditoría sin dependencias indebidas → 14 pruebas automatizadas pasando → commit 0ebb19e`


## 2.8 Dependencias añadidas y comprobación

La trazabilidad de las dependencias incorporadas al proyecto se verificó mediante el historial Git de los archivos de gestión de dependencias:

- [`backend/requirements.txt`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/backend/requirements.txt)
- [`frontend/package.json`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/frontend/package.json)

### Dependencias del backend

El commit `30d5e99` — `Update requirements.txt with new packages` — incorporó la lista inicial de dependencias del backend en `backend/requirements.txt`, incluyendo:

- `annotated-doc==0.0.5`
- `annotated-types==0.8.0`
- `anyio==4.15.0`
- `certifi==2026.7.22`
- `charset-normalizer==3.5.1`
- `click==8.5.0`
- `fastapi==0.141.1`
- `h11==0.16.0`
- `httpcore==1.0.9`
- `httpx==0.28.1`
- `idna==3.19`
- `pydantic==2.13.5`
- `pydantic_core==2.46.5`
- `requests==2.34.2`
- `starlette==1.6.0`
- `typing-inspection==0.4.4`
- `typing_extensions==4.16.0`
- `urllib3==2.7.0`
- `uvicorn==0.52.4`

Posteriormente, el commit `9f238ab` — `feat: add contract testing with schemathesis` — incorporó `schemathesis` al backend.

La dependencia fue actualizada posteriormente mediante:

- `84ea74c` — actualización de Schemathesis a `4.7.0`.
- `576c02c` — actualización de Schemathesis a `4.27.5`.

El commit `92fd004` — `chore: preparar backend para Azure App Service` — añadió:

- `gunicorn==23.0.0`

La versión actual de `backend/requirements.txt` mantiene estas dependencias declaradas con versiones explícitas.

### Dependencias del frontend

El commit `b1270ac` — `feat: configuracion inicial frontend` — creó la configuración inicial de `frontend/package.json` e incorporó:

- `next: latest`
- `react: latest`
- `react-dom: latest`

Estas dependencias se gestionan mediante el registro oficial npm.

### Comprobación en registros oficiales

Las dependencias Python utilizadas por DRIFT se gestionan mediante PyPI. Se verificó la existencia en el registro oficial de las versiones concretas incorporadas posteriormente al proyecto:

- [FastAPI 0.141.1 — PyPI](https://pypi.org/project/fastapi/0.141.1/)
- [Schemathesis 4.27.5 — PyPI](https://pypi.org/project/schemathesis/4.27.5/)
- [Gunicorn 23.0.0 — PyPI](https://pypi.org/project/gunicorn/23.0.0/)

Las dependencias JavaScript se gestionan mediante npm. El registro oficial identifica los paquetes utilizados por el frontend:

- [Next.js — npm](https://www.npmjs.com/package/next)
- [React — npm](https://www.npmjs.com/package/react)
- [React DOM — npm](https://www.npmjs.com/package/react-dom)

En `frontend/package.json`, `next`, `react` y `react-dom` están declarados con el tag `latest`. Por tanto, el archivo identifica el paquete y su registro de origen, pero no fija una versión concreta.

### Trazabilidad

La cadena de comprobación queda establecida como:

`historial Git → archivo de dependencias → dependencia añadida → registro oficial → comprobación del paquete`

Principales commits involucrados:

- `30d5e99` — incorporación de las dependencias iniciales del backend.
- `9f238ab` — incorporación de Schemathesis.
- `84ea74c` — actualización de Schemathesis.
- `576c02c` — actualización de Schemathesis a `4.27.5`.
- `92fd004` — incorporación de Gunicorn.
- `b1270ac` — configuración inicial de las dependencias del frontend.

## 2.9 No credenciales en código, ejemplos ni documentación

Se realizó un barrido del repositorio para detectar posibles credenciales o valores sensibles expuestos en código, ejemplos y documentación.

El barrido general se ejecutó mediante:

`git grep -nEi "api[_-]?key|secret|token|password|passwd|authorization|bearer|access[_-]?token|private[_-]?key" -- . ':!*.lock'`

El resultado únicamente mostró referencias a mecanismos de gestión de secretos, principalmente:

- referencias `${{ secrets.* }}` utilizadas por GitHub Actions para autenticación de Azure;
- referencias al secreto `SONAR_TOKEN`;
- menciones documentales relacionadas con el manejo externo de secretos.

No se encontraron los valores de dichos secretos dentro del repositorio.

También se realizó un barrido específico de la documentación mediante:

`git grep -nEi "api[_-]?key|secret|token|password|passwd|authorization|bearer|access[_-]?token|private[_-]?key" -- docs`

Este barrido encontró únicamente menciones documentales en `docs/evidencias/evidencia_semana8.md` y `docs/ia.md`, incluyendo la documentación del uso de `secrets.*` y la indicación explícita de que los valores reales de los secretos no se encuentran en el repositorio.

Finalmente, se realizó una búsqueda específica de asignaciones directas de posibles credenciales mediante `Select-String`, buscando patrones como:

`api_key = "valor"`
`token = "valor"`
`password = "valor"`
`secret = "valor"`
`private_key = "valor"`

La búsqueda no produjo resultados.

La revisión incluyó el código fuente y la documentación versionada, incluyendo `docs/`, y no identificó valores de credenciales escritos directamente en el repositorio.

**Evidencia principal:** barrido del repositorio mediante `git grep`.

**Evidencia específica de documentación:** barrido de `docs/`.

**Evidencia complementaria:** búsqueda de asignaciones directas de valores sensibles mediante `Select-String`.

Las referencias encontradas corresponden a nombres o referencias de secretos gestionados externamente, no a los valores de las credenciales.


## 2.10 Evaluación de incorporación de IA generativa

La incorporación de un componente de Inteligencia Artificial generativa fue evaluada respecto al alcance actual de DRIFT y quedó documentada mediante el **ADR-0007 — Evaluación de incorporación de IA generativa**.

El ADR establece la decisión de **no incorporar IA generativa dentro del alcance actual del proyecto**, debido a que las funcionalidades principales de DRIFT pueden resolverse mediante búsqueda, filtrado, comparación y procesamiento de datos estructurados.

Entre las funcionalidades actuales se encuentran la búsqueda de videojuegos, comparación de precios y evaluación de compatibilidad de PC. También es posible realizar operaciones como el filtrado por género sin requerir un modelo generativo, ya que esta operación puede resolverse mediante los datos y reglas correspondientes del sistema.

El ADR considera como alternativas posibles la incorporación de un chatbot generativo, el uso de IA generativa para recomendaciones y el mantenimiento del procesamiento mediante lógica convencional. La decisión documentada mantiene esta última alternativa para el alcance actual, evitando introducir una dependencia de modelos generativos sin una necesidad funcional que la justifique.

La decisión no impide una futura evaluación de IA generativa si DRIFT incorpora funcionalidades que requieran interpretación de lenguaje natural, interacción conversacional o generación de contenido. En ese caso, se establece que deberá realizarse una nueva evaluación arquitectónica mediante un ADR.

**Evidencia principal:**

[`docs/adr/0007-evaluacion-de-ia-generativa.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0007-evaluacion-de-incorporación-coponente-generativo.md)

**Evidencia complementaria:**

Los ADR anteriores de DRIFT documentan la arquitectura, integración, despliegue y organización de responsabilidades del sistema, pero no establecían una decisión específica sobre incorporación de IA generativa. El ADR-0007 formaliza esta decisión dentro de la arquitectura del proyecto.
