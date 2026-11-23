# 6. Vista de tiempo de ejecución

Esta sección documenta cómo interactúan en tiempo de ejecución los bloques de construcción definidos en la Sección 5. Siguiendo el criterio de arc42 (relevancia arquitectónica, no exhaustividad), se seleccionan **3 escenarios representativos**: el flujo principal del sistema, un caso de manejo de fallo (disponibilidad) y un caso de estimación de compatibilidad. Los nombres de los bloques usados en los diagramas son consistentes con la Sección 5.

## 6.1 Escenario: Búsqueda y comparación de precios
> **Nota:** Este escenario representa el flujo de ejecución previsto para la arquitectura de DRIFT. El corte vertical actualmente implementado demuestra la búsqueda de videojuegos y consulta de precios mediante Steam; los componentes de recomendación y persistencia mostrados aquí corresponden a extensiones previstas del sistema.

Corresponde al escenario de calidad de rendimiento documentado en `docs/escenarios.md` (búsqueda y comparación, ≤ 3 s p95).

```mermaid
sequenceDiagram
    participant Jugador
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

**Explicación:**

1. El jugador busca un videojuego desde el Adaptador Web/API.
2. El Adaptador Web/API invoca el puerto de entrada del Servicio de Búsqueda y Comparación.
3. El Servicio de Búsqueda consulta precios y disponibilidad a través del Adaptador de Tiendas Digitales.
4. El Adaptador de Tiendas Digitales devuelve los precios obtenidos de cada tienda.
5. El Servicio de Búsqueda registra la consulta en el Adaptador de Persistencia (historial de precios).
6. El Servicio de Búsqueda delega en el Servicio de Recomendación la identificación de la mejor opción.
7. El Servicio de Recomendación devuelve la opción recomendada.
8. El resultado (comparación + recomendación) se devuelve al jugador a través del Adaptador Web/API.

El Servicio de Búsqueda delega en el Adaptador de Tiendas Digitales sin conocer cuántas ni cuáles tiendas se consultan (mantenibilidad); la respuesta depende del tiempo de las tiendas más lentas, lo que motiva el límite de 3 s p95 y el manejo de fallos del escenario 6.2.

---

## 6.2 Escenario: Fallo de una fuente externa de precios
> **Nota:** Este escenario representa el comportamiento previsto para el aislamiento de fallos entre fuentes externas. En el corte vertical actual se encuentra implementada la integración con Steam; las demás fuentes se representan como extensiones de la arquitectura.

Corresponde al escenario de disponibilidad documentado en `docs/escenarios.md` (respuesta ante fallo de fuente externa, ≤ 5 s).

```mermaid
sequenceDiagram
    participant Jugador
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

**Explicación:**

1. El jugador busca un videojuego desde el Adaptador Web/API, igual que en el escenario 6.1.
2. El Servicio de Búsqueda solicita precios al Adaptador de Tiendas Digitales.
3. El Adaptador de Tiendas Digitales reparte la consulta entre los sub-adaptadores correspondientes (Steam, Epic, etc.).
4. El sub-adaptador Steam falla (timeout o error de la fuente externa).
5. El sub-adaptador Epic responde correctamente.
6. El Adaptador de Tiendas Digitales descarta el resultado fallido sin detener la respuesta global.
7. El resultado se entrega con los precios disponibles y un aviso indicando qué fuente no respondió.
8. El jugador recibe la comparación posible junto con la advertencia.

Este comportamiento materializa en tiempo de ejecución la restricción 2.3/2.4 (disponibilidad ante fallo de fuente externa) y la decisión arquitectónica de aislamiento de dependencias externas (Sección 4).

---

## 6.3 Escenario: Estimación de compatibilidad y rendimiento en PC
> **Nota:** Este escenario representa el flujo de ejecución previsto para la funcionalidad de compatibilidad y rendimiento. Esta funcionalidad forma parte de la arquitectura objetivo, pero no del corte vertical actualmente implementado.

Corresponde al escenario de calidad documentado en `docs/escenarios.md` (estimación de compatibilidad/rendimiento, ≤ 5 s p95).

```mermaid
sequenceDiagram
    participant Jugador
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

**Explicación:**

1. El jugador solicita la compatibilidad de un videojuego para su PC.
2. El Adaptador Web/API invoca el puerto de entrada del Servicio de Estimación de Compatibilidad.
3. El servicio solicita los requisitos del videojuego al Adaptador de Proveedor de Información.
4. El adaptador devuelve los requisitos mínimos/recomendados.
5. El servicio solicita las especificaciones del dispositivo registradas por el usuario al Adaptador de Persistencia.
6. El adaptador devuelve las especificaciones almacenadas.
7. El servicio compara especificaciones contra requisitos.
8. El resultado (compatible / rendimiento estimado) se devuelve al jugador.

El Servicio de Estimación de Compatibilidad depende únicamente de los puertos de información y persistencia, no de la implementación concreta del proveedor externo, lo que permite sustituir la fuente de datos sin afectar la lógica de comparación (mantenibilidad, ver Sección 5.2.1).

## 6.4 Escenario: una fuente lenta bajo carga (E6)

```mermaid
sequenceDiagram
    participant U as Usuario
    participant API as FastAPI /games/search
    participant C as CombinedGameRepository
    participant S as Steam (primaria)
    participant K as CheapShark (secundaria)

    U->>API: GET /games/search?q=...
    API->>C: search(query)
    par en paralelo
        C->>S: search(query)
        S-->>C: juegos y precios
    and
        C->>K: search(query), en un hilo aparte
    end
    Note over C,K: espera a CheapShark como máximo 3 s desde que lanzó la consulta
    alt responde dentro del plazo
        K-->>C: precios de tiendas de PC
        C-->>API: juegos con todas las tiendas
    else vence el plazo o falla
        C-->>API: juegos con unavailable_sources = [CheapShark]
        Note over K: el hilo abandonado termina por su timeout HTTP de 5 s
    end
    API-->>U: 200 con la lista de juegos
```

La búsqueda es síncrona y no usa cola. El mismo mecanismo se aplica a PlayStation en el combinador externo. El endpoint registra el evento `source_unavailable` y cuenta la búsqueda en `drift_source_unavailable_total`. Medición antes y después en [E6](../evidencias/e6-degradacion-bajo-carga.md); decisión en [ADR-0008](../adr/0008-persistencia-ejecucion-y-degradacion-de-fuentes.md).

## 6.5 Escenario: búsqueda con una fuente caída y copia de respaldo (noviembre de 2026)

Amplía 6.2 con la copia de respaldo de ADR-0015. Ejemplo: la tienda de Xbox no responde dentro de su plazo.

```mermaid
sequenceDiagram
    autonumber
    actor J as Jugador
    participant W as Página web
    participant A as API (SearchGames)
    participant C as CombinedGameRepository
    participant S as StaleFallbackGameRepository (Xbox)
    participant X as Tienda de Xbox
    participant DB as PostgreSQL (source_snapshot)

    J->>W: Busca «Hades»
    W->>A: GET /api/games/search?q=Hades
    A->>C: search("Hades")
    par Steam, PC, PlayStation y Xbox a la vez
        C->>S: search("Hades")
        S->>DB: ¿copia de menos de 15 min?
        DB-->>S: no
        S->>X: HTTPS + JSON (plazo 3 s)
        X--xS: sin respuesta a tiempo
        S->>DB: última copia (≤ 72 h)
        DB-->>S: copia de hace 2 h
        S-->>C: precios de la copia + fecha
    end
    C-->>A: juegos unidos, cached_sources = [Xbox]
    A-->>W: 200 JSON con precios y aviso
    W-->>J: Resultados con «precio de Xbox de hace 2 h»
```

Si no hubiera copia, Xbox iría a `unavailable_sources` y la respuesta seguiría con las demás fuentes. Si PostgreSQL no responde, `ResilientSourceSnapshotStore` usa la copia en memoria y deja de llamar a la base durante 30 s. Pruebas: `test_copia_de_respaldo.py`, `test_source_degradation.py`.

## 6.6 Escenario: inicio de sesión con Google (ADR-0017)

```mermaid
sequenceDiagram
    autonumber
    actor J as Jugador
    participant W as Página web
    participant A as API (rutas de cuentas)
    participant G as Google
    participant DB as PostgreSQL

    J->>W: «Iniciar sesión con Google»
    W->>A: GET /api/auth/google/login
    A-->>J: 302 a Google + cookies drift_login_state y drift_login_nonce (10 min)
    J->>G: Elige su cuenta y acepta openid, email y profile
    G-->>J: 302 a /api/auth/google/callback?code=…&state=…
    J->>A: GET /api/auth/google/callback
    A->>A: compara state con la cookie
    A->>G: canjea el código (HTTPS + JSON)
    G-->>A: id_token
    A->>A: valida emisor, destinatario, vencimiento, nonce y correo verificado
    A->>DB: crea o actualiza app_user y guarda la huella SHA-256 de la sesión
    A-->>J: 302 a la página con ?login=ok + cookie drift_session (HttpOnly, SameSite=Lax, Secure)
    W->>A: GET /api/auth/me (con la cookie)
    A-->>W: nombre y correo
```

Si el `state` no coincide o el código es rechazado, se vuelve con `?login=error` y el log registra `login_rejected` sin el token. Si Google no responde, el inicio de sesión responde «no disponible» y quien ya tiene sesión no se ve afectado. Pruebas: `test_cuentas.py`. **El recorrido con una cuenta real solo se ha probado en `localhost`** ([§11.11](arc42-11-riesgos-y-deuda-tecnica.md)).

## 6.7 Escenario: alertas de los favoritos al entrar (ADR-0021)

```mermaid
sequenceDiagram
    autonumber
    participant W as Página web
    participant A as API (CheckFavoriteAlerts)
    participant DB as PostgreSQL (user_favorite)
    participant P as StoreCurrentPriceSource
    participant S as Steam
    participant I as IsThereAnyDeal

    W->>A: GET /api/favorites/alerts (cookie de sesión)
    A->>DB: favoritos del usuario con precio guardado y objetivo
    A->>P: precio de hoy de esos juegos (caché 1 h)
    P->>S: precio en Colombia
    P->>I: precios de tiendas de PC (dos llamadas)
    P-->>A: mejor precio de PC por juego
    A->>A: price_alerts: ¿llegó al objetivo o bajó 5 % o más?
    A-->>W: estado por favorito y alertas
```

No hay procesos en segundo plano ni correos: si la persona no entra, no se revisa. Los juegos que solo están en consola no se revisan. Pruebas: `test_alertas_de_precio.py`, `test_favoritos.py`.
