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
- La integración externa actual se realiza mediante un adaptador para **Steam**.
- Los casos de uso dependen de puertos del dominio, no de servicios externos concretos.
- Ante una falla de Steam, el sistema utiliza un catálogo local de respaldo e informa la fuente no disponible.

Las decisiones principales están documentadas en:

- [ADR-0001: Adoptar arquitectura hexagonal](docs/adr/0001-adoptar-arquitectura-hexagonal.md)
- [ADR-0002: Adoptar Next.js y FastAPI sobre arquitectura hexagonal](docs/adr/0002-adoptar-nextjs-fastapi-arquitectura-hexagonal.md)

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
4. Si se desea validar automáticamente el backend, abrir otra terminal y ejecutar:

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

La suite actual incluye pruebas del corte vertical de búsqueda, tolerancia a fallos de Steam y estimación de compatibilidad.

Última validación local: **8 pruebas aprobadas**.

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

1. Pruebas automatizadas del backend.
2. Smoke test entre frontend y API.
3. Compilación del frontend con Next.js.
4. Análisis de calidad con SonarQube Cloud.

SonarQube Cloud está configurado mediante `sonar-project.properties` y el secreto de GitHub `SONAR_TOKEN`. El análisis se ejecutará en GitHub Actions cuando el equipo realice un push autorizado.

## Documentación

| Documento | Contenido |
|---|---|
| [Aspectos de calidad](docs/aspectos.md) | Trazabilidad de E1 a E5, implementación y evidencias. |
| [Escenarios de calidad](docs/escenarios.md) | Escenarios medibles para rendimiento, mantenibilidad, usabilidad, compatibilidad y disponibilidad. |
| [Matriz arquitectónica](docs/matriz.md) | Comparación entre arquitectura en capas, hexagonal y monolito modular. |
| [C4: contexto](docs/c4/contexto.md) | Diagrama de contexto del sistema. |
| [C4: contenedores](docs/c4/contenedores.md) | Diagrama de contenedores de DRIFT. |
| [C4: componentes](docs/c4/componentes.md) | Diagrama de componentes de DRIFT. |
| [arc42](docs/arc42/) | Documentación de arquitectura basada en arc42. |
| [Uso de IA](docs/ia.md) | Registro y criterios de uso de herramientas de IA. |
| [Evidencias](docs/evidencias/) | Resultados de pruebas E1, E3 y E4. |
| [Contextos delimitados y propiedad de los datos](docs/contextos_delimitados_propiedad_datos.md) | Lenguaje ubicuo, mapa de contextos delimitados y propiedad de datos. |
| [Correcciones](correcciones.md) | Trazabilidad entre el feedback y las correcciones realizadas. |

## Alcance actual

La fuente externa real implementada es Steam. La arquitectura permite integrar futuras plataformas mediante adaptadores que cumplan el contrato `GameRepository`.

La compatibilidad de PC usa requisitos controlados para fines académicos. La integración con datos técnicos externos queda como evolución futura.
