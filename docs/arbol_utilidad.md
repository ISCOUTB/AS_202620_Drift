# Árbol de Utilidad — DRIFT

El árbol de utilidad de DRIFT permite organizar y visualizar los aspectos de calidad que consideramos más importantes para el funcionamiento del sistema. A partir de la utilidad general de la plataforma, se desglosan características como el rendimiento, la mantenibilidad, la disponibilidad, la usabilidad y la compatibilidad. Esto nos ayuda a relacionar cada aspecto con objetivos más concretos y a tener una visión clara de qué debe cumplir DRIFT para ofrecer una buena experiencia a los usuarios.

```mermaid
flowchart TD
    A["Utilidad de DRIFT"] --> B["Mantenibilidad"]
    A --> C["Rendimiento"]
    A --> D["Disponibilidad"]
    A --> E["Usabilidad"]
    A --> F["Compatibilidad"]

    B --> B1["Extensibilidad"]
    B --> B2["Modificabilidad"]
    B1 --> B11["Agregar nuevas tiendas sin afectar funcionalidades existentes"]
    B2 --> B21["Realizar cambios minimizando el impacto en el sistema"]

    C --> C1["Tiempo de búsqueda"]
    C --> C2["Tiempo de consulta"]
    C1 --> C11["Objetivo: ≤ 3 s en p95"]
    C2 --> C21["Objetivo: ≤ 3 s en p95"]

    D --> D1["Disponibilidad de fuentes externas"]
    D --> D2["Recuperación ante fallos"]
    D1 --> D11["Mantener el servicio ante fallos temporales"]
    D2 --> D21["Proporcionar una respuesta controlada ante fallos"]

    E --> E1["Facilidad de uso"]
    E --> E2["Claridad de información"]
    E1 --> E11["Permitir comparar precios sin conocimientos técnicos"]
    E2 --> E21["Presentar precios y plataformas de forma comprensible"]

    F --> F1["Compatibilidad con dispositivos"]
    F1 --> F11["Funcionamiento adecuado en los dispositivos contemplados"]
