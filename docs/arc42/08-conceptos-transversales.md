# 8. Conceptos transversales

## 8.1 Propósito

Esta sección define el lenguaje ubicuo y los contextos delimitados de DRIFT. Su objetivo es que el equipo utilice los mismos términos al hablar del dominio y que cada dato tenga una responsabilidad clara dentro de la arquitectura.

## 8.2 Lenguaje ubicuo

| Término | Definición |
|---|---|
| Videojuego | Producto consultable mediante identificador, nombre y precios disponibles. |
| Búsqueda | Consulta realizada por un usuario a partir del nombre de un videojuego. |
| Precio | Valor disponible de un videojuego en una fuente específica. |
| Fuente externa | Plataforma o servicio desde el cual DRIFT obtiene información de videojuegos. |
| Fuente no disponible | Plataforma externa que no respondió correctamente durante una búsqueda. |
| Catálogo de respaldo | Datos locales usados cuando una fuente externa no está disponible. |
| Compatibilidad | Estimación de si un PC puede ejecutar un videojuego. |
| Requisito mínimo | Capacidad mínima de RAM y GPU requerida para un videojuego. |
| Requisito recomendado | Capacidad de RAM y GPU recomendada para una mejor experiencia. |
| Nivel de GPU | Escala controlada usada para comparar la GPU del usuario con los requisitos de un juego. |

## 8.3 Mapa de contextos delimitados

```mermaid
flowchart LR
    Usuario[Usuario]

    UI[Experiencia de usuario]
    Busqueda[Búsqueda y comparación]
    Compatibilidad[Compatibilidad de PC]
    Integracion[Integración de fuentes externas]
    Steam[Steam]
    Respaldo[Catálogo local de respaldo]

    Usuario --> UI
    UI -->|Cliente| Busqueda
    UI -->|Cliente| Compatibilidad

    Busqueda -->|Cliente| Integracion
    Integracion -->|Capa anticorrupción| Steam
    Integracion -->|Proveedor de respaldo| Respaldo

    Busqueda -.->|Identificador de videojuego| Compatibilidad