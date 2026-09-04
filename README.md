# DRIFT — Comparador Inteligente de Videojuegos

Proyecto del curso **Arquitectura de Software (AS_202620)** — Universidad Tecnológica de Bolívar.

## ¿Qué es DRIFT?

**DRIFT** es una plataforma web orientada a jugadores que buscan tomar mejores decisiones al comprar videojuegos. El sistema reúne información de diferentes plataformas digitales para comparar precios, descuentos e historial de ofertas, teniendo en cuenta además las plataformas disponibles para cada usuario y el rendimiento esperado de sus dispositivos.

La definición detallada de la problemática se encuentra en [`docs/ficha_problema.md`](docs/ficha_problema.md).

## Aspecto de calidad declarado

Para DRIFT se prioriza la **mantenibilidad**, buscando que el sistema pueda incorporar nuevas plataformas, fuentes de información y funcionalidades sin generar cambios importantes en los demás componentes.

La justificación y definición del aspecto seleccionado se encuentra en [`docs/aspectos.md`](docs/aspectos.md).

---

## Equipo de desarrollo

- Mauricio Fernández Espinosa
- Jerry Buelvas Mejía
- Luis Pérez Diaz
- Joshua Reyes Leones

---

## Organización del proyecto

DRIFT separa el frontend, el backend y la documentación arquitectónica.

El backend está desarrollado con **FastAPI** y sigue los principios de la **Arquitectura Hexagonal (Ports and Adapters)**, separando el dominio, los casos de uso y la infraestructura. Actualmente cuenta con una integración real con **Steam** mediante un adaptador externo.

El frontend está desarrollado con **Next.js** y consume los servicios expuestos por el backend mediante una API REST.

```text
DRIFT/  
├── .github/  
│   └── workflows/  
│       └── ci.yml  
│  
├── backend/  
│   ├── app/  
│   │   ├── domain/  
│   │   │   ├── model/  
│   │   │   │   └── game.py  
│   │   │   └── ports/  
│   │   │       └── game_repository.py  
│   │   │  
│   │   ├── application/  
│   │   │   └── usecases/  
│   │   │       └── search_games.py  
│   │   │  
│   │   ├── infrastructure/  
│   │   │   ├── external/  
│   │   │   │   └── steam/  
│   │   │   │       └── steam_game_repository.py  
│   │   │   └── persistence/  
│   │   │       └── in_memory_game_repository.py  
│   │   │  
│   │   └── main.py  
│   │  
│   └── tests/  
│       └── test_health.py  
│  
├── frontend/  
│   ├── app/  
│   │   ├── layout.js  
│   │   └── page.js  
│   ├── components/  
│   ├── repositories/  
│   ├── services/  
│   ├── public/  
│   ├── next.config.js  
│   ├── package.json  
│   └── package-lock.json  
│  
├── docs/  
│   ├── adr/  
│   ├── arc42/  
│   ├── c4/  
│   ├── arbol_utilidad.md  
│   ├── aspectos.md  
│   ├── escenarios.md  
│   ├── ficha_problema.md  
│   ├── ia.md  
│   ├── interesados.md  
│   └── matriz.md  
│  
├── .gitignore  
└── README.md
```

---

## Documentación


| Archivo                                                               | Contenido                                                                    |
|-----------------------------------------------------------------------|------------------------------------------------------------------------------|
| [`adr/0002-arquitectura-base.md`](docs/adr/0002-arquitectura-base.md) | Decisión y evolución de la arquitectura base de DRIFT                      |
| [`c4/contexto.md`](docs/c4/contexto.md)                               | Diagrama de contexto C4 de DRIFT                                             |
| [`c4/contenedores.md`](docs/c4/contenedores.md)                       | Diagrama de contenedores C4 (nivel 2) de DRIFT                               |
| [`ficha_problema.md`](docs/ficha_problema.md)                         | Definición y análisis de la problemática                                  |
| [`aspectos.md`](docs/aspectos.md)                                     | Aspecto de calidad seleccionado y escenarios asociados                       |
| [`arbol_utilidad.md`](docs/arbol_utilidad.md)                         | Árbol de utilidad de los atributos de calidad y relación con E1-E5         |
| [`interesados.md`](docs/interesados.md)                               | Identificación y análisis de los interesados de DRIFT                      |
| [`escenarios.md`](docs/escenarios.md)                                 | Escenarios de calidad medibles de DRIFT                                      |
| [`matriz.md`](docs/matriz.md)                                         | Matriz comparativa de estilos arquitectónicos frente a los escenarios E1-E5 |
| [`ia.md`](docs/ia.md)                                                 | Registro y criterios de uso de herramientas de IA                            |


---

## Documentación de arquitectura — arc42

La documentación de arquitectura de DRIFT se desarrolla siguiendo el modelo **arc42**. En ella se describen el propósito del sistema, sus objetivos de calidad, las restricciones arquitectónicas, el contexto y alcance, la estrategia de solución, la estructura interna, el comportamiento en tiempo de ejecución, las decisiones arquitectónicas y los requisitos de calidad detallados.


| Sección                                 | Contenido                                                                | Documento                                                                                 |
|------------------------------------------|--------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **1. Introducción y objetivos**         | Propósito, alcance, objetivos de calidad e interesados.                 | [`arc42_1_introduccion_objetivos.md`](docs/arc42/arc42_1_introduccion_objetivos.md)       |
| **2. Restricciones**                     | Restricciones que condicionan la arquitectura y su justificación.       | [`arc42_2_restricciones.md`](docs/arc42/arc42_2_restricciones.md)                         |
| **3. Contexto y alcance**                | Contexto del sistema, actores, sistemas externos, límites e interfaces. | [`arc42_3_contexto_alcance.md`](docs/arc42/arc42_3_contexto_alcance.md)                   |
| **4. Estrategia de solución**           | Principales decisiones y estrategias arquitectónicas de DRIFT.          | [`arc42_4_soluciones_arquitectonica.md`](docs/arc42/arc42_4_soluciones_arquitectonica.md) |
| **5. Vista de bloques de construcción** | Descomposición estática del sistema, puertos y adaptadores.            | [`arc42_5_bloques_construccion.md`](docs/arc42/arc42_5_bloques_construccion.md)           |
| **6. Vista de tiempo de ejecución**     | Escenarios de interacción entre bloques de construcción en runtime.    | [`arc42_6_vista_runtime.md`](docs/arc42/arc42_6_vista_runtime.md)                         |
| **9. Decisiones de arquitectura**        | Índice de ADR y resumen de las decisiones más importantes.             | [`arc42_9_decisiones_arquitectura.md`](docs/arc42/arc42_9_decisiones_arquitectura.md)     |
| **10. Requisitos de calidad**            | Árbol/tabla de calidad y escenarios de calidad detallados y medibles.   | [`arc42_10_requisitos_calidad.md`](docs/arc42/arc42_10_requisitos_calidad.md)             |
| **12. Glosario**                         | Términos técnicos y de dominio usados en la documentación.            | [`arc42_12_glosario.md`](docs/arc42/arc42_12_glosario.md)                                 |


---

## Contexto y análisis arquitectónico

El proyecto incluye diferentes artefactos que permiten representar y analizar la arquitectura de DRIFT.

El **árbol de utilidad** organiza los atributos de calidad de DRIFT y los escenarios asociados, mostrando cuáles son prioritarios para el proyecto.

- [`docs/arbol_utilidad.md`](docs/arbol_utilidad.md)

El **diagrama C4 de contexto** representa a DRIFT, sus usuarios y los sistemas externos con los que interactúa, mostrando los límites y relaciones principales del sistema.

El **diagrama C4 de contenedores** descompone DRIFT en sus principales unidades arquitectónicas, mostrando las responsabilidades y relaciones entre los componentes internos del sistema.

- [`docs/c4/contexto.md`](docs/c4/contexto.md)
- [`docs/c4/contenedores.md`](docs/c4/contenedores.md)

---

## Interesados y escenarios de calidad

El proyecto incluye el análisis de los interesados de DRIFT y sus principales preocupaciones relacionadas con la calidad del sistema.

El **mapa de interesados** identifica los actores relevantes para la arquitectura y sus prioridades.

Los **escenarios medibles** traducen estas preocupaciones en situaciones verificables, especificando fuente, estímulo, artefacto, entorno, respuesta y una medida cuantificable.

La documentación correspondiente se encuentra en:

- [`docs/interesados.md`](docs/interesados.md)
- [`docs/escenarios.md`](docs/escenarios.md)

Los escenarios actuales contemplan principalmente:

- Comparación de precios.
- Consulta de información de videojuegos.
- Identificación de la opción más conveniente.
- Estimación de rendimiento y compatibilidad en PC.
- Disponibilidad ante fallos de una fuente externa de precios.

---

## Comparación de estilos arquitectónicos

Para definir la estrategia arquitectónica de DRIFT se realizó una comparación entre diferentes estilos arquitectónicos, considerando los escenarios de calidad y las necesidades del sistema.

La **matriz comparativa** evalúa la arquitectura en capas, la arquitectura hexagonal y el monolito modular. A partir de esta comparación se selecciona la **arquitectura hexagonal** como la alternativa más adecuada para DRIFT.

- [`docs/matriz.md`](docs/matriz.md)

---

## Inteligencia Artificial

La IA forma parte de la propuesta de DRIFT como apoyo para la generación de recomendaciones personalizadas y el análisis de información relacionada con precios, plataformas y rendimiento. El uso de estas herramientas será registrado y justificado durante el desarrollo en [`docs/ia.md`](docs/ia.md).

---

# Arquitectura

El proyecto adopta una **Arquitectura Hexagonal (Ports and Adapters)**.

La arquitectura busca mantener aislado el núcleo de la aplicación respecto a tecnologías externas como HTTP, FastAPI y las plataformas de videojuegos.

La decisión arquitectónica se encuentra documentada en:

- [`docs/adr/0002-arquitectura-base.md`](docs/adr/0002-arquitectura-base.md)

---

# Ejecución

Para ejecutar DRIFT localmente se deben levantar el backend y el frontend por separado.

## Backend

Desde una terminal:

```bash
cd backend
```

Instalar las dependencias necesarias:

```bash
python -m pip install fastapi uvicorn httpx pytest
```

Iniciar el servidor:

```bash
uvicorn app.main:app --reload
```

El backend estará disponible en:

```text
http://localhost:8000
```

La documentación interactiva de FastAPI estará disponible en:

```text
http://localhost:8000/docs
```

## Pruebas

Desde otra terminal:

```bash
cd backend  
python -m pytest tests
```

Las pruebas incluyen el estado de la API y el corte vertical de búsqueda. La integración con Steam se simula durante las pruebas para evitar depender de la disponibilidad de un servicio externo.

## Frontend

Desde otra terminal:

```bash
cd frontend  
npm install  
npm run dev
```

El frontend estará disponible en:

```text
http://localhost:3000
```

El frontend consume la API del backend mediante el endpoint:

```text
GET http://localhost:8000/games/search?q=<videojuego>
```

---

# Corte vertical implementado

## Búsqueda de videojuegos y consulta de precios en Steam

DRIFT cuenta actualmente con un **corte vertical funcional** que permite realizar una búsqueda de videojuegos desde la interfaz web, enviar la consulta al backend, procesarla mediante el caso de uso correspondiente y obtener información real desde Steam.

Este corte atraviesa las principales capas de la aplicación y demuestra la integración entre frontend, backend, dominio y una fuente externa real.

### Flujo de ejecución

```text
Usuario  
   ↓  
Frontend Next.js  
   ↓  
searchGames  
   ↓  
GameSearchPort  
   ↓  
FastApiGameRepository  
   ↓  
GET /games/search?q=<videojuego>  
   ↓  
FastAPI  
   ↓  
SearchGames  
   ↓  
GameRepository  
   ↓  
SteamGameRepository  
   ↓  
API de Steam  
   ↓  
Game  
   ↓  
Respuesta al frontend
```

### Componentes involucrados


| Componente              | Responsabilidad                                                               |
|-------------------------|-------------------------------------------------------------------------------|
| `DriftHome`             | Recibe la búsqueda del usuario y presenta los resultados.                    |
| `searchGames`           | Gestiona la búsqueda desde el frontend.                                      |
| `GameSearchPort`        | Define el contrato de búsqueda en el frontend.                               |
| `FastApiGameRepository` | Realiza la comunicación HTTP con el backend.                                 |
| `main.py`               | Expone el endpoint `/games/search` y conecta el adaptador con el caso de uso. |
| `SearchGames`           | Ejecuta la operación de búsqueda mediante el puerto del dominio.            |
| `GameRepository`        | Define el contrato que deben cumplir las fuentes de videojuegos.              |
| `SteamGameRepository`   | Consulta Steam y transforma su respuesta en entidades `Game`.                 |
| `Game`                  | Representa el videojuego y sus precios.                                       |



### Escenario de calidad demostrado

El corte vertical se relaciona principalmente con el **Escenario E2 — Mantenibilidad**, definido en [`docs/escenarios.md`](docs/escenarios.md).

El escenario plantea que, ante un cambio en la API de una fuente externa, el sistema debe permitir adaptar dicha integración sin realizar modificaciones importantes en el núcleo de la aplicación ni en los demás adaptadores.

La implementación actual evidencia esta estrategia porque `SteamGameRepository` concentra la lógica específica de comunicación y transformación de los datos provenientes de Steam, mientras que `SearchGames`, `GameRepository` y `Game` permanecen desacoplados de la plataforma externa.

Por lo tanto, el corte vertical no solo demuestra que una búsqueda funciona de extremo a extremo, sino también que la arquitectura facilita el aislamiento de cambios en fuentes externas, apoyando el atributo de calidad prioritario de **mantenibilidad**.

### Prueba del corte vertical

La prueba `test_search_games_vertical_slice` verifica el flujo principal mediante una solicitud HTTP al endpoint:

```text
TestClient  
   ↓  
GET /games/search  
   ↓  
SearchGames  
   ↓  
GameRepository  
   ↓  
SteamGameRepository  
   ↓  
Respuesta simulada de Steam  
   ↓  
JSON de DRIFT
```

Durante la prueba, la respuesta de Steam se simula para que el resultado sea determinista y no dependa de una conexión externa.

Esto permite validar el comportamiento del corte vertical tanto localmente como dentro del proceso de integración continua (CI).

---

# Integración continua

DRIFT cuenta con un workflow de **GitHub Actions** ubicado en:

- [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

El workflow ejecuta automáticamente las validaciones del proyecto cuando se realizan cambios sobre la rama `master` o mediante Pull Requests.

Actualmente contempla:

- Ejecución de pruebas del backend con `pytest`.
- Verificación del endpoint principal de FastAPI.
- Construcción del frontend con Next.js.
- Smoke test de la API desde el flujo de integración.

Esto permite detectar errores de integración antes de considerar un cambio como estable.

---

# Estado actual del corte vertical

El corte vertical implementado cubre actualmente:

```text
Frontend → API REST → Caso de uso → Puerto → Adaptador Steam → Fuente externa
```

La integración con Steam constituye la primera fuente externa real del sistema. Otras plataformas pueden incorporarse posteriormente mediante nuevos adaptadores que implementen el contrato definido por `GameRepository`, manteniendo el núcleo de DRIFT desacoplado de dichas plataformas.

 
