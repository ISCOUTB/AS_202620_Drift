# ADR-0006: Despliegue serverless para la API de búsqueda de DRIFT

- **Estado:** Aceptado
- **Fecha:** 2026-09-26
- **Decisores:** Equipo DRIFT
- **Relacionado con:** ADR-0002 — Selección de arquitectura base
- **Relacionado con:** ADR-0003 — Reajuste de contextos y responsabilidades del dominio

---

## 1. Contexto

DRIFT expone la funcionalidad de búsqueda de videojuegos mediante el endpoint:

```
GET /games/search?q=<consulta>
```

Para el escenario de evaluación se estableció que el sistema debe soportar hasta **50 usuarios concurrentes** y mantener un tiempo de respuesta **p95 ≤ 3 segundos**. Las solicitudes pueden ser intermitentes, por lo que no es necesario mantener una carga constante sobre la API.

A partir de este escenario se evaluó si la funcionalidad de búsqueda podía ejecutarse mediante un modelo **serverless**, manteniendo el resto de las decisiones arquitectónicas del sistema.

La evaluación se realizó mediante un prototipo desplegado en Vercel utilizando FastAPI y Python.

---

## 2. Problema

Mantener un proceso de backend ejecutándose permanentemente implica disponer de una instancia o contenedor activo incluso durante periodos en los que no existan solicitudes.

Para una funcionalidad como la búsqueda de videojuegos, caracterizada por solicitudes HTTP independientes y potencialmente intermitentes, se consideró la posibilidad de utilizar ejecución bajo demanda mediante funciones serverless.

La decisión debía considerar:

- Cumplimiento del objetivo de rendimiento.
- Capacidad para atender solicitudes concurrentes.
- Simplicidad de despliegue y operación.
- Costos bajo una carga académica esperada.
- Facilidad de reversión.
- Compatibilidad con la arquitectura Hexagonal existente.
- Evitar acoplar el dominio de DRIFT al proveedor de infraestructura.

---

## 3. Alternativas consideradas

### Alternativa A — Mantener la API en un proceso convencional

Mantener FastAPI ejecutándose como un proceso persistente mediante un servidor o contenedor.

**Ventajas:**

- Modelo de ejecución conocido por el equipo.
- Control directo sobre el proceso.
- No depende de características específicas de funciones serverless.

**Desventajas:**

- Requiere mantener un proceso ejecutándose.
- La infraestructura debe permanecer disponible aunque no existan solicitudes.
- Requiere administrar el entorno donde se ejecuta la API.

### Alternativa B — Ejecutar la funcionalidad de búsqueda mediante serverless

Desplegar la API FastAPI como función Python en Vercel.

**Ventajas:**

- Ejecución bajo demanda.
- No requiere mantener un servidor dedicado para el prototipo.
- Despliegue sencillo mediante Vercel.
- Permite conservar la API HTTP existente.
- El código de aplicación continúa separado de la infraestructura mediante los límites definidos por la arquitectura.

**Desventajas:**

- Existen límites propios de la plataforma.
- El comportamiento depende de las condiciones del proveedor.
- Debe considerarse el tiempo de inicialización de las funciones.
- El consumo y los límites gratuitos deben verificarse periódicamente.

---

## 4. Decisión

Se decide utilizar **serverless para la API de búsqueda del prototipo de DRIFT**, mediante una función Python/FastAPI desplegada en Vercel.

Esta decisión **no implica convertir todo DRIFT en una arquitectura serverless ni modificar la arquitectura Hexagonal definida previamente**.

La infraestructura serverless se considera un mecanismo de despliegue para una pieza concreta del sistema: la exposición HTTP de la funcionalidad de búsqueda.

La funcionalidad quedó desplegada públicamente mediante:

```
https://drift-serverless.vercel.app/api/games/search?q=Minecraft
```

El endpoint devuelve información obtenida desde Steam y mantiene el contrato HTTP de búsqueda utilizado por el sistema.

---

## 5. Evidencia del prototipo

El prototipo utiliza la siguiente estructura:

```text
deployment/
└── vercel/
    ├── api/
    │   └── index.py
    ├── requirements.txt
    ├── pyproject.toml
    └── .vercel/
```

La aplicación utiliza FastAPI y expone el endpoint:

```
GET /api/games/search?q=<consulta>
```

La aplicación fue desplegada correctamente en Vercel y posteriormente validada mediante una petición HTTP.

Ejemplo utilizado:

```
curl.exe "https://drift-serverless.vercel.app/api/games/search?q=Minecraft"
```

La respuesta obtenida contiene videojuegos recuperados desde Steam, por ejemplo:

```json
[
  {
    "id": 1912410,
    "name": "Minecraft Dungeons II",
    "prices": {},
    "unavailable_sources": []
  }
]
```

También se implementó un endpoint de comprobación:

```
GET /api
```

que permite verificar que la API se encuentra disponible.

---

## 6. Evaluación del escenario de rendimiento

El escenario definido para la evaluación es:

> DRIFT recibe solicitudes de búsqueda de videojuegos mediante `GET /games/search?q=<consulta>`. El sistema debe soportar hasta 50 usuarios concurrentes y mantener un p95 ≤ 3 segundos. Las solicitudes pueden ser intermitentes, por lo que no es necesario mantener una carga constante.

La prueba se realiza mediante **k6** utilizando 50 usuarios virtuales.

El criterio principal de aceptación es:

```
p95 < 3000 ms
```

y se considera además que la tasa de errores HTTP debe mantenerse por debajo del 1 %.

El endpoint utilizado para la prueba es:

```
https://drift-serverless.vercel.app/api/games/search?q=Minecraft
```

Los resultados definitivos de la prueba de carga se documentarán junto con la evidencia del taller correspondiente.

---

## 7. Costos y límites

Para el prototipo se utiliza el plan **Hobby** de Vercel.

La evaluación de costos considera que la carga académica esperada es pequeña y que las solicitudes son intermitentes.

El análisis de costos debe revisarse cuando cambien los precios, límites o condiciones del proveedor.

Los principales factores que pueden afectar el consumo son:

- Número de invocaciones.
- Tiempo de CPU utilizado.
- Memoria utilizada.
- Transferencia de datos.
- Crecimiento del tráfico.

Por lo tanto, la ausencia de un costo esperado para el prototipo no significa que el servicio sea ilimitado.

**Punto de ruptura**

La solución debe revisarse si el tráfico real supera las condiciones contempladas para el plan utilizado o si alguna de las siguientes situaciones ocurre:

- Se superan los límites incluidos en el plan.
- El volumen de solicitudes aumenta significativamente.
- El tiempo de ejecución de las funciones aumenta.
- Los costos dejan de ser compatibles con las restricciones del proyecto.
- Las necesidades de ejecución persistente hacen que serverless deje de ser adecuado.

Los precios y límites del proveedor deben verificarse nuevamente antes de realizar un despliegue productivo.

---

## 8. Compatibilidad con la arquitectura

La decisión no modifica la arquitectura Hexagonal establecida en ADR-0002.

La función serverless actúa como parte de la infraestructura de ejecución y exposición HTTP.

El dominio y los casos de uso no deben depender directamente de Vercel.

Conceptualmente:

```
Cliente
   │
   ▼
Vercel / función serverless
   │
   ▼
API FastAPI
   │
   ▼
Casos de uso
   │
   ▼
Dominio / puertos
   │
   ▼
Adaptadores externos
   │
   ▼
Steam
```

De esta manera, Vercel constituye un mecanismo de despliegue y no una dependencia conceptual del dominio.

---

## 9. Reversibilidad

La decisión es reversible porque el contrato HTTP de la funcionalidad de búsqueda no depende de Vercel.

Para revertir el despliegue serverless se puede:

- Mantener el código FastAPI existente.
- Ejecutar la API mediante un servidor convencional.
- Reconfigurar el frontend para consumir la nueva URL de la API.
- Mantener los mismos casos de uso y contratos de dominio.

El código específico de despliegue se encuentra aislado en:

```
deployment/vercel/
```

por lo que retirar esta estrategia no requiere eliminar la implementación principal de DRIFT.

---

## 10. Consecuencias positivas

- Permite validar una alternativa de despliegue bajo demanda.
- Reduce la necesidad de mantener un proceso dedicado para el prototipo.
- Mantiene la API HTTP existente.
- Permite realizar pruebas reproducibles sobre una URL pública.
- Mantiene separadas las decisiones de infraestructura y dominio.
- Facilita una futura comparación con un despliegue convencional.

## 11. Consecuencias negativas

- Se introduce una dependencia operativa con Vercel para este despliegue.
- La solución queda condicionada por los límites y características del proveedor.
- El rendimiento puede variar dependiendo del comportamiento de las funciones serverless.
- Se requiere revisar periódicamente los límites y precios del proveedor.
- Una carga elevada o necesidades de ejecución persistente podrían requerir otra estrategia de despliegue.

---

## 12. Criterios para revisar la decisión

La decisión deberá revisarse si:

- El escenario de concurrencia aumenta significativamente.
- El objetivo de p95 deja de cumplirse.
- Las funciones requieren ejecución prolongada o estado persistente.
- Se supera de manera habitual el nivel de uso contemplado para el plan.
- El costo deja de ser compatible con las restricciones del proyecto.
- Se requiere mayor control sobre el entorno de ejecución.
- Se identifica una dependencia del proveedor que dificulte la reversión.

---

## 13. Relación con otros documentos

Esta decisión complementa:

- [**ADR-0002** — Selección de arquitectura base: mantiene la arquitectura Hexagonal.](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0002-adoptar-nextjs-fastapi-arquitectura-hexagonal.md)
- [**ADR-0003** — Reajuste de contextos y responsabilidades del dominio: mantiene la separación de responsabilidades y contextos.](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0003-reajuste-contextos-dominio.md)
- [**Arc42 — Sección 8:** mantiene la separación entre dominio, aplicación e infraestructura.](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/arc42/arc42_8_conceptos_transversales.md)

---

## 14. Estado final

**Aceptado.**

El prototipo serverless de la API de búsqueda de DRIFT fue desplegado y validado mediante una URL pública.

La estrategia se considera válida para la funcionalidad evaluada y para el escenario académico definido, manteniendo la posibilidad de revertir posteriormente hacia una ejecución convencional de FastAPI.
