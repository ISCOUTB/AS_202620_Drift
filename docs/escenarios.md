# Escenarios medibles de DRIFT

## Escenario 1
**Atributo:** Eficiencia de desempeño

- **Fuente:** Usuario de DRIFT.
- **Estímulo:** El usuario realiza una búsqueda de un videojuego para comparar su precio.
- **Artefacto:** Módulo de búsqueda y comparación de precios de DRIFT.
- **Entorno:** Sistema funcionando normalmente con hasta 50 usuarios concurrentes.
- **Respuesta:** DRIFT consulta y muestra los precios disponibles del videojuego en las diferentes tiendas digitales.
- **Medida verificable:** El resultado de la búsqueda deberá mostrarse en **≤ 3 segundos en el p95**.

**Escenario completo:**

>
> Cuando un usuario realice una búsqueda de un videojuego en DRIFT, bajo una carga de hasta 50 usuarios concurrentes, el sistema deberá mostrar los precios disponibles en las diferentes tiendas digitales en un tiempo **≤ 3 segundos en el p95**.
>

---

## Escenario 2

**Atributo:** Mantenibilidad

* **Fuente:** Equipo de desarrollo de DRIFT.
* **Estímulo:** Se requiere modificar o reemplazar la integración con una fuente externa de precios debido a un cambio en su API.
* **Artefacto:** Adaptador de integración de la fuente externa de precios.
* **Entorno:** Sistema funcionando normalmente y utilizando la fuente externa modificada.
* **Respuesta:** DRIFT deberá permitir modificar el adaptador correspondiente sin realizar cambios significativos en el núcleo de la aplicación ni en las integraciones con las demás fuentes.
* **Medida verificable:** El cambio deberá limitarse al adaptador de la fuente afectada, sin modificar el dominio ni los adaptadores de las demás fuentes.

**Escenario completo:**

> Cuando una fuente externa de precios modifique su API, el equipo de desarrollo deberá poder adaptar la integración correspondiente sin realizar cambios en el núcleo de la aplicación ni en los adaptadores de las demás fuentes.


---

## Escenario 3
**Atributo:** Usabilidad / eficiencia

- **Fuente:** Usuario de DRIFT.
- **Estímulo:** El usuario busca un videojuego y desea determinar cuál de las opciones disponibles es más conveniente.
- **Artefacto:** Módulo de comparación y recomendación de DRIFT.
- **Entorno:** Usuario con acceso a los resultados de las diferentes tiendas digitales.
- **Respuesta:** DRIFT presenta las opciones ordenadas o diferenciadas según precio, disponibilidad de plataforma y demás criterios considerados por el sistema.
- **Medida verificable:** El usuario deberá poder identificar la opción recomendada en **máximo 3 interacciones** después de realizar la búsqueda.

**Escenario completo:**

>
> Cuando un usuario busque un videojuego con el objetivo de determinar la opción más conveniente, DRIFT deberá presentar una recomendación basada en precio, plataforma disponible y criterios definidos por el sistema, permitiendo identificar dicha opción en **máximo 3 interacciones**.
>

---

## Escenario 4
**Atributo:** Rendimiento / compatibilidad

- **Fuente:** Usuario con un dispositivo PC registrado en DRIFT.
- **Estímulo:** El usuario consulta un videojuego para conocer si su equipo puede ejecutarlo.
- **Artefacto:** Módulo de compatibilidad y estimación de rendimiento.
- **Entorno:** El usuario tiene previamente registrado su dispositivo y sus especificaciones.
- **Respuesta:** DRIFT compara las especificaciones del dispositivo con los requisitos del videojuego e informa el nivel de compatibilidad o rendimiento estimado.
- **Medida verificable:** El resultado deberá mostrarse en **≤ 5 segundos en el p95** después de realizar la consulta.

**Escenario completo:**

>
> Cuando un usuario con un dispositivo PC registrado consulte un videojuego, DRIFT deberá comparar las especificaciones del equipo con los requisitos del videojuego y mostrar la estimación de compatibilidad o rendimiento en un tiempo **≤ 5 segundos en el p95**.
>

---

## Escenario 5
**Atributo:** Disponibilidad

- **Fuente:** Servicio externo de una tienda digital.
- **Estímulo:** Una de las fuentes externas de precios deja de responder durante una consulta.
- **Artefacto:** Módulo de consulta e integración de fuentes de precios de DRIFT.
- **Entorno:** DRIFT se encuentra funcionando normalmente y el usuario está realizando una comparación de precios.
- **Respuesta:** DRIFT deberá continuar mostrando la información obtenida de las demás fuentes disponibles e indicar que una fuente no pudo ser consultada.
- **Medida verificable:** La consulta deberá continuar disponible para el usuario y mostrar las demás fuentes en **≤ 5 segundos**, sin que el fallo de una fuente provoque la interrupción completa del servicio.

**Escenario completo:**

>
> Cuando una fuente externa de precios no responda durante una consulta, DRIFT deberá continuar mostrando la información disponible de las demás tiendas e informar al usuario de la fuente no disponible, manteniendo la consulta operativa en un tiempo **≤ 5 segundos**.
>

---


**Los escenarios de calidad se consideran como parte de la evaluación de la arquitectura seleccionada para DRIFT. La decisión arquitectónica base se encuentra documentada en:**

- **[`ADR-0002: Selección de Arquitectura Base`](adr/0002-arquitectura-base.md)**
