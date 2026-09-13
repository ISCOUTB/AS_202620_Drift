# Uso de Inteligencia Artificial — DRIFT

## 1. Propósito

Este documento registra el uso de herramientas de inteligencia artificial durante el desarrollo de DRIFT.

La IA se utilizó como apoyo para comprender conceptos, proponer alternativas, revisar documentación, orientar implementaciones y detectar inconsistencias. Las decisiones arquitectónicas, los cambios aplicados y la validación final fueron responsabilidad del equipo.

## 2. Principios de uso

El equipo aplicó los siguientes criterios:

- No se copiaron respuestas de IA sin revisión.
- Cada cambio técnico se revisó en el código y se validó mediante pruebas, compilación o ejecución local cuando correspondía.
- No se compartieron contraseñas, tokens, datos personales ni información sensible con la herramienta.
- Las alternativas sugeridas por IA podían ser rechazadas si no se ajustaban al alcance, al código existente o a los objetivos de calidad.
- La IA no reemplazó el criterio del equipo en decisiones arquitectónicas.

## 3. Herramienta utilizada

La herramienta de IA utilizada como apoyo durante esta etapa fue:

- **ChatGPT (OpenAI):** apoyo conceptual, revisión de documentación, orientación de código, pruebas y configuración.

No se registra evidencia de uso de Claude, Gemini u otras herramientas de IA en los cambios documentados en este repositorio.

## 4. Áreas en las que se utilizó IA

ChatGPT se utilizó como apoyo en:

- Definición y ajuste de la propuesta inicial de DRIFT.
- Elaboración de documentación arc42, C4, ADR, escenarios y matriz arquitectónica.
- Organización de frontend y backend mediante arquitectura hexagonal.
- Configuración de GitHub Actions y SonarQube Cloud.
- Implementación y validación del corte vertical de búsqueda.
- Manejo de fallos de una fuente externa.
- Estimación de compatibilidad de PC.
- Diseño y ejecución de pruebas automatizadas.
- Medición de rendimiento con k6.
- Corrección de enlaces, trazabilidad y documentación del repositorio.

## 5. Registro de uso

### Registro 1 — Selección de tecnología para el frontend

**Fecha:** 2026-08-24
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Qué conviene más para el frontend de DRIFT: Next.js o React con Vite? Explica las diferencias y los criterios de decisión.

**Uso:**

Se utilizó como apoyo para comparar alternativas de frontend y documentar la selección de Next.js.

**Decisión del equipo:**

Se adoptó Next.js por su estructura, facilidad de integración con el backend y adecuación al proyecto.

**Alternativa descartada:**

React con Vite fue descartado porque el equipo consideró que Next.js se ajustaba mejor a la estructura prevista para DRIFT.

---

### Registro 2 — Documentación inicial y ficha del problema

**Fecha:** 2026-08-24
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo podemos organizar la propuesta inicial, la ficha del problema y las funcionalidades de una plataforma para comparar videojuegos?

**Uso:**

Se utilizó para organizar ideas iniciales, definir la problemática y explorar funcionalidades posibles.

**Validación:**

El equipo revisó y ajustó la propuesta para mantenerla dentro del alcance académico del proyecto.

---

### Registro 3 — Escenarios, árbol de utilidad y matriz

**Fecha:** 2026-08-24
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo relacionamos correctamente los escenarios E1–E5 con el árbol de utilidad, los atributos de calidad y la matriz de estilos arquitectónicos?

**Uso:**

Se utilizó para revisar la trazabilidad entre escenarios de calidad, atributos, árbol de utilidad y alternativas arquitectónicas.

**Alternativa descartada:**

Se descartaron relaciones entre escenarios y atributos que no correspondían directamente con su propósito. El equipo conservó únicamente las relaciones coherentes con la documentación.

---

### Registro 4—Configuración inicial del pipeline

**Fecha:** 2026-08-24
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo podemos configurar GitHub Actions para ejecutar automáticamente las pruebas del backend y dejar evidencia de CI?

**Uso:**

Se utilizó para orientar la creación de un workflow de GitHub Actions con pruebas automatizadas.

**Validación:**

La configuración fue revisada por el equipo y las pruebas se ejecutaron localmente antes de incluirse en el pipeline.

---

### Registro 5 — C4 de contenedores

**Fecha:** 2026-08-27
**Herramienta:** ChatGPT

**Consulta utilizada:**

> Ya tenemos el C4 de contexto de DRIFT. ¿Cómo se relaciona con el nivel de contenedores y qué elementos reales del proyecto debemos representar?

**Uso:**

Se utilizó para aclarar el alcance del diagrama C4 de contenedores y su relación con el diagrama de contexto.

**Alternativa descartada:**

Se descartó incluir componentes que pertenecían a otros niveles de C4 o que no existían en el código.

---

### Registro 6 — Renovación visual de la portada

**Fecha:** 2026-09-03
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo podemos organizar una interfaz para explorar videojuegos con buscador, categorías, sugerencias y tarjetas de resultados?

**Uso:**

Se utilizó como apoyo para estructurar la portada de DRIFT y los elementos de interfaz relacionados con la búsqueda.

**Validación:**

El equipo revisó visualmente la interfaz mediante ejecución local del frontend.

---

### Registro 7 — Separación del frontend por capas

**Fecha:** 2026-09-03
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo separar el frontend en dominio, aplicación, infraestructura e interfaz para evitar que la vista dependa directamente de HTTP?

**Uso:**

Se utilizó para orientar la separación entre el modelo de dominio, caso de uso, puerto y adaptador HTTP del frontend.

**Alternativa descartada:**

Se descartó realizar solicitudes HTTP directamente desde los componentes de interfaz, porque aumentaba el acoplamiento con la infraestructura.

---

### Registro 8 — Conexión del buscador con FastAPI

**Fecha:** 2026-09-03
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo conectamos el buscador de Next.js con el endpoint de FastAPI y configuramos la URL de la API para distintos entornos?

**Uso:**

Se utilizó para orientar la creación del repositorio HTTP del frontend y el uso de la variable `NEXT_PUBLIC_DRIFT_API_URL`.

**Validación:**

La integración se comprobó mediante ejecución local del frontend y del backend.

---

### Registro 9 — Smoke test de integración

**Fecha:** 2026-09-03
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo actualizamos GitHub Actions para ejecutar pruebas del backend, iniciar FastAPI, compilar el frontend y comprobar que la portada responda?

**Uso:**

Se utilizó para ampliar el pipeline con un smoke test entre frontend y backend.

**Validación:**

El frontend compiló correctamente con `npm run build` y el backend aprobó sus pruebas automatizadas.

---

### Registro 10 — Comando único de ejecución

**Fecha:** 2026-09-06
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo podemos iniciar frontend y backend con un único comando desde la raíz del proyecto?

**Uso:**

Se utilizó para orientar la creación y documentación del script `scripts/start.py`.

**Validación:**

El equipo ejecutó `python scripts/start.py` y verificó el inicio del backend y frontend.

---

### Registro 11 — Organización de scripts

**Fecha:** 2026-09-06
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Dónde debe ubicarse el script de arranque para mantener organizada la estructura del repositorio?

**Uso:**

Se utilizó para evaluar la ubicación de `start.py`.

**Decisión del equipo:**

El script se ubicó en la carpeta `scripts/`.

**Alternativa descartada:**

Se descartó mantener `start.py` directamente en la raíz para separar scripts de los archivos principales del proyecto.

---

### Registro 12 — Prueba del corte vertical

**Fecha:** 2026-09-07
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo creamos una prueba automatizada del corte vertical de búsqueda sin depender directamente de la API real de Steam?

**Uso:**

Se utilizó para orientar la prueba del recorrido completo mediante `TestClient` y respuestas simuladas de Steam.

**Alternativa descartada:**

Se descartaron propuestas iniciales de fixtures que causaban errores durante la ejecución de pytest. El equipo ajustó la estructura hasta obtener pruebas correctas.

---

### Registro 13 — Diagrama C4 de componentes

**Fecha:** 2026-09-11
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo elaboramos un diagrama C4 de componentes usando únicamente elementos que existen realmente en el código actual de DRIFT?

**Uso:**

Se utilizó para orientar el diagrama C4 de componentes y representar responsabilidades y relaciones entre frontend, backend y Steam.

**Alternativa descartada:**

Se descartaron componentes inexistentes, como bases de datos, cachés o servicios no implementados, para evitar documentar una arquitectura futura como si fuera actual.

---

### Registro 14 — Correcciones de documentación y trazabilidad

**Fecha:** 2026-09-13
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo corregimos los enlaces rotos, los nombres de ADR, la ubicación de `correcciones.md` y la trazabilidad de E1–E5?

**Uso:**

Se utilizó para revisar enlaces, actualizar los nombres descriptivos de ADR, completar las evidencias en `docs/aspectos.md` y consolidar la documentación de correcciones.

**Validación:**

El equipo revisó las referencias con la búsqueda global de VS Code y comprobó que no quedaran nombres antiguos de ADR ni referencias a `docs/correciones.md`.

---

### Registro 15 — Disponibilidad ante fallos de Steam

**Fecha:** 2026-09-13
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo podemos evitar que DRIFT falle por completo cuando Steam no esté disponible y cómo comprobamos ese comportamiento?

**Uso:**

Se utilizó para orientar la implementación de `ResilientGameRepository`, un repositorio local de respaldo y una prueba automatizada de falla controlada de Steam.

**Validación:**

La prueba `test_search_uses_fallback_when_steam_is_unavailable` verifica que el sistema responda con información de respaldo e informe que Steam no estuvo disponible.

**Alternativa descartada:**

Se descartó ocultar la caída de Steam al usuario. La respuesta conserva el campo `unavailable_sources` para informar la fuente afectada.

---

### Registro 16 — Estimación de compatibilidad de PC

**Fecha:** 2026-09-13
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo implementamos una estimación básica de compatibilidad de PC sin depender todavía de una fuente externa de requisitos técnicos?

**Uso:**

Se utilizó para orientar un caso de uso de compatibilidad, un puerto de requisitos y un repositorio en memoria con datos controlados.

**Validación:**

Se crearon pruebas para los estados `Compatible`, `Compatible con limitaciones`, `No compatible` y `Requisitos no disponibles`.

**Alcance controlado:**

Los requisitos actuales son datos académicos controlados. No se presentan como una integración real con una base de datos externa.

---

### Registro 17 — Medición y optimización de rendimiento

**Fecha:** 2026-09-13
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo medimos el escenario E1 con 50 usuarios concurrentes y cómo mejoramos el rendimiento sin modificar artificialmente el umbral de calidad?

**Uso:**

Se utilizó para orientar la creación del script `scripts/k6_baseline.js`, interpretar la línea base y proponer optimizaciones en el adaptador de Steam.

**Validación:**

La primera medición obtuvo p95 de 14.63 segundos. Después de aplicar caché temporal, límite de resultados y consultas paralelas, la medición obtuvo p95 de 1.24 segundos con 50 solicitudes exitosas.

**Alternativa descartada:**

Se descartó aumentar el límite de tiempo del escenario E1 para aparentar cumplimiento. En lugar de modificar el objetivo, se optimizó la implementación y se volvió a ejecutar la prueba.

---

### Registro 18 — SonarQube Cloud

**Fecha:** 2026-09-13
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo agregamos SonarQube Cloud al pipeline sin exponer el token de análisis?

**Uso:**

Se utilizó para orientar la configuración de `sonar-project.properties`, el job de SonarQube Cloud en GitHub Actions y el uso del secreto `SONAR_TOKEN`.

**Validación:**

La configuración fue revisada localmente. La ejecución del análisis en GitHub Actions se realizará cuando el equipo autorice el commit y push de los cambios.

**Alternativa descartada:**

Se descartó escribir el token de SonarQube Cloud directamente en el repositorio o en archivos versionados, porque expondría una credencial sensible.
