# ADR-0007: Persistencia de datos y modelo de ejecución

- **Estado:** Propuesto
- **Fecha:** 11/10/2026
- **Decisores:** Equipo de desarrollo de DRIFT

## Contexto

DRIFT es una plataforma web para consultar y comparar videojuegos y su información comercial. Su arquitectura separa las responsabilidades del sistema mediante un enfoque de puertos y adaptadores, con el objetivo de favorecer la mantenibilidad y permitir que las fuentes de datos puedan evolucionar sin afectar directamente al dominio.

Durante la revisión arquitectónica se identificó la necesidad de verificar la coherencia entre las decisiones documentadas, la implementación del backend y la infraestructura de persistencia.

En particular, deben aclararse dos aspectos:

1. El mecanismo de almacenamiento utilizado para conservar la información de los videojuegos.
2. El modelo de ejecución empleado para realizar las operaciones de consulta e integración con fuentes externas.

La documentación debe representar el comportamiento real del sistema y distinguir entre las funcionalidades implementadas y las que todavía se encuentran pendientes.

## Problema

Es necesario establecer una decisión arquitectónica coherente sobre la persistencia y el modelo de ejecución para evitar contradicciones entre los ADR, los diagramas C4, la documentación arc42 y el código fuente.

La decisión debe considerar la complejidad de implementación, la mantenibilidad, la confiabilidad y las necesidades actuales del proyecto.

## Alternativas consideradas

### Alternativa 1: almacenamiento en memoria y ejecución síncrona

Utilizar un repositorio en memoria para almacenar temporalmente los datos y ejecutar las operaciones de consulta de manera síncrona.

**Ventajas:**

- Menor complejidad de implementación.
- Facilita las pruebas y el desarrollo inicial.
- Reduce la configuración de infraestructura necesaria.

**Desventajas:**

- Los datos almacenados pueden perderse al reiniciar el proceso.
- No proporciona persistencia compartida entre instancias.
- Puede resultar insuficiente si se requiere conservar información de manera permanente.

### Alternativa 2: persistencia mediante MySQL y ejecución síncrona

Utilizar una base de datos MySQL para conservar la información y realizar las operaciones mediante un flujo síncrono.

**Ventajas:**

- Permite conservar los datos entre reinicios.
- Facilita la gestión de información persistente.
- Mantiene un modelo de ejecución relativamente sencillo.

**Desventajas:**

- Requiere configurar y mantener la base de datos.
- Introduce dependencias de infraestructura.
- Las operaciones de entrada y salida pueden bloquear el flujo de ejecución durante la espera.

### Alternativa 3: persistencia mediante MySQL y ejecución asíncrona

Utilizar MySQL como mecanismo de persistencia e implementar operaciones asíncronas cuando las necesidades de concurrencia y rendimiento lo justifiquen.

**Ventajas:**

- Permite conservar información de forma persistente.
- Puede mejorar el aprovechamiento de recursos durante operaciones de entrada y salida.
- Facilita la evolución hacia escenarios con mayor concurrencia, si la implementación está diseñada adecuadamente.

**Desventajas:**

- Incrementa la complejidad del código y de las pruebas.
- Requiere controlar correctamente las operaciones asíncronas y los errores.
- Puede añadir complejidad innecesaria si las necesidades actuales no lo justifican.

## Decisión

**Estado pendiente de validación por el equipo.**

Antes de aceptar este ADR, se verificará el estado actual del repositorio y se seleccionará la alternativa que corresponda con los requisitos del proyecto.

La decisión definitiva deberá indicar:

- El mecanismo de persistencia adoptado.
- El modelo de ejecución utilizado.
- La justificación de la alternativa elegida.
- Los componentes del sistema afectados.
- Los cambios necesarios en el código, las pruebas y la documentación.

Una vez aprobada la decisión, se actualizará este documento y se revisarán los ADR anteriores para establecer cuáles continúan vigentes y cuáles deben quedar sustituidos.

## Consecuencias

La decisión definitiva deberá reflejarse de manera consistente en:

- Los modelos y puertos del dominio.
- Los adaptadores de persistencia del backend.
- Los casos de uso de consulta.
- Los diagramas C4 de contenedores y componentes, cuando corresponda.
- Las secciones 5, 6, 7, 8 y 9 de arc42, según los cambios realizados.
- Las pruebas automatizadas y la configuración de despliegue.
- El README y las instrucciones de ejecución del proyecto.

La aceptación del ADR no demuestra por sí misma que la alternativa elegida esté implementada. La implementación y sus pruebas deberán verificarse por separado.

## Criterios de validación

La decisión se considerará validada cuando:

1. El mecanismo de persistencia esté identificado y documentado.
2. El modelo de ejecución coincida con el código real.
3. Las pruebas relevantes se ejecuten correctamente.
4. Los diagramas y documentos afectados estén actualizados.
5. La decisión y sus consecuencias puedan relacionarse con los componentes implementados.

## Referencias

- Documentación de arquitectura arc42 de DRIFT.
- Diagramas C4 del proyecto.
- ADR anteriores relacionados con persistencia y ejecución.
- Código fuente y pruebas automatizadas del backend.
