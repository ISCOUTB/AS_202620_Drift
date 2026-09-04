# Guía de código

Esta guía describe el corte vertical actual de DRIFT: buscar un videojuego y
mostrar el mejor precio disponible. El sistema está separado en un backend
FastAPI y un frontend Next.js.

## Flujo completo

```text
Persona usuaria
  -> interfaz React (DriftHome)
  -> caso de uso de frontend (searchGames)
  -> puerto GameSearchPort
  -> adaptador HTTP FastApiGameRepository
  -> GET /games/search?q=<consulta>
  -> adaptador de entrada FastAPI (main.py)
  -> caso de uso SearchGames
  -> puerto GameRepository
  -> adaptador SteamGameRepository
  -> API pública de Steam
```

Las flechas importantes siempre apuntan hacia el dominio: los detalles como
React, `fetch`, FastAPI, HTTPX y Steam se sitúan en los bordes del sistema.

## Por qué es arquitectura hexagonal

La arquitectura hexagonal organiza el software alrededor de reglas de negocio
y las comunica con el exterior por medio de puertos y adaptadores.

| Principio | Evidencia en DRIFT | Beneficio |
| --- | --- | --- |
| Dominio independiente | `Game` no importa FastAPI, React, HTTPX ni `fetch`. | El modelo se puede reutilizar y probar sin infraestructura. |
| Casos de uso independientes | `SearchGames` y `searchGames` reciben una abstracción de repositorio. | La regla de búsqueda no depende de Steam ni de una URL. |
| Puertos explícitos | `GameRepository` en Python y `GameSearchPort` en JavaScript definen `search(query)`. | El contrato se conserva aunque cambie el proveedor. |
| Adaptadores intercambiables | `SteamGameRepository` y `FastApiGameRepository` traducen los protocolos externos. | Se puede incorporar GOG, Epic o una API distinta sin modificar el caso de uso. |
| Composition root | `backend/app/main.py` elige el adaptador concreto al arrancar. | El acoplamiento se concentra en el borde de la aplicación. |

En JavaScript el puerto se valida en tiempo de ejecución mediante
`defineGameSearchPort`, pues el proyecto no utiliza TypeScript. En Python se
expresa como una clase abstracta (`ABC`).

## Backend

### Dominio

| Archivo | Responsabilidad |
| --- | --- |
| `backend/app/domain/model/game.py` | Entidad `Game`: identificador, nombre y precios por plataforma. |
| `backend/app/domain/ports/game_repository.py` | Puerto `GameRepository`; declara el contrato `search(query) -> List[Game]`. |

Esta capa no conoce endpoints web ni APIs de Steam. Es el centro de la
arquitectura.

### Aplicación

| Archivo | Responsabilidad |
| --- | --- |
| `backend/app/application/usecases/search_games.py` | Caso de uso `SearchGames`. Recibe un `GameRepository` y delega la búsqueda al puerto. |

El caso de uso representa la acción del sistema. Si mañana se agregan filtros,
orden por precio o reglas de recomendación, pertenecen a esta capa, no al
endpoint ni al repositorio de Steam.

### Infraestructura y adaptadores

| Archivo | Responsabilidad |
| --- | --- |
| `backend/app/infrastructure/external/steam/steam_game_repository.py` | Adaptador de salida. Consulta `storesearch` y `appdetails` de Steam con HTTPX, convierte la respuesta a `Game` y normaliza el precio a moneda decimal. |
| `backend/app/infrastructure/persistence/in_memory_game_repository.py` | Adaptador alternativo en memoria, útil para desarrollo o pruebas sin red. |
| `backend/app/main.py` | Adaptador de entrada HTTP y composition root. Configura CORS, crea `SteamGameRepository`, lo inyecta en `SearchGames` y expone `/` y `/games/search`. |

`main.py` contiene mapeo HTTP y serialización de la respuesta, pero no la regla
de búsqueda ni llamadas a Steam. Esa separación permite reutilizar el caso de
uso desde otra entrada, por ejemplo una tarea programada o una interfaz de
línea de comandos.

### Pruebas del backend

| Archivo | Qué comprueba |
| --- | --- |
| `backend/tests/test_health.py` | `test_health` verifica el endpoint de salud. `test_search_games_vertical_slice` simula las respuestas de Steam y prueba el recorrido completo HTTP -> caso de uso -> puerto -> adaptador. |

Steam se simula en el test para que la prueba sea repetible y no dependa de la
disponibilidad de un tercero.

## Frontend

### Dominio y aplicación

| Archivo | Responsabilidad |
| --- | --- |
| `frontend/domain/model/Game.js` | Crea la entidad que necesita el frontend y aplica valores por defecto para los precios. |
| `frontend/application/ports/GameSearchPort.js` | Valida que un adaptador implemente `search(query)`. |
| `frontend/application/usecases/searchGames.js` | Normaliza la consulta, evita búsquedas vacías y usa el puerto recibido. |

### Infraestructura

| Archivo | Responsabilidad |
| --- | --- |
| `frontend/infrastructure/http/FastApiGameRepository.js` | Adaptador HTTP. Lee `NEXT_PUBLIC_DRIFT_API_URL` —o `http://localhost:8000`—, llama a `/games/search` y transforma el JSON en entidades `Game`. |

La URL de FastAPI está aislada en este archivo. Para cambiar el origen de datos
no es necesario alterar la presentación ni el caso de uso.

### Interfaz

| Archivo | Responsabilidad |
| --- | --- |
| `frontend/app/layout.js` | Metadatos globales y carga de los estilos de la portada. |
| `frontend/app/page.js` | Ruta `/`; delega la pantalla al componente de interfaz. |
| `frontend/ui/components/DriftHome.js` | Componente cliente con estado de consulta, filtros, pestañas, carga, errores y tarjetas de sugerencias o resultados reales. |
| `frontend/ui/components/DriftHome.module.css` | Estilos encapsulados, diseño responsive y estética visual de la portada. |

Las sugerencias se presentan localmente para que la portada tenga contenido al
abrirla. Al buscar, los resultados sí vienen de la API y se muestra el mejor
precio calculado a partir de sus plataformas.

## Configuración y automatización

| Archivo | Responsabilidad |
| --- | --- |
| `backend/requirements.txt` | Dependencias locales del backend. |
| `frontend/package.json` | Comandos `dev`, `build` y `start` del frontend. |
| `frontend/package-lock.json` | Versiones reproducibles de npm. |
| `frontend/next.config.js` | Configuración de Next.js. |
| `.github/workflows/ci.yml` | CI de GitHub Actions: pruebas unitarias, levantamiento de la API, compilación y smoke test del frontend. |

## Límites actuales

- El adaptador de Steam realiza llamadas síncronas y aún no gestiona reintentos
  o timeouts explícitos.
- Los proveedores GOG, Epic, Xbox y PlayStation solo tienen documentación
  inicial; todavía no están conectados como adaptadores activos.
- El frontend contiene el cableado del adaptador HTTP dentro de su componente
  cliente. Una evolución natural es crear un composition root de frontend para
  inyectarlo desde un único punto, igual que ocurre en `backend/app/main.py`.
