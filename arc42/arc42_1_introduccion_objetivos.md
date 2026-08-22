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
