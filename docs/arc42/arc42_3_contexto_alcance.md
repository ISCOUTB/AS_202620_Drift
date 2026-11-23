# 3. Contexto y alcance

## 3.1 Contexto del sistema

DRIFT es una plataforma web que permite a los jugadores consultar y comparar información de videojuegos proveniente de diferentes tiendas digitales y fuentes de información.

El sistema se encuentra dentro de un entorno en el que intervienen usuarios, administradores y diferentes fuentes externas de información.

### Actores y sistemas externos

| Actor / sistema externo | Relación con DRIFT |
|---|---|
| **Jugador / usuario** | Utiliza DRIFT para buscar videojuegos, comparar precios, consultar descuentos, revisar plataformas disponibles, consultar historial de precios y conocer la compatibilidad o rendimiento estimado en PC. |
| **Administrador del sistema** | Supervisa y mantiene el funcionamiento de DRIFT y de las fuentes de información utilizadas por el sistema. |
| **Tiendas digitales** | Proporcionan información sobre precios, descuentos, disponibilidad y ofertas de videojuegos. |
| **Proveedor de información de videojuegos** | Proporciona información relacionada con los videojuegos, incluyendo características y requisitos necesarios para estimar su funcionamiento en PC. |

### Flujo general de información

El contexto general de DRIFT puede describirse de la siguiente manera:

1. El **jugador** realiza una búsqueda o consulta dentro de DRIFT.
2. DRIFT solicita y procesa la información necesaria de las diferentes fuentes externas.
3. Las **tiendas digitales** proporcionan información sobre precios, descuentos y disponibilidad.
4. El **proveedor de información de videojuegos** proporciona información sobre las características y requisitos de los videojuegos.
5. DRIFT integra la información obtenida y la presenta al jugador para facilitar la comparación y la toma de decisiones.
6. En caso de que una fuente externa no esté disponible, DRIFT debe continuar utilizando la información disponible de las demás fuentes.

---

## 3.2 Alcance y límites del sistema

### Dentro del alcance de DRIFT

Las principales responsabilidades de DRIFT son:

- Buscar videojuegos.
- Consultar y comparar precios entre diferentes tiendas digitales.
- Mostrar descuentos.
- Mostrar las plataformas en las que está disponible un videojuego.
- Comparar las opciones disponibles para ayudar al usuario a identificar la alternativa más conveniente.
- Registrar las especificaciones relevantes del dispositivo PC del usuario.
- Comparar las especificaciones del dispositivo con los requisitos de un videojuego.
- Estimar la compatibilidad y el rendimiento esperado de un videojuego en PC.
- Integrar información proveniente de diferentes fuentes externas.
- Mantener las consultas disponibles cuando una fuente externa de información no responda.

### Fuera del alcance de DRIFT

Las siguientes responsabilidades pertenecen a sistemas o servicios externos:

- Gestionar directamente las tiendas digitales.
- Procesar los pagos de las compras de videojuegos.
- Realizar la venta de videojuegos.
- Administrar los catálogos internos de las tiendas digitales.
- Definir los precios, descuentos u ofertas de las tiendas.
- Proporcionar directamente los requisitos oficiales de cada videojuego.
- Ejecutar físicamente los videojuegos en el dispositivo del usuario.

DRIFT funciona como una plataforma de consulta, comparación y recomendación, pero no reemplaza a las tiendas digitales ni a los proveedores externos de información.

---

## 3.3 Interfaces externas

DRIFT requiere intercambiar información con diferentes fuentes externas para cumplir sus funciones principales.

| Interfaz / fuente | Información intercambiada |
|---|---|
| **Tiendas digitales** | Precios, descuentos, disponibilidad y ofertas de videojuegos. |
| **Proveedor de información de videojuegos** | Información del videojuego, características y requisitos de funcionamiento. |
| **Usuario** | Búsquedas, filtros, consultas y especificaciones del dispositivo PC. |
| **Administrador** | Información y acciones relacionadas con la supervisión y mantenimiento del sistema. |

Estas interfaces representan el límite entre DRIFT y los elementos externos que proporcionan o consumen información.


## 3.4 Contexto vigente (actualización de noviembre de 2026)

Las secciones 3.1 a 3.3 nombran las fuentes por su categoría («tiendas digitales», «proveedor de información»). Esta tabla concreta qué sistema externo cumple cada papel en el código actual; el diagrama está en el [C4 nivel 1](../c4/contexto.md).

| Papel de 3.1 | Sistema concreto | Interfaz | Adaptador |
|---|---|---|---|
| Jugador / usuario | Persona con o sin sesión | HTTPS, página web | `frontend/` |
| Administrador del sistema | Integrante del equipo con el token administrativo | HTTPS + JSON, `Authorization: Bearer` | `main.py` (rutas administrativas, ADR-0011) |
| Tiendas digitales | Steam, IsThereAnyDeal (o CheapShark sin llave), PlayStation Store, tienda de Xbox | HTTPS + JSON | `backend/app/infrastructure/external/` |
| Proveedor de información de videojuegos | Steam (requisitos, fichas, más vendidos) y la copia privada de puntajes 3DMark | HTTPS + JSON | `external/steam/`, `json_hardware_benchmark_repository.py` |
| *(nuevo)* Proveedor de identidad | Google (OpenID Connect) | HTTPS + JSON, OAuth 2.0 | `external/google/` (ADR-0017) |
| *(nuevo)* Tasa de cambio | open.er-api.com | HTTPS + JSON | `external/exchange/` |

El contrato de la interfaz propia de DRIFT (24 rutas) está en [`docs/api/drift/openapi.yaml`](../api/drift/openapi.yaml), versión 1.8.0, y se prueba con Schemathesis en el CI.
