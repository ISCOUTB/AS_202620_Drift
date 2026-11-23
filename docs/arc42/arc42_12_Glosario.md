# 12. Glosario

Este glosario recoge los términos específicos de DRIFT y de su documentación de arquitectura — no términos genéricos de uso común (REST, API, HTTP, etc.) que no requieren definición local. Actualizado el 22 de noviembre de 2026 con los términos de cuentas, persistencia y precios.

| Término | Definición |
|---|---|
| **Adaptador de entrada** | Adaptador que recibe solicitudes desde fuera del sistema (por ejemplo, del jugador) y las traduce en invocaciones sobre un puerto de entrada del núcleo de dominio. |
| **Adaptador de salida** | Adaptador que traduce un puerto de salida del núcleo de dominio en una llamada concreta hacia un servicio externo (tienda digital, proveedor de información, persistencia). |
| **Adaptador** | Componente que traduce el puerto de un caso de uso del núcleo de dominio a una tecnología o servicio externo concreto (o viceversa), permitiendo que el núcleo permanezca independiente de esa tecnología. En DRIFT existen adaptadores de entrada (Adaptador Web/API) y de salida (Tiendas Digitales, Proveedor de Información, Persistencia). Ver Sección 5.1. |
| **ADR (Architecture Decision Record)** | Documento que registra una decisión de arquitectura importante, su contexto, las alternativas consideradas y sus consecuencias. En DRIFT se documentan en `docs/adr/`, siguiendo el formato de Michael Nygard (ver Sección 9). |
| **Alerta de precio** | Aviso que DRIFT muestra al entrar cuando un favorito llegó a su precio objetivo o bajó al menos 5 % frente al precio guardado. Ver ADR-0021. |
| **Arquitectura Hexagonal (Ports and Adapters)** | Patrón arquitectónico que separa el núcleo de dominio de las tecnologías y servicios externos mediante puertos (interfaces) y adaptadores (implementaciones concretas de esas interfaces). Modelo arquitectónico base de DRIFT, seleccionado en ADR-0001 y confirmado en ADR-0002 (Sección 9). |
| **Caja blanca (whitebox)** | Descripción de un bloque de construcción que muestra su estructura interna (los sub-bloques que lo componen). Ver Sección 5. |
| **Caja negra (blackbox)** | Descripción de un bloque de construcción que muestra únicamente su responsabilidad e interfaces, sin revelar su estructura interna. Ver Sección 5. |
| **Compatibilidad (en PC)** | Objetivo de calidad de DRIFT relacionado con estimar si un videojuego puede ejecutarse adecuadamente en el dispositivo del usuario, comparando las especificaciones registradas del dispositivo contra los requisitos del videojuego. Ver Secciones 1.2 y 6.3. |
| **Copia de respaldo de una fuente** | Última respuesta guardada de una fuente externa, usada cuando esa fuente falla y avisada en `cached_sources`. Ver ADR-0015. |
| **Degradación controlada** | Responder con las fuentes disponibles cuando una falla o tarda, avisando cuál faltó en `unavailable_sources`. Ver ADR-0008. |
| **Dispositivo** | PC o consola que una persona registra en su cuenta para filtrar tiendas, estimar compatibilidad y recibir recomendaciones. Ver ADR-0017. |
| **DRIFT** | Nombre del sistema documentado: plataforma web que centraliza información de precios, descuentos, disponibilidad y compatibilidad de videojuegos provenientes de múltiples tiendas digitales, para ayudar al jugador a tomar mejores decisiones de compra. |
| **Escenario de calidad** | Descripción concreta y medible de un objetivo de calidad, estructurada en fuente del estímulo, estímulo, artefacto, entorno, respuesta y medida de respuesta. Documentados en `docs/escenarios.md` y ampliados en la Sección 10.2. |
| **Favorito** | Juego guardado en una cuenta junto con su precio y tienda en ese momento. Ver ADR-0020. |
| **Fuente externa (de información/precios)** | Sistema fuera del alcance de DRIFT del cual el sistema obtiene datos: tiendas digitales (precios, descuentos, disponibilidad) o el proveedor de información de videojuegos (características, requisitos). Ver Sección 3. |
| **Huella de sesión** | SHA-256 del identificador de sesión. Es lo único de la sesión que se guarda en PostgreSQL. Ver ADR-0017. |
| **Huella del código** | Hash SHA-256 de los archivos Python de la API, publicado en `/health`. `scripts/verificar_despliegue.py` lo traduce al commit desplegado. |
| **Interesado (stakeholder)** | Persona, rol o sistema con interés o influencia sobre DRIFT: jugador, administrador del sistema, equipo de desarrollo, tiendas digitales, proveedor de información de videojuegos. Ver Secciones 1.3 y 3.1. |
| **Mantenibilidad** | Objetivo de calidad prioritario de DRIFT: capacidad de incorporar nuevas plataformas, fuentes de información o funcionalidades sin generar cambios importantes en los demás componentes del sistema. Ver Sección 1.2. |
| **Núcleo de dominio** | Bloque de construcción central de DRIFT que contiene la lógica de negocio (búsqueda, comparación, recomendación, estimación de compatibilidad) sin depender de tecnologías ni fuentes externas concretas. Ver Sección 5.1 y 5.2.1. |
| **p95 (percentil 95)** | Medida estadística usada en los escenarios de rendimiento de DRIFT: el 95 % de las solicitudes deben cumplir el tiempo de respuesta indicado (por ejemplo, "≤ 3 s en p95" significa que como máximo el 5 % de las solicitudes puede tardar más de 3 segundos). Ver Sección 2.7 y 10.2. |
| **Precio de Colombia** | Precio obtenido directamente para Colombia: Steam, PlayStation, Xbox y Microsoft Store. PlayStation cobra en dólares. Ver ADR-0024. |
| **Precio de referencia** | Precio de Estados Unidos convertido a pesos, entregado por IsThereAnyDeal o CheapShark. Puede diferir del de Colombia y la tienda puede no vender el juego en Colombia. Ver ADR-0024. |
| **Puerto** | Interfaz definida por el núcleo de dominio que especifica una capacidad requerida (puerto de salida, por ejemplo "consultar precios") o expuesta (puerto de entrada, por ejemplo "solicitar comparación"), sin definir cómo se implementa. Ver Sección 5.1. |
| **Recomendación de compra** | Opción más conveniente según precio, compatibilidad y dispositivos, con una regla fija en el dominio. Ver ADR-0019 y ADR-0024. |
| **Restricción** | Condición impuesta desde afuera de la arquitectura (organizacional, técnica o legal/de terceros) que limita la libertad de diseño del equipo, a diferencia de un objetivo de calidad. Ver Sección 2. |
| **Sub-adaptador** | Adaptador más específico que vive dentro de un adaptador general, cuando este agrupa varias implementaciones similares — por ejemplo, cada tienda digital (Steam, PlayStation Store, Xbox Store) tiene su propio sub-adaptador dentro del Adaptador de Tiendas Digitales. Ver Sección 5.2.2. |
| **Tienda digital** | Plataforma externa de venta de videojuegos de la cual DRIFT obtiene precios, descuentos y disponibilidad (Steam, Epic Games Store, PlayStation Store, Xbox Store). Ver Sección 3.1. |
