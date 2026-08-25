# Drift — Comparador Inteligente de Videojuegos

Proyecto del curso **Arquitectura de Software** (AS_202620) — Universidad Tecnológica de Bolívar.

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

## Organización del proyecto

La estructura actual de DRIFT separa el frontend, el backend y la documentación arquitectónica. El backend sigue los principios de la Arquitectura Hexagonal (Ports and Adapters), mientras que el frontend utiliza Next.js.

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
│   │   │   └── ports/
│   │   │
│   │   ├── application/
│   │   │   └── usecases/
│   │   │
│   │   ├── infrastructure/
│   │   │   ├── api/
│   │   │   ├── playstation/
│   │   │   ├── steam/
│   │   │   ├── xbox/
│   │   │   └── persistence/
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
│   ├── public/
│   ├── next.config.js
│   ├── package.json
│   └── package-lock.json
│
├── docs/
│   ├── adr/
│   │   └── 0001-arquitectura-base.md
|   |   └── 0002-arquitectura-base.md
│   ├── arc42/
│   │   ├── arc42_1_introduccion_objetivos.md
│   │   ├── arc42_2_restricciones.md
│   │   ├── arc42_3_contexto_alcance.md
│   │   └── arc42_4_soluciones_arquitectonica.md
│   ├── c4/
│   │   └── contexto.md
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

### Documentación


| Archivo             | Contenido                                               |
|---------------------|---------------------------------------------------------|
| [`adr/0001-arquitectura-base.md`](docs/adr/0001-arquitectura-base.md) | Decisión arquitectónica base de DRIFT            |
| [`arc42/arc42_1_introduccion_objetivos.md`](docs/arc42/arc42_1_introduccion_objetivos.md) | Introducción, objetivos e interesados de DRIFT |
| `arc42/arc42_2_restricciones.md`  | Restricciones del proyecto DRIFT |
| `arc42/arc42_3_contexto_alcance.md` | Contexto y alcance del sistema |
| `arc42/arc42_4_soluciones_arquitectonica.md` | Estrategia de solución arquitectónica |
| `c4/contexto.md`       | Diagrama de contexto C4 de DRIFT  |
| `ficha_problema.md`    | Definición y análisis de la problemática |
| `aspectos.md`     | Aspecto de calidad seleccionado para la arquitectura|
| `ia.md`             | Registro y criterios de uso de herramientas de IA |
| `arbol_utilidad.md`       | Árbol de utilidad de atributos de calidad |
| `interesados.md`    |Identificación y análisis de los interesados de DRIFT|
| `escenarios.md`     | Escenarios de calidad medibles de DRIFT|
| `ia.md`             | Registro y criterios de uso de herramientas de IA |
| `matriz.md`             | Matriz comparativa de estilos arquitectónicos (capas, hexagonal, monolito modular) frente a los escenarios de calidad de DRIFT |

---

### Documentación de arquitectura — arc42

La documentación de arquitectura de DRIFT se desarrolla siguiendo el modelo **arc42**. En ella se describen el propósito del sistema, sus objetivos de calidad, las restricciones arquitectónicas y el contexto y alcance del sistema.

| Sección | Contenido | Documento |
|---|---|---|
| **1. Introducción y objetivos** | Propósito, alcance, objetivos de calidad e interesados. | [`arc42_1_introduccion_objetivos.md`](docs/arc42/arc42_1_introduccion_objetivos.md) |
| **2. Restricciones** | Restricciones que condicionan la arquitectura y su justificación. | [`arc42_2_restricciones.md`](docs/arc42/arc42_2_restricciones.md) |
| **3. Contexto y alcance** | Contexto del sistema, actores, sistemas externos, límites e interfaces. | [`arc42_3_contexto_alcance.md`](docs/arc42/arc42_3_contexto_alcance.md) |
| **4. Soluciones Arquitectonica** | Principales decisiones arquitectónicas de DRIFT. | [`arc42_4_soluciones_arquitectonica.md`](docs/arc42/arc42_4_soluciones_arquitectonica.md) |

---

## Contexto y análisis arquitectónico

El proyecto incluye diferentes artefactos que permiten representar y analizar la arquitectura de DRIFT. 

El **árbol de utilidad** organiza los atributos de calidad de DRIFT y los escenarios asociados, mostrando cuáles son prioritarios para el proyecto. 
- [`docs/arbol_utilidad.md`](docs/arbol_utilidad.md)

El **diagrama C4 de contexto** representa a DRIFT, sus usuarios y los sistemas externos con los que interactúa, mostrando los límites y relaciones principales del sistema.

- [`docs/c4_contexto.md`](docs/c4_contexto.md)

---

## Interesados y escenarios de calidad

El proyecto incluye el análisis de los interesados de DRIFT y sus principales preocupaciones relacionadas con la calidad del sistema.

El **mapa de interesados** identifica los actores relevantes para la arquitectura y sus prioridades.

Los **escenarios medibles** traducen estas preocupaciones en situaciones verificables, especificando fuente, estímulo, artefacto, entorno, respuesta y una medida cuantificable.

La documentación correspondiente se encuentra en:

- [`docs/interesados.md`](docs/interesados.md)
- [`docs/Escenarios.md`](docs/Escenarios.md)

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

## Inteligencia Artificial

La IA forma parte de la propuesta de DRIFT como apoyo para la generación de recomendaciones personalizadas y el análisis de información relacionada con precios, plataformas y rendimiento.El uso de estas herramientas será registrado y justificado durante el desarrollo en [`docs/ia.md`](docs/ia.md).


# DRIFT

## Arquitectura

El proyecto adopta una Arquitectura Hexagonal (Ports and Adapters).

Ver ADR:

- [`docs/adr/0002-arquitectura-base.md`](docs/adr/0002-arquitectura-base.md)

---
# Ejecución

## Backend

```bash
cd backend
uvicorn app.main:app --reload
(El backend estará disponible en http://localhost:8000)
```

## Pruebas

```bash
cd backend
pytest
```

## Frontend
```bash
cd frontend
npm install
npm run dev
(El frontend estará disponible en http://localhost:3000)
```
