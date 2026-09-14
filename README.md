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
│   │   ├── application/usecases/
│   │   │   ├── search_games.py
│   │   │   └── estimate_compatibility.py
│   │   ├── domain/
│   │   │   ├── model/
│   │   │   │   ├── game.py
│   │   │   │   └── game_requirements.py
│   │   │   └── ports/
│   │   │       ├── game_repository.py
│   │   │       └── game_requirements_repository.py
│   │   ├── infrastructure/
│   │   │   ├── external/steam/steam_game_repository.py
│   │   │   └── persistence/
│   │   │       ├── in_memory_game_repository.py
│   │   │       ├── in_memory_game_requirements_repository.py
│   │   │       └── resilient_game_repository.py
│   │   └── main.py
│   └── tests/
│       ├── test_search_games.py
│       └── test_compatibility.py
├── frontend/
│   ├── application/
│   ├── domain/
│   ├── infrastructure/
│   └── ui/components/DriftHome.js
├── docs/
│   ├── adr/
│   ├── arc42/
│   ├── c4/
│   ├── evidencias/
│   ├── aspectos.md
│   ├── escenarios.md
│   ├── ia.md
│   └── matriz.md
├── scripts/
│   ├── start.py
│   └── k6_baseline.js
├── sonar-project.properties
├── correcciones.md
└── README.md
```

## Requisitos previos

- Python 3.12 o superior.
- Node.js 22 o superior y npm.
- Opcional para la prueba de rendimiento: [k6](https://grafana.com/docs/k6/latest/set-up/install-k6/).

## Instalación

Desde la raíz del repositorio, instala las dependencias del backend:

```bash
python -m pip install -r backend/requirements.txt
```

Después instala las dependencias del frontend:

```bash
cd frontend
npm install
cd ..
```

Estas instalaciones solo son necesarias al configurar el entorno o cuando cambian las dependencias.

## Comando Unico de Ejecuccion

Desde la raíz del proyecto:

```bash
python scripts/start.py
```

El script inicia:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Documentación interactiva de la API: `http://localhost:8000/docs`

Para detener ambos procesos, presiona `Ctrl + C` en la terminal donde se ejecutó el script.

## Funcionalidades implementadas

### Búsqueda de videojuegos

El usuario puede buscar videojuegos desde el frontend. La solicitud recorre el frontend, la API REST, el caso de uso, el puerto del dominio y el adaptador de Steam.

```text
Frontend → API REST → SearchGames → GameRepository → SteamGameRepository → Steam
```

La búsqueda implementa caché temporal, consulta paralela de detalles y un límite de resultados para mejorar el rendimiento.

### Tolerancia a fallos de Steam

Si Steam no está disponible, `ResilientGameRepository` utiliza un repositorio local de respaldo. La respuesta informa la fuente no disponible mediante el campo `unavailable_sources`.

### Estimación de compatibilidad de PC

El usuario puede seleccionar un juego, indicar memoria RAM y nivel de GPU, y consultar una estimación de compatibilidad.

La estimación entrega uno de estos resultados:

- `Compatible`
- `Compatible con limitaciones`
- `No compatible`
- `Requisitos no disponibles`

El catálogo de requisitos actual es controlado para fines académicos y puede reemplazarse posteriormente por una fuente externa.

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

### Rendimiento — escenario E1

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

La evidencia completa está en [docs/evidencias/e1-linea-base.md](docs/evidencias/e1-linea-base.md).

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
| [arc42](docs/arc42/) | Documentación de arquitectura basada en arc42. |
| [Uso de IA](docs/ia.md) | Registro y criterios de uso de herramientas de IA. |
| [Evidencias](docs/evidencias/) | Resultados de pruebas E1, E3 y E4. |
| [Conceptos transversales — arc42 sección 8](docs/arc42/08-conceptos-transversales.md) | Lenguaje ubicuo, mapa de contextos delimitados y propiedad de datos. |
| [Evidencia S6](docs/semana-06-contextos-y-propiedad-de-datos.md) | Mapa de contextos, dueño único de datos, auditoría de violaciones y matriz de cumplimiento. |
| [Correcciones](correcciones.md) | Trazabilidad entre el feedback y las correcciones realizadas. |

## Alcance actual

La fuente externa real implementada es Steam. La arquitectura permite integrar futuras plataformas mediante adaptadores que cumplan el contrato `GameRepository`.

La compatibilidad de PC usa requisitos controlados para fines académicos. La integración con datos técnicos externos queda como evolución futura.
