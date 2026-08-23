# 2. Restricciones

Las restricciones de DRIFT corresponden a condiciones externas o de contexto que limitan las decisiones que pueden tomarse durante el diseño y desarrollo de la arquitectura del sistema.

Estas restricciones provienen principalmente del contexto académico del proyecto, de las características del equipo de desarrollo, del uso de fuentes externas de información y de las condiciones establecidas para el desarrollo del proyecto.

## 2.1 Restricciones organizacionales

### Equipo de desarrollo

DRIFT es desarrollado por un equipo de **4 integrantes** dentro del curso de Arquitectura de Software.

**Justificación:**  
La cantidad de integrantes condiciona la capacidad disponible para desarrollar, probar, documentar y mantener el sistema durante el proyecto.

---

## 2.2 Restricciones académicas y de plazo

### Entregas del curso

El desarrollo de DRIFT está condicionado por las entregas y fechas establecidas para el curso **AS_202620 – Arquitectura de Software**.

**Justificación:**  
El proyecto debe cumplir con los entregables y tiempos definidos por el curso, lo que limita el tiempo disponible para diseñar, implementar y validar la arquitectura.

---

## 2.3 Restricciones tecnológicas

El proyecto deberá considerar las tecnologías que hayan sido establecidas como obligatorias por el curso o por los lineamientos del proyecto.

En caso de que no exista un stack tecnológico obligatorio, las tecnologías utilizadas podrán seleccionarse de acuerdo con las necesidades del sistema y las capacidades del equipo de desarrollo.

**Justificación:**  
Las tecnologías impuestas externamente limitan las alternativas disponibles para implementar la solución. Si no existen tecnologías obligatorias, esta restricción no limita directamente las decisiones arquitectónicas.

---

## 2.4 Restricciones relacionadas con fuentes externas

El acceso a información de precios, descuentos, disponibilidad y demás datos de videojuegos estará condicionado por las interfaces, APIs, mecanismos de acceso y condiciones de uso que proporcionen las fuentes externas seleccionadas.

DRIFT deberá considerar las características y limitaciones particulares de cada fuente al momento de integrar su información.

**Justificación:**  
DRIFT depende de información proporcionada por terceros. Las condiciones técnicas y de uso de cada fuente pueden limitar la forma en que el sistema puede obtener, consultar y actualizar dicha información.

---

## 2.5 Restricción de proceso: uso de inteligencia artificial

El uso de herramientas de inteligencia artificial durante el desarrollo del proyecto debe registrarse y documentarse en `docs/ia.md`.

**Justificación:**  
El proyecto contempla el registro del uso de herramientas de inteligencia artificial, por lo que el proceso de desarrollo debe incluir la documentación correspondiente.

---

## 2.6 Restricciones de rendimiento

Las operaciones principales del sistema deben considerar los tiempos de respuesta establecidos en los escenarios de calidad del proyecto.

Actualmente se establecen las siguientes medidas:

- Búsqueda y comparación de precios: **≤ 3 segundos en p95**.
- Consulta de información de un videojuego: **≤ 3 segundos en p95**.
- Estimación de compatibilidad y rendimiento en PC: **≤ 5 segundos en p95**.
- Consulta ante el fallo de una fuente externa: **≤ 5 segundos**.

**Justificación:**  
Estos tiempos representan condiciones medibles establecidas para el sistema y deben ser considerados durante las decisiones de diseño y arquitectura.
