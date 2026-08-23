# C4 — Diagrama de Contexto de DRIFT
El diagrama de contexto representa a DRIFT como el sistema principal y muestra
los usuarios y sistemas externos que interactúan con él, permitiendo
identificar de forma clara los límites del sistema y sus relaciones externas.

```mermaid
flowchart LR
    U["Usuario / Jugador<br/><br/>[Persona]<br/>Busca y compara videojuegos<br/>y sus precios"]
    A["Administrador<br/><br/>[Persona]<br/>Gestiona información y<br/>configuración del sistema"]
    D["DRIFT<br/><br/>[Sistema de Software]<br/>Sistema web para comparar<br/>precios de videojuegos<br/>entre diferentes plataformas"]
    T["Tiendas digitales<br/><br/>[Sistema Externo]<br/>Steam, Epic Games Store,<br/>PlayStation Store,<br/>Xbox Store, Nintendo"]
    P["Proveedores externos de información<br/><br/>[Sistema Externo]<br/>Proporcionan datos de videojuegos,<br/>precios, plataformas y disponibilidad"]

    U -->|"Busca videojuegos"| D
    D -->|"Muestra precios e información"| U
    A -->|"Administra el sistema"| D
    D -->|"Presenta información"| A
    D -->|"Consulta precios"| T
    T -->|"Devuelve precios y disponibilidad"| D
    D -->|"Solicita información"| P
    P -->|"Entrega datos"| D

    classDef person fill:#08427b,stroke:#052e56,color:#ffffff,rx:20,ry:20
    classDef system fill:#1168bd,stroke:#0b4884,color:#ffffff
    classDef external fill:#999999,stroke:#6b6b6b,color:#ffffff

    class U,A person
    class D system
    class T,P external

    subgraph Leyenda["Leyenda"]
        direction LR
        L1["Persona"]:::person
        L2["Sistema de Software<br/>(en estudio)"]:::system
        L3["Sistema Externo"]:::external
    end
```
