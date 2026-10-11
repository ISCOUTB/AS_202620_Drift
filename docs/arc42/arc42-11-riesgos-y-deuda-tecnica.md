# 11. Riesgos y deuda técnica

## 11.1. Propósito

Esta sección identifica los principales riesgos técnicos y arquitectónicos de DRIFT, así como la deuda técnica que puede afectar su mantenibilidad, confiabilidad y evolución. Para cada riesgo se describe su posible impacto y las acciones necesarias para reducirlo.

Los riesgos descritos se deben revisar periódicamente y actualizar conforme evolucione la implementación del sistema.

## 11.2. Riesgos arquitectónicos y técnicos

| ID | Riesgo | Impacto | Estrategia de mitigación |
|---|---|---|---|
| R-01 | Indisponibilidad o cambios en las fuentes externas de videojuegos. | La búsqueda puede fallar o devolver información incompleta. | Encapsular las integraciones mediante puertos y adaptadores, validar las respuestas y manejar errores y tiempos de espera. |
| R-02 | Diferencias entre la arquitectura documentada y la implementación real. | Dificulta la comprensión, el mantenimiento y la evolución del sistema. | Mantener sincronizados los ADR, los diagramas C4, arc42 y el código fuente. Registrar formalmente los cambios arquitectónicos. |
| R-03 | Pérdida de información si el catálogo depende de almacenamiento en memoria. | Los datos pueden desaparecer al reiniciar el proceso y no compartirse entre instancias. | Verificar el mecanismo de persistencia actual y determinar si los requisitos requieren almacenamiento persistente. |
| R-04 | Cobertura insuficiente de pruebas del flujo principal de búsqueda. | Los errores funcionales pueden llegar a la rama principal sin detectarse. | Probar el endpoint de búsqueda, los casos de uso y la interacción con las fuentes externas mediante dependencias controladas. |
| R-05 | Falta de observabilidad del sistema desplegado. | Dificulta identificar errores y diagnosticar problemas en producción. | Incorporar logs útiles, comprobaciones de salud y métricas adecuadas al alcance del proyecto. |
| R-06 | Regresiones causadas por cambios en frontend, backend o infraestructura. | Puede afectar funcionalidades existentes y generar incompatibilidades. | Ejecutar pruebas automatizadas en CI y revisar los cambios antes de integrarlos. |
| R-07 | Configuración incorrecta o exposición de secretos. | Puede impedir el despliegue o comprometer las credenciales de servicios externos. | Gestionar la configuración mediante variables de entorno, proteger los secretos y evitar versionar credenciales. |

Los niveles de impacto anteriores son valoraciones cualitativas iniciales. Deben revisarse según la evidencia obtenida durante las pruebas y el despliegue.

## 11.3. Deuda técnica

La deuda técnica comprende decisiones o implementaciones que pueden facilitar el desarrollo inicial, pero que incrementan el costo de mantenimiento o limitan la evolución futura del sistema.

| ID | Elemento | Consecuencia potencial | Acción propuesta |
|---|---|---|---|
| DT-01 | Desactualización de los ADR y diagramas respecto al código. | La documentación puede describir decisiones o componentes que no corresponden con la implementación. | Revisar las decisiones arquitectónicas y actualizar la documentación o el código para mantener su coherencia. |
| DT-02 | Uso de almacenamiento en memoria, si continúa siendo el mecanismo principal. | Pérdida de datos entre reinicios y limitaciones para escalar la aplicación. | Definir los requisitos de persistencia y adoptar una solución persistente cuando el alcance lo requiera. |
| DT-03 | Manejo incompleto de errores de las fuentes externas. | Respuestas inestables y dificultades para diagnosticar fallos. | Estandarizar el manejo de errores y agregar pruebas para respuestas inválidas, vacías y fallos de conexión. |
| DT-04 | Cobertura insuficiente del flujo completo de búsqueda. | Las regresiones pueden pasar inadvertidas durante la integración. | Incorporar pruebas del flujo principal al pipeline de integración continua. |
| DT-05 | Evidencias de calidad y operación incompletas. | Dificultad para demostrar el cumplimiento de los requisitos de calidad. | Conservar resultados verificables de pruebas, análisis de calidad y comprobaciones del despliegue. |

Los elementos que dependan de una condición específica deben verificarse contra la versión actual del repositorio antes de considerarse deuda técnica confirmada.

## 11.4. Estrategia de seguimiento

La gestión de riesgos y deuda técnica se realizará mediante las siguientes actividades:

1. **Verificación:** contrastar cada riesgo con el código, las pruebas, la configuración y la infraestructura existentes.
2. **Priorización:** atender primero los riesgos que puedan afectar el funcionamiento de la búsqueda, la coherencia arquitectónica o la seguridad.
3. **Asignación:** asociar cada acción correctiva con una tarea y un responsable del equipo.
4. **Implementación:** realizar los cambios necesarios en el código, las pruebas o la documentación.
5. **Validación:** comprobar los resultados mediante pruebas reproducibles y conservar la evidencia correspondiente.
6. **Actualización:** revisar esta sección cuando cambie una decisión arquitectónica, se cierre una deuda técnica o aparezca un riesgo nuevo.

## 11.5. Relación con otras secciones de arc42

- **Sección 4 — Estrategia de solución:** relaciona los riesgos con los principios arquitectónicos de DRIFT.
- **Sección 5 — Vista de bloques:** identifica los componentes afectados por cada riesgo.
- **Sección 6 — Vista de ejecución:** permite analizar los escenarios de búsqueda y manejo de errores.
- **Sección 7 — Vista de despliegue:** describe los riesgos asociados a configuración, disponibilidad y operación.
- **Sección 8 — Conceptos transversales:** documenta mecanismos compartidos de validación, manejo de errores, logging y pruebas.
- **Sección 9 — Decisiones arquitectónicas:** registra las decisiones que justifican las soluciones adoptadas.
- **Sección 10 — Requisitos de calidad:** relaciona los riesgos con atributos como mantenibilidad, confiabilidad y capacidad de prueba.
- **Sección 12 — Glosario:** define los términos técnicos necesarios para interpretar esta sección.

## 11.6. Estado y mantenimiento de la sección

Esta sección constituye un registro inicial de riesgos y deuda técnica. Las valoraciones y los elementos pendientes de verificación deben ajustarse con base en la implementación real y en las evidencias obtenidas por el equipo.

La sección se considerará actualizada cuando los riesgos estén evaluados, las acciones prioritarias tengan responsables y los elementos cerrados cuenten con evidencia de validación.
