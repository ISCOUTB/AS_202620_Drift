# ADR-0001: Selección de Arquitectura Base

## Contexto

DRIFT es una plataforma orientada a la comparación de precios de videojuegos, integrando información proveniente de múltiples fuentes externas. El sistema deberá evolucionar para incorporar nuevas plataformas, servicios de análisis, motores de recomendación y posibles fuentes de datos adicionales.

Dado que la **mantenibilidad** ha sido identificada como el principal atributo de calidad, se requiere una arquitectura que facilite la incorporación de nuevas funcionalidades e integraciones sin afectar significativamente el núcleo de la aplicación.

---

## Alternativas Consideradas

### Opción 1: Arquitectura en Capas

#### Descripción

Organiza la aplicación en capas tradicionales (presentación, negocio y persistencia), donde cada capa depende de la inmediatamente inferior.

#### Ventajas

- Fácil de comprender e implementar.
- Amplia documentación y adopción.
- Baja complejidad inicial.

#### Desventajas

- Alto acoplamiento entre capas.
- La lógica de negocio puede terminar dependiendo de detalles de infraestructura.
- Menor flexibilidad para reemplazar tecnologías externas.

---

### Opción 2: Monolito Modular

#### Descripción

Organiza el sistema en módulos funcionales independientes dentro de una única aplicación desplegable.

#### Ventajas

- Buena separación de responsabilidades.
- Despliegue sencillo.
- Facilita la evolución por dominios funcionales.

#### Desventajas

- Puede generar dependencias entre módulos con el tiempo.
- No separa completamente la lógica de negocio de la infraestructura.
- Requiere disciplina arquitectónica constante.

---

### Opción 3: Arquitectura Hexagonal (Ports and Adapters)

#### Descripción

Separa el dominio de la infraestructura mediante puertos y adaptadores, permitiendo que la lógica de negocio permanezca independiente de tecnologías externas.

#### Ventajas

- Alta mantenibilidad.
- Excelente testabilidad.
- Bajo acoplamiento.
- Facilita la incorporación de nuevas integraciones externas.
- Permite reemplazar componentes tecnológicos sin afectar el dominio.

#### Desventajas

- Mayor complejidad inicial.
- Más clases y paquetes desde etapas tempranas.
- Curva de aprendizaje superior a otras alternativas.

---

## Matriz Comparativa

| Criterio | Arquitectura en Capas | Monolito Modular | Hexagonal |
|-----------|-----------|-----------|-----------|
| Mantenibilidad | Media | Alta | Muy Alta |
| Testabilidad | Media | Alta | Muy Alta |
| Facilidad de implementación | Alta | Alta | Media |
| Escalabilidad | Media | Alta | Alta |
| Integración con APIs externas | Media | Alta | Muy Alta |
| Acoplamiento | Alto | Medio | Bajo |
| Adaptación a cambios futuros | Media | Alta | Muy Alta |

---

## Decisión

Se selecciona la **Arquitectura Hexagonal (Ports and Adapters)** como arquitectura base para DRIFT.

La decisión se fundamenta en la necesidad de mantener desacoplada la lógica de negocio respecto de las múltiples fuentes de información externas y facilitar la evolución futura del sistema sin generar dependencias innecesarias entre componentes.

---

## Consecuencias

### Positivas

- Las integraciones con nuevas plataformas pueden agregarse mediante adaptadores independientes.
- La lógica de negocio permanece aislada de detalles tecnológicos.
- Mayor facilidad para realizar pruebas unitarias y de integración.
- Menor impacto ante cambios en APIs externas.
- Incremento de la mantenibilidad general del sistema.

### Negativas

- Incremento en la complejidad inicial del proyecto.
- Mayor cantidad de paquetes y clases desde las primeras iteraciones.
- Requiere conocimiento previo de patrones de diseño y principios de inversión de dependencias.

---

## Estructura Inicial Derivada del ADR

```text
src/main/java/com/drift

├── domain
│   ├── model
│   └── ports
│
├── application
│   └── usecases
│
├── infrastructure
│   ├── steam
│   ├── epic
│   ├── gog
│   ├── persistence
│   └── web
│
└── config
```

Esta estructura representa únicamente el esqueleto inicial del proyecto y no contiene lógica de negocio implementada.
