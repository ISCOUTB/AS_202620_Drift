# 4. Estrategia de solución
 
DRIFT adopta **Arquitectura Hexagonal (Ports and Adapters)** como modelo arquitectónico principal. Esta decisión mantiene la lógica del sistema independiente de las tiendas digitales, proveedores de información y demás servicios externos con los que DRIFT se integra (ver Sección 3).
 
La comparación con las alternativas consideradas y las consecuencias de esta decisión se documentan en **ADR-0001**.
 
## 4.1 Decisiones frente a los objetivos de calidad
 
| Objetivo de calidad | Escenario relacionado | Estrategia de solución |
|---|---|---|
| Mantenibilidad | Incorporación de una nueva plataforma/fuente sin modificar el núcleo | Separación núcleo/adaptadores mediante puertos; cada fuente externa se integra a través de su propio adaptador. |
| Disponibilidad | Fallo de una fuente externa de precios | Aislamiento de dependencias externas: el fallo de un adaptador no bloquea la respuesta del núcleo ni de los demás adaptadores. |
| Rendimiento | Búsqueda y comparación de precios (≤ 3 s p95) | Aplicación única, sin comunicación innecesaria entre servicios internos; las integraciones externas se controlan desde los adaptadores. |
| Testabilidad | *(no cubierto aún por un escenario en Escenarios.md — pendiente de agregar)* | Desacoplamiento de servicios externos mediante puertos, permitiendo dobles de prueba (mocks/stubs) para la lógica de dominio. |
 
## 4.2 Decisiones tecnológicas
 
El dominio no dependerá directamente de frameworks, APIs concretas ni tecnologías de persistencia. Estas dependencias se gestionan mediante los adaptadores correspondientes. La selección definitiva del stack se documentará aquí una vez definida, considerando las restricciones técnicas de la Sección 2.2.
 
## 4.3 Decisiones organizativas
 
Equipo de 4 integrantes (ver Sección 2.1), desarrollo incremental: se prioriza validar la arquitectura (puertos, adaptadores, integración con una fuente externa) antes de completar la lógica de negocio y el resto de integraciones. La separación por puertos/adaptadores permite distribuir el trabajo entre los integrantes con bajo acoplamiento.
 
## 4.4 Relación con las restricciones
 
Esta estrategia responde directamente a las restricciones de la Sección 2: dependencia de múltiples fuentes externas con distintos formatos y niveles de acceso (2.3), equipo y plazos académicos reducidos (2.1), y ausencia de control sobre la disponibilidad de las fuentes externas (2.2).
 
Los detalles estructurales de esta estrategia (componentes, puertos y adaptadores) se documentan en la Sección 5 (Vista de bloques de construcción).
