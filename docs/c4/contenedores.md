# C4 — Diagrama de Contenedores de DRIFT

El diagrama de contenedores representa la descomposición interna del sistema DRIFT. Cada contenedor representa una unidad principal de ejecución o responsabilidad dentro del sistema y muestra cómo se relaciona con los actores y sistemas externos definidos en el diagrama de contexto.

```mermaid
flowchart LR

    %% Actores externos
    U["Jugador<br/><br/>[Persona]<br/>Busca y compara videojuegos"]

    A["Administrador<br/><br/>[Persona]<br/>Gestiona información y configuración"]

    %% Sistema DRIFT
    subgraph DRIFT["DRIFT"]

        WEB["Web / API<br/><br/>[Contenedor]<br/>Expone la interfaz HTTP y recibe<br/>las solicitudes de los usuarios"]

        APP["Aplicación / Casos de uso<br/><br/>[Contenedor]<br/>Coordina las operaciones de búsqueda,<br/>comparación, recomendación y compatibilidad"]

        DOM["Dominio<br/><br/>[Contenedor]<br/>Contiene las reglas de negocio,<br/>modelos y puertos de la arquitectura"]

        EXT["Adaptadores de fuentes externas<br/><br/>[Contenedor]<br/>Integra las APIs de tiendas y<br/>proveedores externos"]

        DB["Persistencia<br/><br/>[Contenedor]<br/>Almacena y recupera precios,<br/>videojuegos e información necesaria"]
    end

    %% Sistemas externos
    T["Tiendas digitales<br/><br/>[Sistema Externo]<br/>Steam, Epic Games Store,<br/>PlayStation Store, Xbox Store"]

    P["Proveedor de información de videojuegos<br/><br/>[Sistema Externo]<br/>Información, requisitos y características<br/>de los videojuegos"]

    %% Relaciones
    U -->|"Consulta videojuegos y precios"| WEB
    A -->|"Administra información"| WEB

    WEB -->|"Invoca casos de uso"| APP
    APP -->|"Utiliza reglas de negocio"| DOM
    DOM -->|"Consulta fuentes externas mediante puertos"| EXT
    DOM -->|"Consulta y almacena información mediante puertos"| DB

    EXT -->|"Consulta precios y disponibilidad"| T
    EXT -->|"Consulta información de videojuegos"| P

    %% Estilos
    classDef person fill:#08427b,stroke:#052e56,color:#ffffff,rx:20,ry:20
    classDef container fill:#438dd5,stroke:#2e6295,color:#ffffff
    classDef external fill:#999999,stroke:#6b6b6b,color:#ffffff

    class U,A person
    class WEB,APP,DOM,EXT,DB container
    class T,P external

    %% Leyenda
    subgraph Leyenda["Leyenda"]
        direction LR
        L1["Persona"]:::person
        L2["Contenedor"]:::container
        L3["Sistema Externo"]:::external
    end
```

Coherencia con la arquitectura

La descomposición corresponde a la Arquitectura Hexagonal seleccionada en el ADR-0001. El dominio se mantiene aislado de los detalles de infraestructura y las integraciones externas se realizan mediante adaptadores.

Esta separación permite incorporar nuevas fuentes externas sin modificar directamente las reglas de negocio, contribuyendo al atributo de calidad prioritario de mantenibilidad.

El nivel 2 no descompone todavía los servicios internos de búsqueda, recomendación y compatibilidad. Estos corresponden a una vista de mayor detalle que puede documentarse posteriormente como nivel 3.
