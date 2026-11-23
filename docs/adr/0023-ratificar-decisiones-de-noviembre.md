# ADR-0023: Ratificar las decisiones ADR-0013 a ADR-0022

- **Estado:** Propuesto (pasa a Aceptado cuando el equipo dé su visto bueno)
- **Fecha:** 2026-11-22
- **Decisores:** Equipo de desarrollo de DRIFT
- **Ratifica a:** [ADR-0013](0013-plazo-total-en-la-busqueda-de-steam.md), [ADR-0014](0014-postgresql-como-persistencia.md), [ADR-0015](0015-copia-de-respaldo-de-las-fuentes.md), [ADR-0016](0016-isthereanydeal-e-historial-de-precios.md), [ADR-0017](0017-inicio-de-sesion-con-google-y-dispositivos.md), [ADR-0018](0018-puntajes-de-hardware-en-la-base-de-datos.md), [ADR-0019](0019-recomendacion-de-compra.md), [ADR-0020](0020-juegos-favoritos.md), [ADR-0021](0021-alertas-de-precio.md) y [ADR-0022](0022-desplegar-solo-en-el-laboratorio.md)
- **Relacionado con:** [evaluación S13/S14](https://github.com/ISCOUTB/AS_202620_feedback/blob/master/revisiones/2026-2/AS_202620_Drift/evaluacion-s13-s14-s15-2026-11-17.md) y [ADR-0024](0024-precios-de-colombia-y-de-referencia.md)

## Contexto

Los ADR-0013 a ADR-0022 siguen con estado «Propuesto», pero sus decisiones ya están en `master` (`a0e18f9`) y desplegadas. Quien lea el repositorio no puede saber si son vigentes.

El equipo sigue la regla de no reescribir los ADR existentes: un cambio se registra en un ADR nuevo que menciona al anterior. Por eso este ADR no edita ninguno de los diez.

## Alternativas

1. **Cambiar el estado dentro de cada ADR.** Es lo más directo, pero toca diez archivos y añade commits al historial de cada decisión.
2. **Registrar la ratificación en un ADR nuevo.** Deja un solo punto de decisión y conserva los diez archivos como están.
3. **No hacer nada.** Mantiene la ambigüedad sobre qué decisiones están vigentes.

## Decisión

Se adopta la **alternativa 2**. Cuando este ADR esté aceptado, las decisiones de esta tabla se consideran **aceptadas**, aunque su archivo diga «Propuesto»:

| ADR | Decisión ratificada | Efecto sobre decisiones anteriores |
|---|---|---|
| ADR-0013 | Plazo total por búsqueda en Steam | Modifica a ADR-0009 en el tiempo de una búsqueda; corrige una cita de ADR-0010 |
| ADR-0014 | PostgreSQL como persistencia | Sustituye la persistencia en memoria de ADR-0008; modifica a ADR-0010 |
| ADR-0015 | Copia de respaldo de las fuentes | Primer uso de la base de datos |
| ADR-0016 | IsThereAnyDeal e historial de precios | CheapShark queda como respaldo sin llave; su regla de precios la complementa ADR-0024 |
| ADR-0017 | Inicio de sesión con Google y dispositivos | Introduce datos personales en el servidor |
| ADR-0018 | Puntajes de hardware en la base de datos | La copia privada queda como respaldo |
| ADR-0019 | Recomendación de compra | Su paso 1 lo ajusta ADR-0024 |
| ADR-0020 | Juegos favoritos | Ninguno |
| ADR-0021 | Alertas de precio | El precio que revisa lo ajusta ADR-0024 |
| ADR-0022 | Desplegar solo en el laboratorio | Sustituye a ADR-0005 y ADR-0006 |

El índice de [arc42 §9](../arc42/arc42_9_Decisiones_Arquitectonicas.md) remite a este ADR para conocer el estado de los diez.

## Consecuencias

**Positivas**

- Un solo lugar dice qué decisiones están vigentes.
- Ningún ADR anterior se reescribe.

**Negativas**

- Quien abra uno de los diez verá «Propuesto» y debe consultar este ADR o el índice de arc42 §9.
- Ratificar no prueba que las decisiones funcionen en el laboratorio: las verificaciones de Google y PostgreSQL siguen en [su guía](../evidencias/verificaciones-pendientes-google-y-laboratorio.md).

## Trazabilidad

- **Aspectos:** F1 a F5 en [docs/aspectos.md](../aspectos.md).
- **C4:** [contenedores](../c4/contenedores.md) y [componentes](../c4/componentes.md).
- **Implementación:** commits `cdb2486` a `109adcc`, fusionados en `a0e18f9` (PR #65).
- **Pruebas:** las citadas en cada ADR ratificado.
