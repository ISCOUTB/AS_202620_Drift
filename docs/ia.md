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
**Herramienta:**ChatGPT

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

---

### Registro 19 — Integración de una nueva API para DRIFT

Fecha: 2026-09-19 Herramienta: ChatGPT

Consulta utilizada:

> ¿Cómo podemos integrar una nueva API en DRIFT para consultar información de videojuegos y conectarla con el backend existente?

Uso:

Se utilizó ChatGPT como apoyo para revisar la integración de una nueva API externa en el backend de DRIFT. La orientación se enfocó en identificar el lugar adecuado para realizar la conexión, organizar el consumo de la API mediante la arquitectura existente y mantener separadas las responsabilidades del dominio, los casos de uso y la infraestructura.

Validación:

El equipo revisó la implementación de la nueva API dentro del repositorio y verificó su relación con el backend actual. También se revisó que la integración conservara la organización arquitectónica del proyecto y que no se mezclara directamente la lógica de consumo de la API con los componentes de interfaz.

Alternativa descartada:

Se descartó realizar las solicitudes a la nueva API directamente desde los componentes del frontend, debido a que esto aumentaría el acoplamiento y dificultaría el mantenimiento de la aplicación.

---

### Registro 20 — Prueba automatizada de contrato OpenAPI

Fecha: 2026-09-20 Herramienta: ChatGPT

Consulta utilizada:

> ¿Cómo implementamos una prueba de contrato para validar automáticamente que los endpoints de DRIFT cumplen con el contrato OpenAPI?

Uso:

Se utilizó como apoyo para implementar una prueba automatizada mediante Schemathesis, tomando como fuente el contrato `docs/api/drift/openapi.yaml`. La prueba se implementó en `backend/tests/test_contract.py` y utiliza `pytest` para ejecutar los casos generados a partir de las operaciones definidas en el contrato.

Alternativa descartada:

Se descartó realizar únicamente pruebas manuales de cada endpoint, ya que no permitirían validar automáticamente todas las operaciones y esquemas definidos en el contrato OpenAPI. Se optó por Schemathesis para automatizar esta validación.

---

### Registro 20 — Validación ante cambio incompatible en el contrato

Fecha: 2026-09-20 Herramienta: ChatGPT

Consulta utilizada:

> ¿Cómo podemos demostrar mediante una prueba automatizada que el contrato de la API detecta cambios incompatibles?

Uso:

Se utilizó como apoyo para validar que la prueba de contrato implementada con Schemathesis no solamente verifica el funcionamiento normal de los endpoints, sino que también detecta cambios que generan incompatibilidades con el contrato OpenAPI.

Alternativa descartada:

Se descartó utilizar únicamente una ejecución exitosa como evidencia, ya que esta demostraría que el contrato es válido en condiciones normales, pero no que la prueba sea capaz de detectar cambios incompatibles. Se utilizó un cambio controlado para comprobar explícitamente el comportamiento de la prueba ante una incompatibilidad.

---

### Registro 21 — Planificación del despliegue de DRIFT

Fecha: 2026-09-27 Herramienta: ChatGPT

Consulta utilizada:

> ¿Cómo podemos organizar el despliegue de DRIFT utilizando Azure para el backend, Vercel para el frontend y dejar preparada la integración con Supabase para cuando se implemente la base de datos?

Uso:

Se utilizó ChatGPT como apoyo para organizar la estrategia de despliegue de DRIFT, diferenciando las responsabilidades de Azure, Vercel y Supabase. Se revisó el flujo de despliegue del backend mediante Azure Web App, el despliegue del frontend mediante Vercel y el uso futuro de Supabase como servicio de base de datos.

Validación:

El equipo revisó la propuesta de despliegue y la relacionó con la arquitectura actual del proyecto. Se mantuvo Supabase como componente previsto para una etapa posterior, debido a que la base de datos todavía no forma parte de la implementación actual.

Alternativa descartada:

Se descartó presentar Supabase como un componente actualmente operativo, ya que su utilización está prevista para la etapa en la que se implemente la persistencia de datos.

---

### Registro 22 — Documentación de la decisión de despliegue

Fecha: 2026-09-27 Herramienta: ChatGPT

Consulta utilizada:

> ¿Cómo documentamos mediante un ADR la decisión de utilizar Azure para el backend, Vercel para el frontend y Supabase para la futura base de datos?

Uso:

Se utilizó ChatGPT como apoyo para estructurar un Architecture Decision Record (ADR) relacionado con la estrategia de despliegue de DRIFT. La documentación busca registrar las tecnologías seleccionadas, sus responsabilidades y las razones técnicas de la decisión.

Validación:

El equipo revisó la estructura propuesta tomando como referencia los ADR existentes del repositorio y manteniendo la organización utilizada en la documentación arquitectónica de DRIFT.

Alternativa descartada:

Se descartó documentar las tecnologías de despliegue únicamente en el README, debido a que la decisión involucra criterios arquitectónicos que requieren una justificación y trazabilidad independiente.

---

### Registro 23 — Corrección de dependencias de GitHub Actions

Fecha: 2026-09-27 Herramienta: ChatGPT

Consulta utilizada:

> ¿Cómo solucionamos los avisos de SonarQube que indican que las GitHub Actions deben utilizar el SHA completo del commit?

Uso:

Se utilizó ChatGPT como apoyo para analizar los avisos de seguridad de SonarQube relacionados con el uso de versiones mediante etiquetas como `@v4`, `@v5`, `@v2` y `@v3` en GitHub Actions. Se identificó la necesidad de fijar las acciones a un SHA completo para evitar que una referencia mutable cambie el código ejecutado por el pipeline.

Validación:

Se revisó el workflow de despliegue de DRIFT y se identificaron las acciones `actions/checkout`, `actions/setup-python`, `azure/login` y `azure/webapps-deploy` como dependencias que requieren fijación mediante SHA.

Alternativa descartada:

Se descartó mantener únicamente las etiquetas de versión (`@v4`, `@v5`, `@v2` y `@v3`), debido a que SonarQube identifica este patrón como un riesgo de seguridad relacionado con dependencias externas no fijadas.

### Registro 24 — Revisión de arquitectura Hexagonal

**Fecha:** 2026-09-28
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo podemos revisar la estructura actual de DRIFT para verificar que mantiene la arquitectura Hexagonal y que las responsabilidades están correctamente separadas?

**Uso:**

Se utilizó ChatGPT como apoyo para revisar la organización del backend y verificar la separación entre dominio, aplicación, puertos e infraestructura.

**Validación:**

El equipo comparó las recomendaciones con la estructura real del repositorio y mantuvo únicamente los elementos que correspondían a componentes existentes.

**Alternativa descartada:**

Se descartó modificar la arquitectura existente sin evidencia de un problema concreto, manteniendo la estructura Hexagonal definida para DRIFT.

---

### Registro 25 — Revisión del repositorio Steam

**Fecha:** 2026-09-28
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo podemos mejorar `SteamGameRepository` para reducir el tiempo de respuesta de las búsquedas manteniendo la arquitectura actual?

**Uso:**

Se utilizó ChatGPT para analizar el flujo de consultas hacia Steam y proponer mecanismos de caché, limitación de resultados y ejecución paralela de consultas.

**Validación:**

El equipo revisó las modificaciones propuestas y las relacionó con la medición del escenario E1 mediante k6.

**Alternativa descartada:**

Se descartó modificar artificialmente el umbral de rendimiento y se mantuvo el objetivo establecido en el escenario E1.

---

### Registro 26 — Caché temporal de Steam

**Fecha:** 2026-09-13
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo podemos agregar una caché temporal a `SteamGameRepository` para evitar repetir consultas iguales a Steam?

**Uso:**

Se utilizó ChatGPT como apoyo para diseñar una caché en memoria con una duración limitada para las búsquedas realizadas contra Steam.

**Validación:**

El equipo revisó la implementación y verificó que la caché perteneciera al adaptador de Steam, manteniendo la responsabilidad aislada de los casos de uso.

**Alternativa descartada:**

Se descartó introducir una base de datos o sistema de caché externo para esta optimización, debido a que el alcance actual no requería incorporar infraestructura adicional.

---

### Registro 27 — Consultas paralelas a Steam

**Fecha:** 2026-09-13
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo podemos consultar en paralelo los detalles de los videojuegos obtenidos desde Steam para reducir la latencia?

**Uso:**

Se utilizó ChatGPT para analizar la posibilidad de ejecutar las consultas de detalles de Steam en paralelo mediante `ThreadPoolExecutor`.

**Validación:**

La implementación fue integrada en `SteamGameRepository` y posteriormente contrastada mediante la medición de rendimiento del escenario E1.

**Alternativa descartada:**

Se descartó realizar todas las consultas de detalles secuencialmente debido al impacto acumulativo de la latencia de las solicitudes externas.

---

### Registro 28 — Límite de resultados de Steam

**Fecha:** 2026-09-13
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo podemos limitar la cantidad de resultados obtenidos desde Steam para evitar realizar consultas innecesarias de detalles?

**Uso:**

Se utilizó ChatGPT como apoyo para limitar los resultados procesados por `SteamGameRepository` a los primeros cinco elementos.

**Validación:**

El equipo revisó que el límite se aplicara únicamente en el adaptador externo y que no modificara el contrato del caso de uso de búsqueda.

**Alternativa descartada:**

Se descartó solicitar y procesar decenas de detalles de videojuegos cuando la interfaz únicamente necesitaba un conjunto reducido de resultados.

---

### Registro 29 — Prueba de rendimiento con k6

**Fecha:** 2026-09-13
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo podemos construir una prueba de carga con k6 para el escenario E1 utilizando 50 usuarios concurrentes y midiendo el p95?

**Uso:**

Se utilizó ChatGPT para orientar la configuración de `scripts/k6_baseline.js` y la definición de los umbrales de rendimiento.

**Validación:**

El equipo ejecutó la prueba contra el endpoint de búsqueda y registró los resultados en `docs/evidencias/e1-linea-base.md`.

**Alternativa descartada:**

Se descartó utilizar únicamente una medición manual, debido a que no permitiría reproducir de forma consistente la condición de concurrencia definida en E1.

---

### Registro 30 — Análisis de resultados de rendimiento

**Fecha:** 2026-09-13
**Herramienta:** ChatGPT

**Consulta utilizada:**

> Tenemos un p95 inicial de 14.63 segundos para E1. ¿Cómo podemos identificar qué parte de la búsqueda está generando la latencia?

**Uso:**

Se utilizó ChatGPT para analizar el flujo de búsqueda y relacionar la latencia con las consultas externas realizadas por `SteamGameRepository`.

**Validación:**

El equipo contrastó el análisis con la implementación real y utilizó los resultados para orientar las optimizaciones posteriores.

**Alternativa descartada:**

Se descartó asumir que el problema estaba en el frontend sin revisar primero el flujo de solicitudes del backend y la comunicación con Steam.

---

### Registro 31 — Validación posterior de E1

**Fecha:** 2026-09-13
**Herramienta:** ChatGPT

**Consulta utilizada:**

> Después de optimizar `SteamGameRepository`, ¿cómo debemos volver a ejecutar E1 y comparar el resultado con el umbral de p95?

**Uso:**

Se utilizó ChatGPT para orientar la repetición de la prueba de carga y la comparación entre la línea base y la medición posterior.

**Validación:**

La segunda medición registró un p95 de 1.24 segundos con 50 solicitudes exitosas, y los resultados fueron documentados en `docs/evidencias/e1-linea-base.md`.

**Alternativa descartada:**

Se descartó modificar el umbral de E1 para considerar válida la medición inicial y se mantuvo el criterio de p95 ≤ 3 segundos.

---

### Registro 32 — Revisión del contrato de búsqueda

**Fecha:** 2026-09-20
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo podemos comprobar que un cambio en la respuesta de `/games/search` rompe el contrato esperado de la API?

**Uso:**

Se utilizó ChatGPT para analizar la relación entre las pruebas automatizadas, el contrato OpenAPI y la respuesta generada por el endpoint.

**Validación:**

El equipo utilizó un cambio controlado en el campo `name` de la respuesta para comprobar que el contrato pudiera detectar la incompatibilidad.

**Alternativa descartada:**

Se descartó utilizar únicamente una prueba de funcionamiento exitoso, ya que no demostraría el comportamiento ante una ruptura del contrato.

---

### Registro 33 — Ruptura controlada del contrato

**Fecha:** 2026-09-20
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo podemos introducir una ruptura controlada en el contrato de la API para demostrar que la prueba falla ante el defecto?

**Uso:**

Se utilizó ChatGPT como apoyo para definir una modificación intencional del campo `name` de la respuesta del endpoint.

**Validación:**

El cambio controlado produjo una ejecución fallida del pipeline de CI. Posteriormente se restauró el contrato original.

**Alternativa descartada:**

Se descartó utilizar un fallo aleatorio o una prueba sin relación con el contrato, ya que la evidencia debía demostrar específicamente la detección del defecto.

---

### Registro 34 — Revisión del fallo de CI

**Fecha:** 2026-09-20
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo podemos documentar la evidencia de un CI que falla después de introducir intencionalmente un cambio incompatible en la API?

**Uso:**

Se utilizó ChatGPT para organizar la trazabilidad entre el commit que introdujo el defecto, la ejecución fallida y el commit que restauró el contrato.

**Validación:**

El equipo verificó la secuencia histórica `9c102df → CI fallido → 9750878` y documentó la evidencia correspondiente.

**Alternativa descartada:**

Se descartó presentar únicamente el CI en verde como evidencia, porque no demostraría que la prueba detecta el defecto.

---

### Registro 35 — Revisión de responsabilidades de contextos

**Fecha:** 2026-09-14
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo podemos organizar las responsabilidades de `SearchGames`, `SteamGameRepository`, `ResilientGameRepository` y `EstimateCompatibility` sin romper la arquitectura Hexagonal?

**Uso:**

Se utilizó ChatGPT para revisar la separación de responsabilidades entre los contextos de búsqueda, integración externa y compatibilidad de PC.

**Validación:**

El equipo contrastó la propuesta con ADR-0003 y mantuvo las responsabilidades documentadas en la arquitectura.

**Alternativa descartada:**

Se descartó crear microservicios independientes para cada contexto debido al alcance y complejidad innecesaria para el proyecto actual.

---

### Registro 36 — Relación entre ADR y código existente

**Fecha:** 2026-09-19
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo podemos relacionar la decisión documentada en el ADR de integración con la implementación real de `SteamGameRepository`?

**Uso:**

Se utilizó ChatGPT para revisar la trazabilidad entre ADR-0004, el adaptador de Steam y la estrategia de integración con fuentes externas.

**Validación:**

El equipo revisó el ADR y el código existente, identificando la relación entre la estrategia híbrida y el aislamiento de las fuentes externas mediante adaptadores.

**Alternativa descartada:**

Se descartó presentar el ADR como si hubiera originado el adaptador cuando el historial demuestra que `SteamGameRepository` existía previamente.

---

### Registro 37 — Trazabilidad del componente seleccionado

**Fecha:** 2026-09-30
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo podemos construir la trazabilidad completa de `SteamGameRepository` desde su implementación hasta los escenarios y evidencias de calidad?

**Uso:**

Se utilizó ChatGPT para relacionar el componente con sus commits, ADR, escenario E1, script de k6 y evidencias de medición.

**Validación:**

El equipo contrastó la trazabilidad con el historial de Git y la documentación existente del proyecto.

**Alternativa descartada:**

Se descartó presentar únicamente la ruta del archivo como evidencia, debido a que la evaluación requiere relacionar implementación, decisión arquitectónica y evidencia de calidad.

---

### Registro 38 — Revisión de evidencias de arquitectura

**Fecha:** 2026-09-30
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo podemos organizar la evidencia de la evaluación S9 para que cada criterio tenga una trazabilidad verificable sin duplicar información?

**Uso:**

Se utilizó ChatGPT para revisar la relación entre los criterios de evaluación, los documentos del repositorio, los commits y las pruebas existentes.

**Validación:**

El equipo revisó cada criterio de manera independiente y organizó la evidencia en `docs/evidencias/`.

**Alternativa descartada:**

Se descartó reunir todas las evidencias en una única sección sin distinguir los criterios, porque dificultaría verificar la correspondencia entre cada requisito y su evidencia.

---

### Registro 39 — Revisión de evidencia de medición del servidor

**Fecha:** 2026-09-30
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo debemos relacionar las mediciones realizadas en el servidor y en el despliegue con el escenario E1 sin duplicar la evidencia de rendimiento?

**Uso:**

Se utilizó ChatGPT para diferenciar la medición principal del escenario E1 de las mediciones complementarias realizadas sobre el despliegue serverless.

**Validación:**

El equipo revisó `docs/evidencias/e1-linea-base.md` y `docs/evidencias/Evidencia_TallerS8.md` para mantener cada medición en su contexto correspondiente.

**Alternativa descartada:**

Se descartó presentar las mediciones del servidor y del despliegue como si fueran exactamente la misma prueba, debido a que corresponden a contextos de ejecución diferentes.

---

### Registro 40 — Organización de evidencias S9

**Fecha:** 2026-09-30
**Herramienta:** ChatGPT

**Consulta utilizada:**

> ¿Cómo podemos documentar cada criterio de la matriz S9 utilizando únicamente evidencias que podamos comprobar en el repositorio?

**Uso:**

Se utilizó ChatGPT para organizar la evidencia documental y técnica correspondiente a los criterios de la matriz S9.

**Validación:**

El equipo revisó los archivos, commits, pruebas y resultados disponibles antes de incorporar cada evidencia.

**Alternativa descartada:**

Se descartó incluir afirmaciones que no pudieran relacionarse con un archivo, commit, ejecución de CI, prueba o resultado verificable.
