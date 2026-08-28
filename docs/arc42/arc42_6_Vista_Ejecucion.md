# 6. Vista de tiempo de ejecución

Esta sección documenta cómo interactúan en tiempo de ejecución los bloques de construcción definidos en la Sección 5. Se seleccionan **3 escenarios representativos**: el flujo principal del sistema, un caso de manejo de fallo (disponibilidad) y un caso de estimación de compatibilidad. Los nombres de los bloques usados en los diagramas son consistentes con la Sección 5.

## 6.1 Escenario: Búsqueda y comparación de precios

Corresponde al escenario de calidad de rendimiento documentado en `docs/Escenarios.md` (búsqueda y comparación, ≤ 3 s p95).

```mermaid
sequenceDiagram
    actor Jugador
    participant UI as Adaptador Web/API
    participant BUSQ as Núcleo: Servicio de Búsqueda y Comparación
    participant REC as Núcleo: Servicio de Recomendación
    participant TIENDAS as Adaptador de Tiendas Digitales
    participant PERSIST as Adaptador de Persistencia

    Jugador->>UI: Buscar videojuego "X"
    UI->>BUSQ: solicitarComparacion("X")
    BUSQ->>TIENDAS: consultarPrecios("X")
    TIENDAS-->>BUSQ: precios y disponibilidad por tienda
    BUSQ->>PERSIST: registrar historial de consulta
    BUSQ->>REC: identificarMejorOpcion(precios)
    REC-->>BUSQ: opción recomendada
    BUSQ-->>UI: resultado de comparación + recomendación
    UI-->>Jugador: muestra comparación y mejor opción
```

**Aspectos relevantes:** el Servicio de Búsqueda delega en el Adaptador de Tiendas Digitales sin conocer cuántas ni cuáles tiendas se consultan (mantenibilidad); la respuesta al usuario depende del tiempo de las tiendas más lentas, lo que motiva el límite de 3 s p95 y el manejo de fallos del escenario 6.2.

---

## 6.2 Escenario: Fallo de una fuente externa de precios

Corresponde al escenario de disponibilidad documentado en `docs/Escenarios.md` (respuesta ante fallo de fuente externa, ≤ 5 s).

```mermaid
sequenceDiagram
    actor Jugador
    participant UI as Adaptador Web/API
    participant BUSQ as Núcleo: Servicio de Búsqueda y Comparación
    participant TIENDAS as Adaptador de Tiendas Digitales
    participant Steam as Sub-adaptador Steam
    participant Epic as Sub-adaptador Epic

    Jugador->>UI: Buscar videojuego "X"
    UI->>BUSQ: solicitarComparacion("X")
    BUSQ->>TIENDAS: consultarPrecios("X")
    TIENDAS->>Steam: consultarPrecio("X")
    TIENDAS->>Epic: consultarPrecio("X")
    Steam--xTIENDAS: timeout / error
    Epic-->>TIENDAS: precio disponible
    Note over TIENDAS: Se descarta el resultado de Steam.<br/>No se detiene la respuesta global.
    TIENDAS-->>BUSQ: precios disponibles + aviso "Steam no disponible"
    BUSQ-->>UI: resultado parcial + advertencia
    UI-->>Jugador: muestra comparación disponible<br/>e indica fuente no disponible
```

**Aspectos relevantes:** el fallo de un sub-adaptador (Steam) es aislado por el Adaptador de Tiendas Digitales y no interrumpe la respuesta general; esto materializa en tiempo de ejecución la restricción 2.3/2.4 (disponibilidad ante fallo de fuente externa) y la decisión arquitectónica de la Sección 4 (aislamiento de dependencias externas).

---

## 6.3 Escenario: Estimación de compatibilidad y rendimiento en PC

Corresponde al escenario de calidad documentado en `docs/Escenarios.md` (estimación de compatibilidad/rendimiento, ≤ 5 s p95).

```mermaid
sequenceDiagram
    actor Jugador
    participant UI as Adaptador Web/API
    participant COMPAT as Núcleo: Servicio de Estimación de Compatibilidad
    participant INFO as Adaptador de Proveedor de Información
    participant PERSIST as Adaptador de Persistencia

    Jugador->>UI: Consultar compatibilidad de "X" en su PC
    UI->>COMPAT: estimarCompatibilidad("X", specsDispositivo)
    COMPAT->>INFO: obtenerRequisitos("X")
    INFO-->>COMPAT: requisitos mínimos/recomendados
    COMPAT->>PERSIST: obtenerSpecsDispositivo(usuario)
    PERSIST-->>COMPAT: especificaciones registradas
    COMPAT->>COMPAT: comparar specs vs requisitos
    COMPAT-->>UI: resultado (compatible / rendimiento estimado)
    UI-->>Jugador: muestra estimación de compatibilidad
```

**Aspectos relevantes:** el Servicio de Estimación de Compatibilidad depende únicamente de los puertos de información y persistencia, no de la implementación concreta del proveedor externo, lo que permite sustituir la fuente de datos sin afectar la lógica de comparación (mantenibilidad, ver Sección 5.2.1).
