# 9. Decisiones de arquitectura

Esta sección funciona como el punto central de referencia para las decisiones de arquitectura de DRIFT. Se evita duplicar contenido ya explicado en otras secciones: la decisión de fondo (uso de Arquitectura Hexagonal) fue introducida en la **Sección 4 (Estrategia de solución)**; aquí se documenta en detalle como **ADR (Architecture Decision Record)**.

Cada decisión relevante se documenta como un ADR independiente en `docs/adr/`. Esta sección mantiene únicamente el índice y un resumen ordenado por importancia.

## 9.1 Índice de decisiones

| ID | Decisión | Estado | Impacto principal |
|---|---|---|---|
| [ADR-0001](adr/0001-arquitectura-base.md) | Selección de Arquitectura Hexagonal (Ports and Adapters) como arquitectura base, sobre stack Java | Superada parcialmente por ADR-0002 (stack tecnológico) | Estructura completa del sistema (Sección 5); soporta mantenibilidad y testabilidad (Sección 1.2) |
| [ADR-0002](adr/0002-arquitectura-base.md) | Cambio de stack tecnológico: Next.js (frontend) + FastAPI (backend), manteniendo Arquitectura Hexagonal | Aceptada | Reemplaza la tecnología concreta de implementación definida en ADR-0001, sin cambiar la decisión arquitectónica de fondo |

## 9.2 Resumen

**ADR-0001** estableció la Arquitectura Hexagonal como base de DRIFT, evaluando tres alternativas (Arquitectura en Capas, Monolito Modular, Hexagonal) mediante una matriz comparativa frente a mantenibilidad, testabilidad, escalabilidad, acoplamiento e integración con APIs externas. Se seleccionó Hexagonal por desacoplar la lógica de negocio de las fuentes externas. La estructura inicial propuesta usaba un stack en Java.

**ADR-0002** mantiene la misma decisión arquitectónica (Hexagonal) pero cambia la tecnología de implementación a Next.js + FastAPI, con una estructura de carpetas `frontend/` y `backend/` (`domain`, `application`, `infrastructure`) consistente con los bloques de construcción de la Sección 5.


## 9.3 Criterio de documentación

No toda decisión de diseño se documenta como ADR en esta sección central. Se registra aquí una decisión cuando cumple al menos uno de estos criterios:

- Afecta la estructura general del sistema (Sección 5) o su comportamiento en tiempo de ejecución (Sección 6).
- Tiene consecuencias difíciles o costosas de revertir.
- Involucra una alternativa descartada que otro integrante del equipo podría proponer de nuevo sin conocer esta discusión.

Decisiones de menor alcance, específicas de un bloque de construcción puntual, se documentan localmente dentro de la descripción de ese bloque (Sección 5.2) en lugar de duplicarse aquí.
