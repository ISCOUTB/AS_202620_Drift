# Drift — Comparador Inteligente de Videojuegos

Proyecto del curso **Arquitectura de Software** (AS_202620) — Universidad Tecnológica de Bolívar.

## ¿Qué es DRIFT?

**DRIFT** es una plataforma web orientada a jugadores que buscan tomar mejores decisiones al comprar videojuegos. El sistema reúne información de diferentes plataformas digitales para comparar precios, descuentos e historial de ofertas, teniendo en cuenta además las plataformas disponibles para cada usuario y el rendimiento esperado de sus dispositivos.

La definición detallada de la problemática se encuentra en [`docs/ficha_problema.md`](docs/ficha_problema.md).

## Aspecto de calidad declarado

Para DRIFT se prioriza la **mantenibilidad**, buscando que el sistema pueda incorporar nuevas plataformas, fuentes de información y funcionalidades sin generar cambios importantes en los demás componentes.

La justificación y definición del aspecto seleccionado se encuentra en [`docs/aspectos.md`](docs/aspectos.md).

---

## Equipo de desarrollo

- Mauricio Fernández Espinosa
- Jerry Buelvas Mejía
- Luis Pérez Diaz
- Joshua Reyes Leones

## Organización del proyecto

```text
docs/  
├── Escenarios.md  
├── aspectos.md  
├── ficha_problema.md  
├── ia.md  
├── interesados.md  
```

### Documentación


| Archivo             | Contenido                                               |
|---------------------|---------------------------------------------------------|
| `ficha_problema.md` | Definición y análisis de la problemática             |
| `aspectos.md`       | Aspecto de calidad seleccionado para la arquitectura    |
| `interesados.md`    | Identificación y análisis de los interesados de DRIFT |
| `Escenarios.md`     | Escenarios de calidad medibles de DRIFT                 |
| `ia.md`             | Registro y criterios de uso de herramientas de IA       |

---

### Documentación de arquitectura — arc42

La documentación de arquitectura de DRIFT se desarrolla siguiendo el modelo **arc42**. En ella se describen el propósito del sistema, sus objetivos de calidad, las restricciones arquitectónicas y el contexto y alcance del sistema.

| Sección | Contenido | Documento |
|---|---|---|
| **1. Introducción y objetivos** | Propósito, alcance, objetivos de calidad e interesados. | [`arc42_1_introduccion_objetivos.md`](docs/arc42_1_introduccion_objetivos.md) |
| **2. Restricciones** | Restricciones que condicionan la arquitectura y su justificación. | [`arc42_2_restricciones.md`](docs/arc42_2_restricciones.md) |
| **3. Contexto y alcance** | Contexto del sistema, actores, sistemas externos, límites e interfaces. | [`arc42_3_contexto_alcance.md`](docs/arc42_3_contexto_alcance.md) |
| **4. Solucion Arquitectonica** | Principales decisiones arquitectónicas de DRIFT. | [`arc42_4_solucion_arquitectonica.md`](docs/arc42_4_solucion_arquitectonica.md) |


---

## Interesados y escenarios de calidad

El proyecto incluye el análisis de los interesados de DRIFT y sus principales preocupaciones relacionadas con la calidad del sistema.

El **mapa de interesados** identifica los actores relevantes para la arquitectura y sus prioridades.

Los **escenarios medibles** traducen estas preocupaciones en situaciones verificables, especificando fuente, estímulo, artefacto, entorno, respuesta y una medida cuantificable.

La documentación correspondiente se encuentra en:

- [`docs/interesados.md`](docs/interesados.md)
- [`docs/Escenarios.md`](docs/Escenarios.md)

Los escenarios actuales contemplan principalmente:

- Comparación de precios.
- Consulta de información de videojuegos.
- Identificación de la opción más conveniente.
- Estimación de rendimiento y compatibilidad en PC.
- Disponibilidad ante fallos de una fuente externa de precios.

---

## Inteligencia Artificial

La IA forma parte de la propuesta de DRIFT como apoyo para la generación de recomendaciones personalizadas y el análisis de información relacionada con precios, plataformas y rendimiento.El uso de estas herramientas será registrado y justificado durante el desarrollo en [`docs/ia.md`](docs/ia.md).

 
