# Uso de Inteligencia Artificial — DRIFT


## 1. Propósito

En esta etapa inicial del proyecto se utilizó *ChatGPT* como herramienta de apoyo para el planteamiento y definición de *DRIFT*. Su uso permitió organizar ideas, explorar posibles funcionalidades y definir qué características podría incorporar la plataforma web.

## 2. Uso inicial

ChatGPT fue utilizado principalmente para:

* Generar ideas sobre funcionalidades para la página web.
* Organizar y definir la propuesta inicial de DRIFT.
* Apoyar la elaboración de la ficha del problema.
* Explorar posibles características que podrían incorporarse en futuras etapas.

## 3. Apoyo en la documentación arquitectónica

Durante el desarrollo del proyecto se utilizó ChatGPT como apoyo para revisar y organizar la documentación relacionada con arc42, los escenarios de calidad y las restricciones arquitectónicas.

Se trabajó en:

* *Sección 1:* Introducción y objetivos.
* *Sección 2:* Restricciones.
* *Sección 3:* Contexto y alcance.
* *Sección 4:* Estrategia de solución.
* *Sección 5:* Vista de Bloques.
* *Sección 6:* Vista de Tiempos de Ejecucion.
* *Sección 9:* Decisiones Arquitectonicas.
* *Sección 10:* Requisitos de Calidad.
* *Sección 12:* Glosario.
* Escenarios de calidad medibles.
* Revisión conceptual de las restricciones arquitectónicas.
* Organización de los documentos mediante enlaces desde el `README.md`.

### 3.1 Revisión de restricciones y escenarios

Durante la revisión se identificó que algunos elementos inicialmente incluidos en la sección de restricciones de arc42 correspondían realmente a requisitos funcionales o atributos de calidad. Por esta razón, se realizó una revisión conceptual para diferenciar las restricciones externas de los objetivos y requisitos del sistema.

También se revisaron las medidas de los escenarios de calidad para mantener coherencia entre los diferentes documentos del proyecto.

## 4. Revisión de conocimientos

Se utilizó ChatGPT para **aclarar conceptos relacionados con estilos arquitectónicos, tácticas y patrones de diseño**, así como para revisar las alternativas consideradas para DRIFT.

Esto permitió reforzar los conocimientos del equipo y apoyar la documentación de las decisiones tomadas durante esta etapa.

## Herramientas de IA que se implementarán

* Claude (Anthropic)
* ChatGPT (OpenAI)
* Gemini (Google)

---
# Log

### Registro 1 — Selección de tecnología para el frontend

**Fecha:** 24/08/2026  
**Herramienta:** ChatGPT  
**Prompt utilizado:**

> "¿Qué sería mejor para el frontend de DRIFT, Next.js o React con Vite? Explícame cuál conviene más para nuestro proyecto y por qué."

**Uso:** Se utilizó ChatGPT para comparar alternativas tecnológicas para el frontend de DRIFT y apoyar la selección de Next.js como framework para la interfaz web.

---

### Registro 2 — Actualización del README

**Fecha:** 24/08/2026  
**Herramienta:** ChatGPT  
**Prompt utilizado:**

> "Mira, el README está así. Tenemos que actualizarlo porque ahora el proyecto tiene frontend y backend, pero quiero mantener más o menos la estructura que ya tiene. ¿Qué deberíamos cambiar?"

**Uso:** Se utilizó ChatGPT para revisar el README, identificar información desactualizada y actualizar las instrucciones de ejecución y la estructura del proyecto de acuerdo con los cambios realizados.

---

### Registro 3 — Relación entre escenarios, árbol de utilidad y matriz

**Fecha:** 24/08/2026  
**Herramienta:** ChatGPT  
**Prompt utilizado:**

> "Te paso el contenido de la matriz y del árbol de utilidad para resolver la observación 4. ¿Cómo podemos hacer que los escenarios E1-E5 queden relacionados correctamente?"

**Uso:** Se utilizó ChatGPT para analizar la relación entre el árbol de utilidad, los escenarios de calidad y la matriz comparativa. Como resultado, se modificó el escenario E2 para representar una situación de mantenibilidad y se actualizaron las referencias E1-E5 en los documentos relacionados.

---

### Registro 4 — Configuración del pipeline de pruebas

**Fecha:** 24/08/2026  
**Herramienta:** ChatGPT  
**Prompt utilizado:**

> "La observación dice que no tenemos pipeline y que la prueba existe pero no está evidenciado el verde. ¿Cómo podemos solucionarlo en GitHub?"

**Uso:** Se utilizó ChatGPT para identificar una solución mediante GitHub Actions y configurar un workflow que ejecuta automáticamente las pruebas del backend utilizando `pytest`. La ejecución del pipeline finalizó correctamente y fue evidenciada mediante el resultado verde de GitHub Actions.

---

### Registro 5 — C4 de contenedores
**Fecha:** 27/08/2026  
**Herramienta:** ChatGPT  
**Prompt utilizado:**

> "Ayúdame a entender cómo hacer el C4 de contenedores de nuestro repositorio DRIFT. Ya tenemos el C4 de contexto, ¿cómo se relaciona con el nivel 2 y qué debería tener en cuenta para hacerlo correctamente?"

**Uso:** Se utilizó para aclarar dudas sobre el C4 de contenedores y su relación con el C4 de contexto.
