# Evidencia S6 — Contextos delimitados y propiedad de datos

| Campo | Valor |
|---|---|
| Semana | 6 |
| Corte | Segundo corte |
| Tipo | Grupal |
| Rama de referencia | `master` |
| Estado evaluado | Último commit de `master` anterior o igual al cierre de la actividad |
| Artefactos relacionados | `docs/arc42/08-conceptos-transversales.md`, `docs/aspectos.md`, `docs/c4/`, `docs/adr/` |

## 1. Alcance de la revisión

La revisión se realizó sobre el código actual de DRIFT. El proyecto no cuenta con base de datos, migraciones ni tablas SQL; por esta razón, se revisaron las entidades de dominio, catálogos en memoria y estados temporales existentes en el código.

Archivos revisados:

- `backend/app/domain/model/game.py`
- `backend/app/domain/model/game_requirements.py`
- `backend/app/domain/ports/game_repository.py`
- `backend/app/domain/ports/game_requirements_repository.py`
- `backend/app/application/usecases/search_games.py`
- `backend/app/application/usecases/estimate_compatibility.py`
- `backend/app/infrastructure/external/steam/steam_game_repository.py`
- `backend/app/infrastructure/persistence/in_memory_game_repository.py`
- `backend/app/infrastructure/persistence/in_memory_game_requirements_repository.py`
- `backend/app/infrastructure/persistence/resilient_game_repository.py`
- `backend/app/main.py`

## 2. Mapa de contextos

## 2. Mapa de contextos

El mapa completo y el lenguaje ubicuo se encuentran en [arc42 sección 8](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/arc42/08-conceptos-transversales.md).

| Contexto | Responsabilidad | Tipo |
|---|---|---|
| Búsqueda y comparación | Ejecutar búsquedas y entregar videojuegos con precios y fuentes disponibles. | Núcleo del dominio propio. |
| Integración de fuentes externas | Obtener y transformar información de Steam y del catálogo local de respaldo. | Contexto de soporte y capa anticorrupción. |
| Compatibilidad de PC | Estimar compatibilidad a partir de requisitos del juego, RAM y nivel de GPU. | Contexto de soporte. |
| Experiencia de usuario | Buscar videojuegos, visualizar resultados y consultar compatibilidad. | Cliente de los contextos del dominio. |

## 3. Tabla módulo → datos con dueño único

| Dato o entidad | Ubicación real | Contexto dueño único | Módulos que lo consultan o transforman |
|---|---|---|---|
| `Game` | `backend/app/domain/model/game.py` | Búsqueda y comparación | `SearchGames`, `SteamGameRepository`, `InMemoryGameRepository`, `ResilientGameRepository` y frontend. |
| Precio de Steam | `backend/app/infrastructure/external/steam/steam_game_repository.py` | Integración de fuentes externas | `SteamGameRepository` lo consulta y lo transforma a `Game`. |
| Catálogo local de respaldo | `backend/app/infrastructure/persistence/in_memory_game_repository.py` | Integración de fuentes externas | `ResilientGameRepository` lo consulta cuando Steam no está disponible. |
| Caché temporal de Steam | `backend/app/infrastructure/external/steam/steam_game_repository.py` | Integración de fuentes externas | Solo `SteamGameRepository`. |
| `GameRequirements` | `backend/app/domain/model/game_requirements.py` | Compatibilidad de PC | `EstimateCompatibility` e `InMemoryGameRequirementsRepository`. |
| Catálogo de requisitos de PC | `backend/app/infrastructure/persistence/in_memory_game_requirements_repository.py` | Compatibilidad de PC | `EstimateCompatibility`. |
| Resultado de compatibilidad | `backend/app/application/usecases/estimate_compatibility.py` | Compatibilidad de PC | `main.py` y frontend lo consumen. |

## 4. Auditoría de propiedad de datos

Se revisaron los módulos que crean, transforman o modifican entidades y datos del dominio.

### V1 — Metadato de disponibilidad modificado desde infraestructura

**Dato afectado:** `Game.unavailable_sources`.

**Ubicación verificada:**

- Definición del campo: `backend/app/domain/model/game.py:10`
- Inicialización del campo: `backend/app/domain/model/game.py:15`
- Modificación desde infraestructura: `backend/app/infrastructure/persistence/resilient_game_repository.py:25`
- Exposición en la respuesta HTTP: `backend/app/main.py:62`

**Procedimiento de revisión:**

Se ejecutó el siguiente comando desde la raíz del repositorio:

```powershell
Get-ChildItem backend/app -Recurse -Filter *.py | Select-String -Pattern 'unavailable_sources|Game\('
```

**Descripción:**

`ResilientGameRepository` modifica el campo `unavailable_sources` de objetos `Game` obtenidos desde el catálogo de respaldo.

**No conformidad:**

La información sobre fuentes no disponibles forma parte del resultado de búsqueda. Esta decisión debe ser propiedad del contexto Búsqueda y comparación, no de un adaptador de infraestructura.

**Plan de corrección:**

1. Crear un resultado de búsqueda explícito, por ejemplo `SearchResult`.
2. Hacer que `ResilientGameRepository` devuelva videojuegos de respaldo o una señal de falla sin modificar `Game.unavailable_sources`.
3. Hacer que `SearchGames` construya el resultado final e informe las fuentes no disponibles.
4. Ajustar la prueba de fallback para validar el nuevo resultado.

**Estado:** Pendiente para el siguiente incremento.

### Hallazgos sin violación

- `SteamGameRepository` e `InMemoryGameRepository` construyen objetos `Game` como adaptadores que transforman datos externos o de respaldo. No existen escrituras persistentes de `Game` desde varios módulos.
- `GameRequirements` solo es administrado por el contexto Compatibilidad de PC.
- No se encontraron tablas SQL, migraciones ni operaciones de persistencia compartida.
- La caché de Steam pertenece exclusivamente a `SteamGameRepository` y es estado técnico temporal.

## 5. Relación con los escenarios de calidad

| Escenario | Contextos relacionados |
|---|---|
| E1 — Rendimiento | Búsqueda y comparación; Integración de fuentes externas. |
| E2 — Mantenibilidad | Integración de fuentes externas; Búsqueda y comparación. |
| E3 — Usabilidad | Experiencia de usuario; Búsqueda y comparación. |
| E4 — Compatibilidad | Compatibilidad de PC; Experiencia de usuario. |
| E5 — Disponibilidad | Integración de fuentes externas; Búsqueda y comparación. |

Todos los escenarios de `docs/aspectos.md` pueden relacionarse con al menos un contexto del mapa.

