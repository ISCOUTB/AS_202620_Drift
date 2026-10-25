# DRIFT — Comparador Inteligente de Videojuegos

Proyecto del curso **Arquitectura de Software (AS_202620)** — Universidad Tecnológica de Bolívar.

## ¿Qué es DRIFT?

**DRIFT** es una plataforma web para apoyar la decisión de compra de videojuegos. Permite buscar juegos, consultar precios disponibles, identificar la mejor opción mostrada y estimar compatibilidad básica de PC.

El sistema está diseñado para incorporar nuevas fuentes externas de información sin afectar el núcleo de negocio.

- [Ficha del problema](docs/ficha_problema.md)
- [Aspectos y escenarios de calidad](docs/aspectos.md)

## Equipo de desarrollo

- Mauricio Fernández Espinosa
- Jerry Buelvas Mejía
- Luis Pérez Diaz
- Joshua Reyes Leones

## Arquitectura

DRIFT adopta una **Arquitectura Hexagonal (Ports and Adapters)**.

- El backend usa **FastAPI**.
- El frontend usa **Next.js**.
- Los casos de uso dependen de puertos del dominio, no de servicios externos concretos. Cada fuente externa es un adaptador:

| Fuente | Para qué se usa | Adaptador |
|---|---|---|
| Steam | Fuente principal: búsqueda, precio en pesos, portada y requisitos de PC | `backend/app/infrastructure/external/steam/` |
| CheapShark | Precios de otras tiendas de PC (GOG, Epic, Humble, Fanatical y más) | `backend/app/infrastructure/external/cheapshark/` |
| PlayStation Store Colombia | Precio de la versión de consola | `backend/app/infrastructure/external/playstation/` |
| open.er-api.com | Tasa de cambio de dólares a pesos | `backend/app/infrastructure/external/exchange/` |

- Las fuentes se consultan en paralelo, cada una con un plazo de 3 segundos. Si una no responde a tiempo, la búsqueda sigue con las demás y avisa cuál faltó en `unavailable_sources`.
- Steam tiene además timeout explícito, un reintento con espera creciente y validación de sus respuestas. Si falla, se usa un catálogo local de respaldo.
- `backend/tests/test_architecture.py` falla si el dominio o la aplicación importan infraestructura.

Decisiones de arquitectura vigentes:

| ADR | Decisión |
|---|---|
| [ADR-0002](docs/adr/0002-adoptar-nextjs-fastapi-arquitectura-hexagonal.md) | Next.js y FastAPI sobre arquitectura hexagonal (reemplaza a [ADR-0001](docs/adr/0001-adoptar-arquitectura-hexagonal.md)) |
| [ADR-0003](docs/adr/0003-reajuste-contextos-dominio.md) | Contextos y responsabilidades del dominio |
| [ADR-0004](docs/adr/0004-estrategia-de-integracion.md) | Estrategia de integración con fuentes externas (la persistencia y la actualización asíncrona las sustituye ADR-0008) |
| [ADR-0005](docs/adr/0005-estrategia-despliegue.md) | Estrategia de despliegue |
| [ADR-0006](docs/adr/0006-despliegue-serverless-api-busqueda.md) | Despliegue serverless para la API de búsqueda |
| [ADR-0007](docs/adr/0007-evaluacion-incorporacion-componente-generativo.md) | No incorporar un componente generativo |
| [ADR-0008](docs/adr/0008-persistencia-ejecucion-y-degradacion-de-fuentes.md) | Persistencia en memoria, ejecución síncrona y degradación controlada de fuentes |
| [ADR-0009](docs/adr/0009-decision-extraccion-integracion-steam.md) | Mantener la integración con Steam dentro del backend, con resiliencia en el adaptador |
| [ADR-0010](docs/adr/0010-costo-de-reversion-de-las-decisiones-de-datos.md) | Costo de reversión de las decisiones de datos; mantener el modelo público del juego como decisión de alto costo de cambio |

## Organización del proyecto

```text
DRIFT/
├── backend/
│   ├── app/
│   │   ├── application/
│   │   │   └── usecases/
│   │   │       ├── search_games.py
│   │   │       ├── estimate_compatibility.py
│   │   │       └── sync_playstation_catalog.py
│   │   ├── domain/
│   │   │   ├── model/
│   │   │   │   ├── game.py
│   │   │   │   ├── game_requirements.py
│   │   │   │   └── normalized_game.py
│   │   │   └── ports/
│   │   │       ├── game_repository.py
│   │   │       ├── game_requirements_repository.py
│   │   │       └── game_catalog_source.py
│   │   ├── infrastructure/
│   │   │   ├── external/
│   │   │   │   ├── steam/
│   │   │   │   │   └── steam_game_repository.py
│   │   │   │   └── playstation/
│   │   │   │       └── playstation_game_catalog_source.py
│   │   │   └── persistence/
│   │   │       ├── in_memory_game_repository.py
│   │   │       ├── in_memory_game_requirements_repository.py
│   │   │       ├── in_memory_playstation_catalog.py
│   │   │       ├── combined_game_repository.py
│   │   │       └── resilient_game_repository.py
│   │   └── main.py
│   ├── tests/
│   │   ├── test_health.py
│   │   ├── test_search_games.py
│   │   └── test_compatibility.py
│   └── requirements.txt
│
├── frontend/
│   ├── application/
│   ├── domain/
│   ├── infrastructure/
│   └── ui/
│       └── components/
│           └── DriftHome.js
│
├── docs/
│   ├── adr/
│   ├── arc42/
│   ├── c4/
│   ├── evidencias/
│   ├── api/
│   │   ├── drift/
│   │   │   ├── contrato_api_DRIFT.md
│   │   │   └── openapi.yaml
│   │   └── playstation/
│   │       ├── contrato_api_playstation.md
│   │       ├── openapi.yaml
│   │       └── asyncapi.yaml
│   ├── aspectos.md
│   ├── escenarios.md
│   ├── ia.md
│   └── matriz.md
│
├── deployment/
│   └── vercel/
│       ├── api/
│       │   └── index.py
│       ├── requirements.txt
│       ├── pyproject.toml
│       └── .vercel/
│           └── project.json
│
├── scripts/
│   ├── start.py
│   └── k6_baseline.js
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── sonar-project.properties
├── correcciones.md
└── README.md
```

## Recreación del entorno

Para ejecutar DRIFT desde un equipo nuevo, siga los siguientes pasos.

### 1. Clonar el repositorio

Desde una terminal:

```bash
git clone https://github.com/ISCOUTB/AS_202620_Drift.git
cd AS_202620_Drift
```

### 2. Verificar los requisitos

El proyecto requiere:

- Python 3.12 o superior.
- Node.js 22 o superior.
- npm.
- Git.

Para comprobar las versiones instaladas:

```bash
python --version
node --version
npm --version
git --version
```

Para las pruebas de rendimiento se requiere adicionalmente [k6](https://grafana.com/docs/k6/latest/).

### 3. Instalar las dependencias del backend

Desde la raíz del proyecto:

```bash
python -m pip install -r backend/requirements.txt
```

Esto instala las dependencias necesarias para ejecutar la API y las pruebas del backend.

### 4. Instalar las dependencias del frontend

Desde la raíz del proyecto:

```bash
cd frontend
npm install
cd ..
```

Esto instala las dependencias definidas por el frontend.

### 5. Ejecutar DRIFT

Desde la raíz del proyecto:

```bash
python scripts/start.py
```

El script inicia automáticamente los dos componentes principales:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

La documentación interactiva de la API queda disponible en:

`http://localhost:8000/docs`

### 6. Verificar el funcionamiento

Con el proyecto en ejecución:

1. Abrir `http://localhost:3000` para acceder al frontend.
2. Verificar que la aplicación permita realizar una búsqueda de videojuegos.
3. Abrir `http://localhost:8000/docs` para comprobar que la API está disponible.
4. Si se desea validar automáticamente el backend, abrir otra terminal y ejecutar lo siguiente. Con el proyecto en marcha corren también las pruebas de contrato, que necesitan la API en el puerto 8000:

```bash
cd backend
python -m pytest tests -q
```

### 7. Detener el entorno

Para detener el frontend y el backend, regresar a la terminal donde se ejecutó:

```bash
python scripts/start.py
```

y presionar:

```text
Ctrl + C
```

## Pruebas y validación

### Pruebas del backend

Desde la carpeta `backend`:

```bash
python -m pytest tests -q
```

La suite incluye la búsqueda, la degradación de fuentes, la resiliencia de Steam (no responde, responde tarde, responde dos veces, 429, 5xx y respuestas inválidas), la compatibilidad de PC y la regla de dependencias de la arquitectura. Ninguna de estas pruebas sale a internet.

Las pruebas de contrato (`tests/test_contract.py`) comparan la API con [`docs/api/drift/openapi.yaml`](docs/api/drift/openapi.yaml) y necesitan la API encendida en `http://localhost:8000`. Sin ella fallan por conexión, no por un error del código. Para correr solo el resto:

```bash
python -m pytest tests -q --ignore=tests/test_contract.py
```

Última validación local (18 de octubre de 2026): **152 pruebas aprobadas**, más las 6 de contrato con la API encendida. Las de contrato tardan varios minutos porque consultan las fuentes reales.

### Experimento E6 (degradación de una fuente)

Reproduce la comparación antes/después con un upstream simulado (no usa servicios reales). Requiere k6. Desde la raíz del proyecto:

```bash
python scripts/e6_corrida.py backend despues-1
python scripts/resumen_e6.py
```

Procedimiento completo, versión "antes" y resultados medidos en [docs/evidencias/e6-degradacion-bajo-carga.md](docs/evidencias/e6-degradacion-bajo-carga.md).

### Compilación del frontend

Desde la carpeta `frontend`:

```bash
npm run build
```

Última validación local: compilación de producción aprobada.

### Pruebas de Rendimiento

Con k6 se ejecutó una prueba de carga sobre `GET /games/search?q=Minecraft` con 50 usuarios virtuales concurrentes.

Resultado posterior a la optimización:

| Métrica | Resultado |
|---|---:|
| Solicitudes exitosas | 50 de 50 |
| Solicitudes fallidas | 0 % |
| p95 | 1.24 s |
| Objetivo E1 | p95 ≤ 3 s |
| Estado | Cumple |

Para ejecutarla, inicia primero el proyecto con `python scripts/start.py`. En otra terminal ejecuta:

```bash
k6 run scripts/k6_baseline.js
```

En Windows, si k6 no está agregado al PATH:

```powershell
& "C:\Program Files\k6\k6.exe" run scripts/k6_baseline.js
```

La evidencia completa de este y demás escenarios se encuentra en [docs/evidencias/](docs/evidencias/).

## Integración continua y calidad

El workflow de GitHub Actions se encuentra en [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

El pipeline ejecuta:

1. Pruebas automatizadas del backend, incluidas las de contrato con la API levantada.
2. Smoke test entre frontend y API, con la compilación del frontend.
3. Análisis de SonarQube Cloud con el reporte de cobertura del backend.

El pipeline corre en cada push a `master` y en cada pull request hacia `master`. El análisis espera el veredicto del Quality Gate y el job falla si no pasa, así que un cambio con hallazgos no se integra. La configuración está en [`sonar-project.properties`](sonar-project.properties) y usa el secreto de GitHub `SONAR_TOKEN`.

## Despliegue

| Entorno | Qué publica | Dirección | Cómo se despliega |
|---|---|---|---|
| Servidor del laboratorio (Dokploy) | Frontend y backend | https://drift.iscoutb.dev | Docker Compose con [`deploy/compose.lab.yaml`](deploy/compose.lab.yaml), automático en cada push a `master` |
| Azure App Service | Backend | https://drift-utb-202620-g5fvchdcgpcthkeg.mexicocentral-01.azurewebsites.net | GitHub Actions en cada push a `master` |
| Vercel | Frontend | https://drift-frontend-as202620.vercel.app | Manual, desde la línea de comandos de Vercel |

Para probar en local la misma composición del laboratorio (requiere Docker):

```bash
docker compose -p drift --env-file deploy/.env -f deploy/compose.lab.yaml up -d --build
```

Detalle de la infraestructura en [arc42 §7](docs/arc42/arc42_7_vista_despliegue.md) y en [ADR-0005](docs/adr/0005-estrategia-despliegue.md).

## Configuración

Todas las variables son opcionales: sin ellas el sistema arranca con los valores por defecto. La plantilla está en [`deploy/.env.example`](deploy/.env.example); la copia con valores reales, `deploy/.env`, no se versiona.

| Variable | Por defecto | Para qué sirve |
|---|---|---|
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Orígenes que pueden llamar a la API |
| `NEXT_PUBLIC_DRIFT_API_URL` | `http://localhost:8000` | Dirección de la API que usa el frontend |
| `USD_TO_COP_RATE` | `3250` | Tasa de respaldo si la API de tasa de cambio no responde |
| `DRIFT_SOURCE_TIMEOUT_SECONDS` | `3` | Plazo de cada fuente secundaria en la búsqueda (ADR-0008) |
| `DRIFT_STEAM_TIMEOUT_SECONDS` | `3.0` | Timeout de cada llamada a Steam (ADR-0009) |
| `DRIFT_STEAM_MAX_ATTEMPTS` | `2` | Intentos totales con Steam: una llamada y un reintento |
| `DRIFT_STEAM_BACKOFF_BASE_SECONDS` | `0.25` | Espera base antes de reintentar |
| `DRIFT_STEAM_BACKOFF_MAX_SECONDS` | `2.0` | Espera máxima antes de reintentar |
| `DRIFT_STEAM_MAX_RETRY_AFTER_SECONDS` | `2.0` | Máximo que se respeta del `Retry-After` de Steam |
| `DRIFT_GPU_BENCHMARKS_URL` y `DRIFT_CPU_BENCHMARKS_URL` | vacías | Direcciones privadas de los puntajes de benchmarks. Sin ellas, la compatibilidad compara por niveles. Son secretas y no se escriben en el repositorio |

## Observabilidad

| Ruta | Qué muestra |
|---|---|
| `/health` | Estado de la API |
| `/metrics` | Latencia de búsqueda (promedio y p95 de las últimas 100) y búsquedas con una fuente no disponible, por fuente |

En el laboratorio van con el prefijo `/api`, por ejemplo https://drift.iscoutb.dev/api/metrics. Las métricas viven en memoria y se reinician con cada despliegue. Cada búsqueda deja además una línea de log en JSON.

## Documentación

| Documento | Contenido |
|---|---|
| [Aspectos de calidad](docs/aspectos.md) | Trazabilidad de E1 a E6, implementación y evidencias. |
| [Escenarios de calidad](docs/escenarios.md) | Escenarios medibles para rendimiento, mantenibilidad, usabilidad, compatibilidad y disponibilidad. |
| [Matriz arquitectónica](docs/matriz.md) | Comparación entre arquitectura en capas, hexagonal y monolito modular. |
| [C4: contexto](docs/c4/contexto.md) | Diagrama de contexto del sistema. |
| [C4: contenedores](docs/c4/contenedores.md) | Diagrama de contenedores de DRIFT. |
| [C4: componentes](docs/c4/componentes.md) | Diagrama de componentes de DRIFT. |
| [arc42](docs/arc42/) | Documentación de arquitectura basada en arc42. |
| [Uso de IA](docs/ia.md) | Registro y criterios de uso de herramientas de IA. |
| [Evidencias](docs/evidencias/) | Resultados de pruebas E1, E3, E4 y E6. |
| [Contextos delimitados y propiedad de los datos](docs/contextos_delimitados_propiedad_datos.md) | Lenguaje ubicuo, mapa de contextos delimitados y propiedad de datos. |
| [Correcciones](correcciones.md) | Trazabilidad entre el feedback y las correcciones realizadas. |

## Alcance actual

DRIFT busca juegos en Steam, compara su precio con el de otras tiendas de PC y con PlayStation Store, y abre la página de compra de cada tienda en una pestaña nueva. Una fuente nueva se integra con un adaptador que cumpla el puerto `GameRepository`, sin tocar el dominio.

La compatibilidad de PC usa los requisitos reales de cada juego en Steam y el equipo que el usuario guarda en su navegador. Compara memoria, procesador, tarjeta gráfica y espacio libre; la gráfica y el procesador se comparan por benchmark cuando hay datos y por niveles cuando no.

Limitaciones conocidas:

- **Precios de CheapShark:** son los de Estados Unidos, convertidos a pesos. Algunas tiendas cobran otro precio en Colombia y otras no venden el juego en Colombia. Los precios de Steam sí son los de Colombia, y los de PlayStation coinciden con su tienda, aunque esta cobra en dólares.
- **Persistencia:** el catálogo, las cachés y las métricas viven en memoria y se pierden al reiniciar (ADR-0008).
- **Pruebas del frontend:** no hay pruebas automatizadas del frontend.
- **Riesgos y deuda técnica:** el resto, con los modos de fallo de Steam, está en [arc42 §11](docs/arc42/arc42-11-riesgos-y-deuda-tecnica.md).
