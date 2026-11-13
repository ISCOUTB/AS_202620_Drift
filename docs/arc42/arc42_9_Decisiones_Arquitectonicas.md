# 9. Decisiones de arquitectura

Esta sección funciona como el punto central de referencia para las decisiones de arquitectura de DRIFT. Se evita duplicar contenido ya explicado en otras secciones: la decisión de fondo (uso de Arquitectura Hexagonal) fue introducida en la **Sección 4 (Estrategia de solución)**; aquí se documenta en detalle como **ADR (Architecture Decision Record)**.

Cada decisión relevante se documenta como un ADR independiente en `docs/adr/`. Esta sección mantiene únicamente el índice y un resumen ordenado por importancia.

## 9.1 Índice de decisiones

| ID | Decisión | Estado | Impacto principal |
|---|---|---|---|
| [ADR-0001](../adr/0001-adoptar-arquitectura-hexagonal.md) | Selección de Arquitectura Hexagonal (Ports and Adapters) como arquitectura base, sobre stack Java | Superada por ADR-0002 en cuanto al stack; se mantiene la decisión de Arquitectura Hexagonal | Estructura completa del sistema (Sección 5); soporta principalmente la mantenibilidad |
| [ADR-0002](../adr/0002-adoptar-nextjs-fastapi-arquitectura-hexagonal.md) | Cambio de stack tecnológico: Next.js (frontend) + FastAPI (backend), manteniendo Arquitectura Hexagonal | Aceptada | Reemplaza la tecnología concreta de implementación definida en ADR-0001, sin cambiar la decisión arquitectónica de fondo |
| [ADR-0004](../adr/0004-estrategia-de-integracion.md) | Estrategia híbrida de integración con MySQL y actualización asíncrona | Superseded por ADR-0008 | Persistencia y modelo de ejecución |
| [ADR-0008](../adr/0008-persistencia-ejecucion-y-degradacion-de-fuentes.md) | Catálogo en memoria, ejecución síncrona y degradación controlada de fuentes (plazo por fuente y aviso en `unavailable_sources`) | Aceptado; la persistencia en memoria la sustituye ADR-0014 | Secciones 5, 6, 7 y 11 y escenario E6; sustituye a ADR-0004 |
| [ADR-0009](../adr/0009-decision-extraccion-integracion-steam.md) | Mantener la integración con Steam dentro del backend; resiliencia del adaptador y circuit breaker diferido | Aceptado | Secciones 5, 7, 8 y 11; evidencia S11 |
| [ADR-0011](../adr/0011-autenticacion-operaciones-administrativas.md) | Token de servicio para la sincronización del catálogo y `/metrics`; registro de las operaciones administrativas | Aceptado | Secciones 8 y 11; modelo de amenazas A2, A5 y A10 |
| [ADR-0012](../adr/0012-limitacion-de-tasa-en-la-api.md) | Límite de tasa por cliente en búsqueda y compatibilidad; CORS acotado | Aceptado | Secciones 8 y 11; modelo de amenazas A3 y A9 |
| [ADR-0013](../adr/0013-plazo-total-en-la-busqueda-de-steam.md) | Plazo total por búsqueda en Steam; registra además las correcciones a ADR-0009 y ADR-0010 | Propuesto | Secciones 8 y 11; escenarios E5 y E6; modifica a ADR-0009 solo en el tiempo de una búsqueda |
| [ADR-0014](../adr/0014-postgresql-como-persistencia.md) | PostgreSQL como único servicio de datos; la base no puede tumbar la búsqueda | Propuesto | Secciones 5, 7 y 11; sustituye la persistencia en memoria de ADR-0008 |
| [ADR-0015](../adr/0015-copia-de-respaldo-de-las-fuentes.md) | Responder con la última copia de una fuente cuando falla (15 minutos fresca, 72 horas de respaldo) y avisarlo en `cached_sources` | Propuesto | Secciones 6, 8 y 11; escenarios E5 y E6; tensión disponibilidad contra actualización de precios |
| [ADR-0016](../adr/0016-isthereanydeal-e-historial-de-precios.md) | IsThereAnyDeal para las tiendas de PC y el historial de precios, con control de cuota; CheapShark queda como respaldo sin llave | Propuesto | Secciones 3, 5, 6 y 11; escenario E1 |
| [ADR-0017](../adr/0017-inicio-de-sesion-con-google-y-dispositivos.md) | Inicio de sesión con Google, sesión en cookie y registro de dispositivos en PostgreSQL | Propuesto | Secciones 3, 5, 8 y 11; modelo de amenazas A12 a A21; modifica el CORS de ADR-0012 |
| [ADR-0018](../adr/0018-puntajes-de-hardware-en-la-base-de-datos.md) | Puntajes de gráficas y procesadores en PostgreSQL, cargados desde la copia privada, que queda como respaldo | Propuesto | Secciones 5, 7 y 8; escenario E4 |
| [ADR-0019](../adr/0019-recomendacion-de-compra.md) | Recomendación de compra con una regla fija en el dominio: la opción más barata entre los dispositivos del usuario, salvo que otra dé mejor experiencia por hasta 10 % más | Propuesto | Secciones 5 y 6; modelo de amenazas A3 (la ruta entra en el límite de tasa) |
| [ADR-0020](../adr/0020-juegos-favoritos.md) | Juegos favoritos en PostgreSQL, con el precio al guardarlos como referencia; sin revisión en segundo plano | Propuesto | Secciones 5 y 8; privacidad, sección 8 |
| [ADR-0021](../adr/0021-alertas-de-precio.md) | Alertas de precio de los favoritos revisadas al entrar, solo tiendas de PC, con caché de una hora; sin correo ni procesos en segundo plano | Propuesto | Secciones 5, 6 y 8; modelo de amenazas A3 (límite de tasa); modifica ADR-0020 |

## 9.2 Resumen

**ADR-0001** estableció la Arquitectura Hexagonal como base de DRIFT, evaluando tres alternativas (Arquitectura en Capas, Monolito Modular, Hexagonal) mediante una matriz comparativa frente a mantenibilidad, testabilidad, escalabilidad, acoplamiento e integración con APIs externas. Se seleccionó Hexagonal por desacoplar la lógica de negocio de las fuentes externas. La estructura inicial propuesta usaba un stack en Java.

**ADR-0002** mantiene la misma decisión arquitectónica (Hexagonal) pero cambia la tecnología de implementación a Next.js + FastAPI, con una estructura de carpetas `frontend/` y `backend/` (`domain`, `application`, `infrastructure`) consistente con los bloques de construcción de la Sección 5.


## 9.3 Criterio de documentación

No toda decisión de diseño se documenta como ADR en esta sección central. Se registra aquí una decisión cuando cumple al menos uno de estos criterios:

- Afecta la estructura general del sistema (Sección 5) o su comportamiento en tiempo de ejecución (Sección 6).
- Tiene consecuencias difíciles o costosas de revertir.
- Involucra una alternativa descartada que otro integrante del equipo podría proponer de nuevo sin conocer esta discusión.

Decisiones de menor alcance, específicas de un bloque de construcción puntual, se documentan localmente dentro de la descripción de ese bloque (Sección 5.2) en lugar de duplicarse aquí.
