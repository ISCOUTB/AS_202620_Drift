# 1. Introducción y objetivos

## 1.1 Propósito y alcance

**DRIFT** es una plataforma web orientada a jugadores que buscan tomar mejores decisiones al momento de comprar videojuegos. El sistema reúne información proveniente de diferentes plataformas digitales para facilitar la consulta y comparación de información relacionada con los videojuegos.

El propósito principal de DRIFT es centralizar información que se encuentra distribuida entre diferentes plataformas digitales, permitiendo al usuario comparar diferentes opciones antes de realizar una compra.

El sistema contempla principalmente las siguientes funcionalidades:

- Comparar precios de videojuegos entre diferentes plataformas digitales.
- Consultar descuentos e historial de ofertas.
- Consultar información de los videojuegos.
- Identificar la opción de compra más conveniente.
- Consultar las plataformas en las que se encuentra disponible un videojuego.
- Estimar el rendimiento y la compatibilidad de un videojuego en un dispositivo PC.
- Mantener disponible la información proveniente de otras fuentes cuando una fuente externa de precios presente un fallo.

Estas funcionalidades se encuentran representadas en los escenarios de calidad definidos para DRIFT.


## 1.2 Objetivos de calidad

El principal objetivo de calidad de DRIFT es la **mantenibilidad**.

Se busca que el sistema pueda incorporar nuevas plataformas, fuentes de información y funcionalidades sin generar cambios importantes en los demás componentes del sistema.

Además de la mantenibilidad, los escenarios de calidad definidos para DRIFT consideran los siguientes objetivos:

| Prioridad | Objetivo de calidad | Descripción |
|---|---|---|
| **1** | **Mantenibilidad** | Permitir incorporar nuevas plataformas, fuentes de información y funcionalidades sin generar cambios importantes en otros componentes. |
| **2** | **Rendimiento** | Proporcionar respuestas en tiempos adecuados para las consultas y operaciones principales del sistema. |
| **3** | **Disponibilidad** | Mantener la consulta de información cuando alguna fuente externa de precios presente un fallo. |
| **4** | **Usabilidad** | Permitir al usuario identificar y utilizar la opción más conveniente con una cantidad reducida de interacciones. |
| **5** | **Compatibilidad y rendimiento en PC** | Permitir estimar si un videojuego puede ejecutarse adecuadamente en el dispositivo del usuario. |

Estos objetivos se concretan mediante los escenarios de calidad medibles definidos para el sistema.


## 1.3 Interesados y sus objetivos

Los principales interesados de DRIFT son:

| Interesado | Objetivo / interés |
|---|---|
| **Jugador / usuario** | Comparar precios, descuentos y opciones disponibles para tomar una mejor decisión de compra y conocer el rendimiento esperado de un videojuego en su dispositivo. |
| **Administrador del sistema** | Supervisar y mantener el funcionamiento de DRIFT y sus fuentes de información. |
| **Equipo de desarrollo** | Mantener y evolucionar el sistema, incorporando nuevas plataformas, fuentes de información y funcionalidades sin afectar significativamente los componentes existentes. |
| **Plataformas o tiendas digitales** | Proporcionar información relacionada con precios, descuentos, disponibilidad y ofertas de los videojuegos. |
| **Proveedor de información de videojuegos** | Proporcionar información necesaria sobre los videojuegos, incluyendo aquella relacionada con sus características y requisitos de funcionamiento. |


## 1.4 Alcance entregado (actualización de noviembre de 2026)

Las secciones 1.1 a 1.3 describen la intención del proyecto en agosto. Esta tabla dice qué quedó implementado en `master` a la entrega final y qué no, para que el alcance recortado quede declarado y no se infiera de la intención inicial.

| Funcionalidad de 1.1 | Estado en `master` | Dónde | Decisión |
|---|---|---|---|
| Comparar precios entre plataformas | **Entregada:** Steam, más de 30 tiendas de PC (IsThereAnyDeal o CheapShark), PlayStation Store y tienda de Xbox, en pesos. Los precios de Colombia (Steam, PlayStation, Xbox) se distinguen de los de referencia de EE. UU. convertidos (ADR-0024) | [C4 nivel 3](../c4/componentes.md), `backend/app/infrastructure/external/` | ADR-0008, ADR-0016, ADR-0024 |
| Consultar descuentos e historial de ofertas | **Entregada** para PC: descuento por tienda e historial de 12 meses del mejor precio. **No hay historial de consolas.** | `GET /games/{id}/price-history` | ADR-0016 |
| Consultar información de los videojuegos | **Entregada:** portada con los más vendidos y página «Explorar» por género, con fichas de Steam | `/games/featured`, `/games/explore` | — |
| Identificar la opción de compra más conveniente | **Entregada:** recomendación de tienda y dispositivo | `POST /games/{id}/recommendation` | ADR-0019 |
| Consultar plataformas disponibles | **Entregada:** plataformas por tienda y filtro «Tengo:» | `domain/services/platforms.py` | — |
| Estimar compatibilidad en PC | **Entregada** para juegos con identificador de Steam, por puntaje de benchmark o por niveles | `POST /games/{id}/compatibility` | ADR-0018 |
| Mantener la información cuando una fuente falla | **Entregada:** plazo por fuente, aviso en `unavailable_sources` y copia de respaldo de hasta 72 h en `cached_sources` | `CombinedGameRepository`, `StaleFallbackGameRepository` | ADR-0008, ADR-0015 |
| *(nueva)* Cuentas, dispositivos, favoritos y alertas | **Entregada** con inicio de sesión de Google; alertas solo al entrar y solo tiendas de PC; **sin correo** | `/auth/*`, `/devices`, `/favorites` | ADR-0017, ADR-0020, ADR-0021 |

**Lo que no se hizo y queda declarado:** historial de precios de consolas; avisos por correo o en segundo plano; compatibilidad de juegos que no están en Steam; pruebas automatizadas del frontend; cumplir E1 en el despliegue (p95 de 9,05 s frente a 3 s, [arc42 §10](arc42_10_Requisitos_Calidad.md)); copias de seguridad de la base de datos; probar en el laboratorio el inicio de sesión real y el compose con PostgreSQL ([§11.11](arc42-11-riesgos-y-deuda-tecnica.md)).
