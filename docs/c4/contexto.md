# C4 — Nivel 1: diagrama de contexto de DRIFT

> **Vista vigente.** Revisada el 22 de noviembre de 2026 contra `master` en `a0e18f9` (PR #62 y #65 integrados). Describe el sistema que está en la rama principal, no planes. Las versiones anteriores quedan en el historial de git de este archivo.

## Objetivo

El diagrama de contexto muestra a DRIFT como una sola caja: una plataforma web para buscar videojuegos, comparar su precio entre tiendas de PC y de consola, ver cómo se ha movido ese precio, recibir una recomendación de compra y saber si un juego corre en el PC del usuario. Identifica a quienes la usan y los sistemas externos de los que depende.

## Diagrama de contexto

```mermaid
flowchart LR
    U["Jugador<br/>[Persona]<br/>Busca juegos, compara precios,<br/>guarda favoritos y dispositivos"]
    A["Integrante del equipo<br/>[Persona]<br/>Sincroniza catálogo y puntajes;<br/>lee las métricas"]

    D["DRIFT<br/>[Sistema de software]<br/>Compara precios de videojuegos<br/>entre tiendas y estima<br/>compatibilidad de PC"]

    S["Steam<br/>[Sistema externo]<br/>Búsqueda, precio en COP,<br/>requisitos, más vendidos"]
    I["IsThereAnyDeal<br/>[Sistema externo]<br/>Precios de tiendas de PC<br/>e historial de 12 meses"]
    C["CheapShark<br/>[Sistema externo]<br/>Tiendas de PC sin llave<br/>de IsThereAnyDeal"]
    P["PlayStation Store<br/>[Sistema externo]<br/>Precio en la tienda<br/>de Colombia"]
    X["Tienda de Xbox<br/>[Sistema externo]<br/>Precio en COP de la<br/>tienda de Colombia"]
    G["Google<br/>[Sistema externo]<br/>Proveedor de identidad<br/>OAuth 2.0 / OpenID Connect"]
    F["open.er-api.com<br/>[Sistema externo]<br/>Tasa USD → COP"]
    B["Copia privada de puntajes<br/>[Sistema externo]<br/>JSON de puntajes 3DMark<br/>de GPU y CPU"]

    U -->|"Usa la página<br/>[HTTPS]"| D
    A -->|"Operaciones administrativas<br/>[HTTPS + JSON, Bearer token]"| D
    U -.->|"Inicia sesión en la página<br/>de Google [HTTPS]"| G

    D -->|"Busca juegos, precios,<br/>requisitos, destacados<br/>[HTTPS + JSON]"| S
    D -->|"Pide precios e historial<br/>[HTTPS + JSON, API key]"| I
    D -.->|"Pide precios si no hay<br/>llave de ITAD [HTTPS + JSON]"| C
    D -->|"Busca juegos y precios<br/>[HTTPS + JSON]"| P
    D -->|"Busca juegos y precios<br/>[HTTPS + JSON]"| X
    D -->|"Cambia el código por la<br/>identidad [HTTPS + JSON, OIDC]"| G
    D -->|"Consulta la tasa<br/>[HTTPS + JSON]"| F
    D -.->|"Carga los puntajes<br/>[HTTPS + JSON]"| B

    subgraph LEYENDA["Leyenda"]
        direction LR
        L1["Persona"]
        L2["Sistema en alcance"]
        L3["Sistema externo"]
        L4["── siempre · - - - solo en algunos casos"]
    end

    classDef person fill:#08427b,stroke:#052e56,color:#ffffff
    classDef system fill:#1168bd,stroke:#0b4884,color:#ffffff
    classDef external fill:#999999,stroke:#6b6b6b,color:#ffffff
    classDef note fill:#ffffff,stroke:#999999,color:#333333

    class U,A,L1 person
    class D,L2 system
    class S,I,C,P,X,G,F,B,L3 external
    class L4 note
```

Las cajas azul oscuro son personas, la azul es DRIFT y las grises son sistemas externos. Una línea continua es una relación que ocurre siempre que se usa la función; una punteada, una que solo ocurre en algunos casos.

## Elementos del diagrama

| Elemento | Tipo | Descripción | Dónde está en el código |
|---|---|---|---|
| Jugador | Persona | Usa DRIFT sin registrarse. Si inicia sesión con Google puede guardar varios dispositivos (PC y consolas) y juegos favoritos con un precio objetivo. | `frontend/ui/components/` |
| Integrante del equipo | Persona | Con el token administrativo sincroniza el catálogo de PlayStation, recarga los puntajes de hardware y lee las métricas (ADR-0011, ADR-0018). | `backend/app/main.py` (`/games/sync/playstation`, `/hardware/benchmarks/sync`, `/metrics`) |
| DRIFT | Sistema en alcance | Página web, API y base de datos. Su interior está en el [nivel 2](contenedores.md). | `frontend/`, `backend/`, `deploy/compose.lab.yaml` |
| Steam | Sistema externo | Fuente principal: búsqueda, precio en pesos de Colombia, requisitos de PC, precio regional para el historial, los más vendidos de la portada y la página «Explorar». | `backend/app/infrastructure/external/steam/` |
| IsThereAnyDeal | Sistema externo | Precios de las demás tiendas de PC y el historial de 12 meses. Exige llave (`DRIFT_ITAD_API_KEY`) y limita las llamadas; DRIFT se fija un tope de 900 cada 5 minutos (ADR-0016). | `backend/app/infrastructure/external/isthereanydeal/` |
| CheapShark | Sistema externo | Tiendas de PC cuando no hay llave de IsThereAnyDeal. No ofrece historial. | `backend/app/infrastructure/external/cheapshark/` |
| PlayStation Store | Sistema externo | Precio de la versión de PlayStation en la tienda de Colombia, que cobra en dólares. | `backend/app/infrastructure/external/playstation/` |
| Tienda de Xbox | Sistema externo | Precio en pesos de la versión de Xbox. Son los buscadores y el catálogo de la tienda web de Microsoft, sin contrato publicado. | `backend/app/infrastructure/external/xbox/` |
| Google | Sistema externo | Proveedor de identidad (OpenID Connect). DRIFT no guarda contraseñas ni tokens de Google (ADR-0017). | `backend/app/infrastructure/external/google/` |
| open.er-api.com | Sistema externo | Tasa para convertir a pesos los precios que llegan en dólares. Con fallo, se usa `USD_TO_COP_RATE`. | `backend/app/infrastructure/external/exchange/` |
| Copia privada de puntajes | Sistema externo | Dos archivos JSON con puntajes de 3DMark en direcciones privadas (`DRIFT_GPU_BENCHMARKS_URL`, `DRIFT_CPU_BENCHMARKS_URL`). DRIFT los carga en su base de datos (ADR-0018). | `backend/app/infrastructure/persistence/json_hardware_benchmark_repository.py` |

## Relaciones principales

| Origen | Destino | Protocolo | Cuándo |
|---|---|---|---|
| Jugador | DRIFT | HTTPS | Siempre: búsqueda, filtro por plataforma, historial, compatibilidad, recomendación, favoritos. |
| Jugador | Google | HTTPS | Solo al iniciar sesión: escribe su contraseña en la página de Google, nunca en DRIFT. |
| Integrante del equipo | DRIFT | HTTPS + JSON, `Authorization: Bearer` | Solo para operaciones administrativas. |
| DRIFT | Steam, IsThereAnyDeal (o CheapShark), PlayStation Store, Tienda de Xbox | HTTPS + JSON | En cada búsqueda consulta las cuatro a la vez, con un plazo por fuente. Si una falla, responde con su última copia guardada o avisa que no está disponible (ADR-0015). |
| DRIFT | Google | HTTPS + JSON (OIDC) | Al volver del inicio de sesión: cambia el código por el `id_token`. |
| DRIFT | open.er-api.com | HTTPS + JSON | Cuando necesita convertir y su caché de 12 horas venció. |
| DRIFT | Copia privada de puntajes | HTTPS + JSON | Solo en el primer arranque con la base vacía y cuando el equipo pide recargar los puntajes. |

## Alcance y límites

- Este diagrama no muestra el interior de DRIFT: los contenedores están en el [nivel 2](contenedores.md) y los componentes en el [nivel 3](componentes.md).
- Todas las fuentes de precios se consultan en el momento de la búsqueda. DRIFT no descarga catálogos completos, salvo una página del catálogo de PlayStation cuando el equipo lo pide.
- No hay envío de correos, pagos ni integración con cuentas de las tiendas: el usuario compra en la página de cada tienda, que DRIFT abre en una pestaña nueva.
