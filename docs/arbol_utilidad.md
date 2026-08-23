# Árbol de Utilidad — DRIFT

El árbol de utilidad organiza los atributos de calidad de DRIFT según su prioridad y relaciona cada uno con escenarios evaluados mediante **impacto** y **riesgo**. 

La prioridad se establece de acuerdo con los objetivos de calidad definidos en la sección 1 de arc42.

```mermaid
flowchart RL
    A["Utilidad de DRIFT"]

    A --> B["1. Mantenibilidad"]
    A --> C["2. Rendimiento"]
    A --> D["3. Disponibilidad"]
    A --> E["4. Usabilidad"]
    A --> F["5. Compatibilidad"]

    B --> B1["[Impacto: Alto | Riesgo: Alto]<br/>Agregar una nueva plataforma sin modificar el núcleo"]
    B --> B2["[Impacto: Alto | Riesgo: Medio]<br/>Modificar una fuente externa sin afectar el sistema"]

    C --> C1["[Impacto: Alto | Riesgo: Medio]<br/>Consulta de precios dentro del tiempo establecido"]

    D --> D1["[Impacto: Alto | Riesgo: Alto]<br/>Mantener el servicio ante fallos de fuentes externas"]

    E --> E1["[Impacto: Medio | Riesgo: Bajo]<br/>Permitir comparar precios de forma sencilla"]

    F --> F1["[Impacto: Medio | Riesgo: Medio]<br/>Estimar el rendimiento del videojuego en PC"]
