# Correcciones · Revisión del repositorio DRIFT

## Propósito

Este documento registra la revisión realizada por el equipo DRIFT sobre las observaciones generadas durante las revisiones semanales del repositorio. 

Las observaciones fueron contrastadas con el estado real del repositorio, su documentación, código, pruebas y configuración. Para cada hallazgo se determina si:

- estaba pendiente y fue corregido;
- ya estaba presente en el repositorio y la observación no correspondía;
- estaba parcialmente resuelto y requería ajustes;
- o continúa pendiente.

El objetivo es mantener trazabilidad entre el feedback recibido y la evidencia disponible en el repositorio.

---

## Revisión del feedback

### 1. `docs/aspectos.md` sin tabla de 8 columnas ni trazabilidad

**Observación recibida:**

> `docs/aspectos.md` en prosa, sin la tabla de 8 columnas ni enlaces a escenarios ni al ADR.

**Estado:** Corregido.

**Verificación:**

Se revisó `docs/aspectos.md` y se incorporó la estructura solicitada para los atributos de calidad, incluyendo la trazabilidad correspondiente hacia los escenarios E1–E5 y la decisión arquitectónica documentada en ADR-0002.

**Evidencia:**

- [`docs/aspectos.md`](docs/aspectos.md)
- [`docs/escenarios.md`](docs/escenarios.md)
- [`docs/adr/0002-arquitectura-base.md`](docs/adr/0002-arquitectura-base.md)

---

### 2. Ficha del problema sin tensiones de calidad

**Observación recibida:**

> Ficha del problema sin tensiones de calidad.

**Estado:** Corregido.

**Verificación:**

Se revisó la ficha del problema y se incorporaron las tensiones entre los objetivos de calidad relevantes para DRIFT, especialmente mantenibilidad, rendimiento, disponibilidad, usabilidad y compatibilidad.

**Evidencia:**

- [`docs/aspectos.md`](docs/aspectos.md)
- [`docs/arc42/arc42_1_introduccion_objetivos.md`](docs/arc42/arc42_1_introduccion_objetivos.md)

---

### 3. Desbalance de contribución

**Observación recibida:**

> Desbalance de contribución en el periodo (51 vs 9 commits en S3).

**Estado:** Observación válida.

**Verificación:**

El repositorio efectivamente presenta una distribución desigual de commits entre los integrantes durante el periodo indicado. Este hallazgo no corresponde a una ausencia documental o técnica que pueda considerarse corregida mediante un cambio en la arquitectura.

**Evidencia:**

- Historial de Git del repositorio.
- Distribución de contribuciones registrada en la planilla de equipo.

**Acción:**

El equipo debe continuar equilibrando la participación y mantener evidencia de las contribuciones de todos los integrantes durante los siguientes periodos.

---

### 4. README con arranque contradictorio

**Observación recibida:**

> README con arranque contradictorio (mvn sin pom.xml / uvicorn solo backend) y sin comando único.

**Estado:** Corregido.

**Verificación:**

El README fue actualizado para reflejar el stack tecnológico real del proyecto. Se eliminó la referencia incorrecta a Maven/Spring Boot y se documentó el arranque del backend mediante FastAPI/Uvicorn y del frontend mediante Next.js.

**Evidencia:**

```bash
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
