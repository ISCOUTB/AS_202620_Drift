# ADR-0002: Selección de Arquitectura Base

## Contexto

DRIFT es una plataforma orientada a la comparación de precios de videojuegos, integrando información proveniente de múltiples fuentes externas. El sistema deberá evolucionar para incorporar nuevas plataformas, servicios de análisis, motores de recomendación y posibles fuentes de datos adicionales.

Dado que la **mantenibilidad** ha sido identificada como el principal atributo de calidad, se requiere una arquitectura que facilite la incorporación de nuevas funcionalidades e integraciones sin afectar significativamente el núcleo de la aplicación.

---

## Alternativas Consideradas

### Opción 1: Arquitectura en Capas

#### Descripción

Organiza la aplicación en capas tradicionales (presentación, negocio y persistencia), donde cada capa depende de la inmediatamente inferior.

#### Ventajas

- Fácil de comprender e implementar.
- Amplia documentación y adopción.
- Baja complejidad inicial.

#### Desventajas

- Alto acoplamiento entre capas.
- La lógica de negocio puede terminar dependiendo de detalles de infraestructura.
- Menor flexibilidad para reemplazar tecnologías externas.

---

### Opción 2: Monolito Modular

#### Descripción

Organiza el sistema en módulos funcionales independientes dentro de una única aplicación desplegable.

#### Ventajas

- Buena separación de responsabilidades.
- Despliegue sencillo.
- Facilita la evolución por dominios funcionales.

#### Desventajas

- Puede generar dependencias entre módulos con el tiempo.
- No separa completamente la lógica de negocio de la infraestructura.
- Requiere disciplina arquitectónica constante.

---

### Opción 3: Arquitectura Hexagonal (Ports and Adapters)

#### Descripción

Separa el dominio de la infraestructura mediante puertos y adaptadores, permitiendo que la lógica de negocio permanezca independiente de tecnologías externas.

#### Ventajas

- Alta mantenibilidad.
- Excelente testabilidad.
- Bajo acoplamiento.
- Facilita la incorporación de nuevas integraciones externas.
- Permite reemplazar componentes tecnológicos sin afectar el dominio.

#### Desventajas

- Mayor complejidad inicial.
- Más clases y paquetes desde etapas tempranas.
- Curva de aprendizaje superior a otras alternativas.

---

## Matriz Comparativa

| Criterio | Arquitectura en Capas | Monolito Modular | Hexagonal |
|-----------|-----------|-----------|-----------|
| Mantenibilidad | Media | Alta | Muy Alta |
| Testabilidad | Media | Alta | Muy Alta |
| Facilidad de implementación | Alta | Alta | Media |
| Escalabilidad | Media | Alta | Alta |
| Integración con APIs externas | Media | Alta | Muy Alta |
| Acoplamiento | Alto | Medio | Bajo |
| Adaptación a cambios futuros | Media | Alta | Muy Alta |

---

## Decisión

Se selecciona la **Arquitectura Hexagonal (Ports and Adapters)** como arquitectura base para DRIFT.

La decisión se fundamenta en la necesidad de mantener desacoplada la lógica de negocio respecto de las múltiples fuentes de información externas y facilitar la evolución futura del sistema sin generar dependencias innecesarias entre componentes.

---

## Consecuencias

### Positivas

- Las integraciones con nuevas plataformas pueden agregarse mediante adaptadores independientes.
- La lógica de negocio permanece aislada de detalles tecnológicos.
- Mayor facilidad para realizar pruebas unitarias y de integración.
- Menor impacto ante cambios en APIs externas.
- Incremento de la mantenibilidad general del sistema.

### Negativas

- Incremento en la complejidad inicial del proyecto.
- Mayor cantidad de paquetes y clases desde las primeras iteraciones.
- Requiere conocimiento previo de patrones de diseño y principios de inversión de dependencias.

---

**En este segundo ADR, se cambia la estructura inicial de Java y Spring-boot por una estructura actualizada utilizando Next.js para frontend y FAST-Api en Backend.**
## Estructura Inicial Derivada del ADR

```text
DRIFT
├── frontend
│   ├── app
│   │   ├── layout.js
│   │   └── page.js
│   ├── public
│   ├── next.config.js
│   ├── package.json
│   └── package-lock.json
│
└── backend
    ├── app
    │   ├── domain
    │   │   ├── model
    │   │   └── ports
    │   │
    │   ├── application
    │   │   └── usecases
    │   │
    │   ├── infrastructure
    │   │   ├── api
    │   │   ├── xbox
    │   │   ├── playstation
    │   │   ├── persistence
    │   │   └── steam
    │   │
    │   └── main.py
    │
    └── tests
```

Esta estructura representa únicamente el esqueleto inicial del proyecto y no contiene lógica de negocio implementada.
## Trazabilidad de la decisión

La decisión de utilizar Arquitectura Hexagonal se relaciona directamente con los escenarios de calidad definidos para DRIFT y con la estructura implementada actualmente.

| Elemento                | Relación con la decisión                                                                                                                |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **E1 — Rendimiento**    | La separación entre caso de uso y adaptadores permite optimizar las integraciones externas sin modificar el dominio.                    |
| **E2 — Mantenibilidad** | Es el escenario directamente relacionado con la decisión. Los adaptadores aíslan las fuentes externas del núcleo de la aplicación.      |
| **E3 — Usabilidad**     | El frontend se mantiene separado del núcleo del backend, permitiendo evolucionar la interfaz sin modificar la lógica de dominio.        |
| **E4 — Compatibilidad** | La lógica de compatibilidad puede implementarse como un caso de uso independiente utilizando los puertos definidos por la arquitectura. |
| **E5 — Disponibilidad** | La separación mediante adaptadores permite manejar independientemente los errores de las fuentes externas.                              |

### Relación con C4

La decisión se representa en el C4 de contenedores mediante la separación entre:

* Frontend Next.js.
* API/backend FastAPI.
* Casos de uso.
* Dominio.
* Adaptadores de fuentes externas.

[C4 de contexto](../c4/contexto.md)

[C4 de contenedores](../c4/contenedores.md)

### Relación con el código

La implementación actual refleja la decisión mediante:

* `backend/app/domain/model/game.py`
* `backend/app/domain/ports/game_repository.py`
* `backend/app/application/usecases/search_games.py`
* `backend/app/infrastructure/external/steam/steam_game_repository.py`
* `backend/app/infrastructure/persistence/in_memory_game_repository.py`

El puerto `GameRepository` define el contrato que utilizan las fuentes de datos, mientras que `SearchGames` depende de dicho contrato y no de una implementación concreta.

### Relación con pruebas

La decisión se valida parcialmente mediante la prueba `test_search_games_vertical_slice`, que comprueba el flujo desde el endpoint hasta el adaptador de Steam utilizando una respuesta externa simulada.

La prueba específica de sustitución de un adaptador externo queda como trabajo pendiente para validar completamente el escenario E2.

### Relación con CI

El workflow `.github/workflows/ci.yml` ejecuta las pruebas del backend y realiza una comprobación de integración entre el backend y el frontend.

