# 2. Restricciones

Las restricciones de DRIFT corresponden a condiciones que deben ser consideradas al momento de definir la arquitectura del sistema. Estas condiciones provienen principalmente del problema planteado, de las características de las fuentes externas de información y de los objetivos de calidad definidos para el proyecto.

## 2.1 Dependencia de fuentes externas de información

DRIFT depende de información proveniente de diferentes tiendas digitales y proveedores de información de videojuegos.

Las fuentes externas pueden manejar diferentes catálogos, formatos de información, precios, descuentos y condiciones de disponibilidad. Por esta razón, la arquitectura debe considerar la integración con múltiples fuentes y evitar que las diferencias entre ellas afecten significativamente al resto del sistema.

**Justificación:**  
El problema identificado establece que la información de precios, descuentos y disponibilidad se encuentra distribuida entre diferentes plataformas.

---

## 2.2 Incorporación de múltiples plataformas digitales

El sistema debe permitir trabajar con información proveniente de diferentes plataformas digitales, como tiendas de videojuegos para PC y consolas.

La arquitectura no debe estar diseñada de manera que una única plataforma sea indispensable para el funcionamiento general del sistema.

**Justificación:**  
El objetivo principal de DRIFT es centralizar información que actualmente se encuentra distribuida entre diferentes tiendas. La solución debe poder trabajar con varias fuentes para realizar comparaciones entre las opciones disponibles.

---

## 2.3 Capacidad de incorporar nuevas fuentes

La arquitectura debe permitir agregar nuevas tiendas o fuentes de información sin requerir modificaciones importantes en las demás partes del sistema.

Los cambios relacionados con una fuente específica deben mantenerse lo más aislados posible del resto de funcionalidades.

**Justificación:**  
La mantenibilidad es el principal atributo de calidad declarado para DRIFT. El proyecto establece como necesidad la incorporación de nuevas plataformas y fuentes de información, así como la posibilidad de modificar componentes sin afectar significativamente otras funcionalidades.

---

## 2.4 Manejo de fallos de fuentes externas

El fallo o indisponibilidad temporal de una fuente externa no debe provocar la interrupción completa de la consulta de precios.

Cuando una fuente no pueda proporcionar información, DRIFT debe poder continuar mostrando la información disponible de las demás fuentes e informar que la fuente afectada no está disponible.

**Justificación:**  
Este comportamiento está definido explícitamente en los escenarios de calidad de DRIFT. El sistema debe mantener la consulta operativa incluso cuando una fuente externa de precios deje de responder.

---

## 2.5 Centralización de información para la comparación

DRIFT debe integrar información relacionada con precios, descuentos, historial de precios y disponibilidad de plataformas, junto con información necesaria para estimar la compatibilidad y el rendimiento en PC.

La arquitectura debe permitir relacionar esta información para que pueda ser utilizada en la comparación y recomendación de opciones.

**Justificación:**  
El problema identificado surge precisamente de que esta información se encuentra distribuida entre diferentes plataformas y fuentes. La propuesta de DRIFT busca centralizarla para reducir el tiempo de búsqueda y facilitar decisiones de compra informadas.

---

## 2.6 Consideración de las características del dispositivo del usuario

Para las funcionalidades relacionadas con PC, el sistema debe considerar las especificaciones del dispositivo registrado por el usuario y compararlas con los requisitos del videojuego.

**Justificación:**  
DRIFT plantea estimar el rendimiento y la compatibilidad de un videojuego en PC a partir de las especificaciones del dispositivo y de los requisitos del videojuego.

---

## 2.7 Restricciones de rendimiento

Las operaciones principales del sistema deben cumplir con los tiempos de respuesta establecidos en los escenarios de calidad.

Actualmente se establecen las siguientes medidas:

- Búsqueda y comparación de precios: **≤ 3 segundos en p95**.
- Consulta de información de un videojuego: **≤ 2 segundos en p95**.
- Estimación de compatibilidad y rendimiento en PC: **≤ 5 segundos en p95**.
- Consulta ante el fallo de una fuente externa: **≤ 5 segundos**.

**Justificación:**  
Estos tiempos se encuentran definidos como medidas verificables en los escenarios de calidad del proyecto y representan condiciones que la arquitectura deberá considerar.

---

## 2.8 Restricción de mantenibilidad

La arquitectura debe priorizar la mantenibilidad del sistema, procurando que los cambios, ampliaciones y modificaciones puedan realizarse con un impacto reducido sobre las funcionalidades existentes.

Esto incluye principalmente:

- Incorporar nuevas plataformas digitales.
- Agregar nuevas fuentes de información.
- Modificar la lógica de comparación.
- Modificar la lógica de recomendación.
- Añadir nuevos filtros o características.

**Justificación:**  
La mantenibilidad es el aspecto de calidad prioritario declarado para DRIFT debido a que el sistema depende de múltiples fuentes externas y está planteado para crecer e incorporar nuevas funcionalidades.
