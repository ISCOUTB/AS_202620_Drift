# Correcciones · Revisión del repositorio DRIFT

## Propósito

Este documento registra la revisión realizada por el equipo DRIFT sobre las observaciones recibidas durante las revisiones semanales del repositorio.

El objetivo es mantener trazabilidad entre el feedback, las correcciones realizadas y la evidencia disponible en el proyecto.

---

## 1. `docs/aspectos.md` sin tabla de 8 columnas ni trazabilidad

**Observación recibida:**

> `docs/aspectos.md` en prosa, sin la tabla de 8 columnas ni enlaces a escenarios ni al ADR.

**Estado:** Corregido.

**Verificación:**

Se completó la tabla de ocho columnas para los escenarios E1–E5. La tabla incluye atributo de calidad, escenario, componentes relacionados, ADR, implementación, evidencia y estado.

**Evidencia:**

- [`docs/aspectos.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/aspectos.md)
- [`docs/escenarios.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/escenarios.md)
- [`ADR-0002`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0002-adoptar-nextjs-fastapi-arquitectura-hexagonal.md)

---

## 2. Ficha del problema sin tensiones de calidad

**Observación recibida:**

> Ficha del problema sin tensiones de calidad.

**Estado:** Corregido.

**Verificación:**

La documentación registra tensiones entre mantenibilidad, rendimiento, disponibilidad, usabilidad y compatibilidad para el contexto de DRIFT.

**Evidencia:**

- [`docs/aspectos.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/aspectos.md)
- [`docs/arc42/arc42_1_introduccion_objetivos.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/arc42/arc42_1_introduccion_objetivos.md)

---

## 3. Desbalance de contribución

**Observación recibida:**

> Desbalance de contribución en el periodo (51 vs 9 commits en S3).

**Estado:** Observación válida.

**Verificación:**

El repositorio presentó una distribución desigual de commits durante el periodo indicado. Esta situación no se corrige mediante documentación o cambios de arquitectura.

**Acción:**

El equipo debe mantener una participación equilibrada y evidencia de las contribuciones de todos los integrantes en los siguientes periodos.

---

## 4. README con arranque contradictorio

**Observación recibida:**

> README con arranque contradictorio (mvn sin pom.xml / uvicorn solo backend) y sin comando único.

**Estado:** Corregido.

**Verificación:**

El README fue actualizado para reflejar el stack real del proyecto: FastAPI en el backend y Next.js en el frontend. Se eliminó la referencia incorrecta a Maven/Spring Boot.

El proyecto se inicia con un único comando desde la raíz: `python scripts/start.py`.

El script inicia la API en `http://localhost:8000` y el frontend en `http://localhost:3000`.

**Evidencia:**

- [`README.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/README.md)
- [`scripts/start.py`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/scripts/start.py)

---

## 5. Sin pipeline / evidencia de CI en verde

**Observación recibida:**

> Sin pipeline: prueba existe sin evidencia de verde.

**Estado:** Corregido y ampliado.

**Verificación:**

El repositorio cuenta con un workflow de integración continua en `.github/workflows/ci.yml`. El workflow ejecuta pruebas del backend, un smoke test del frontend conectado a la API y un análisis de calidad con SonarQube Cloud.

En la validación local más reciente:

- El backend aprobó 8 pruebas automatizadas.
- El frontend compiló correctamente con `npm run build`.
- La prueba de rendimiento con k6 cumplió el escenario E1 con p95 de 1.24 segundos bajo 50 usuarios virtuales.

SonarQube Cloud está configurado mediante `sonar-project.properties` y el secreto `SONAR_TOKEN`. La nueva ejecución del análisis ocurrirá en GitHub Actions cuando el equipo decida realizar el commit y push de estos cambios.

**Evidencia:**

- [`.github/workflows/ci.yml`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/.github/workflows/ci.yml)
- [`sonar-project.properties`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/sonar-project.properties)
- [`backend/tests`](https://github.com/ISCOUTB/AS_202620_Drift/tree/master/backend/tests)
- [`scripts/k6_baseline.js`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/scripts/k6_baseline.js)

---

## 6. Matriz de estilos sin referencia a E1–E5

**Observación recibida:**

> Matriz de estilos sin referencia a los escenarios E1–E5.

**Estado:** Corregido.

**Verificación:**

La matriz de estilos arquitectónicos relaciona las alternativas evaluadas con los escenarios de calidad E1–E5.

**Evidencia:**

- [`docs/matriz.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/matriz.md)
- [`docs/escenarios.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/escenarios.md)

---

## 7. Prueba automatizada del recorrido completo

**Observación recibida:**

> Prueba automatizada del recorrido completo.

**Estado:** Corregido.

**Verificación:**

Se implementó una prueba automatizada del recorrido vertical de búsqueda de videojuegos:

`GET /games/search` → FastAPI → `SearchGames` → `GameRepository` → `SteamGameRepository` → respuesta HTTP.

La prueba utiliza un mock de `httpx.get`, por lo que no depende de la disponibilidad real de Steam.

**Evidencia:**

- [`backend/tests/test_search_games.py`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/backend/tests/test_search_games.py)
- [`backend/app/main.py`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/backend/app/main.py)
- [`backend/app/application/usecases/search_games.py`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/backend/app/application/usecases/search_games.py)
- [`backend/app/infrastructure/external/steam/steam_game_repository.py`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/backend/app/infrastructure/external/steam/steam_game_repository.py)

---

## 8. Tabla de trazabilidad en `docs/aspectos.md`

**Observación recibida:**

> Tabla de trazabilidad en `docs/aspectos.md`.

**Estado:** Corregido.

**Verificación:**

La documentación relaciona los atributos de calidad con los escenarios E1–E5, los componentes, las decisiones arquitectónicas y las pruebas o evidencias correspondientes.

**Evidencia:**

- [`docs/aspectos.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/aspectos.md)

---

## 9. ADR con trazabilidad y marcado de reemplazo

**Observación recibida:**

> ADR con trazabilidad y marcado de reemplazo.

**Estado:** Corregido.

**Verificación:**

ADR-0001 registra la adopción inicial de arquitectura hexagonal y fue marcado como reemplazado por ADR-0002. ADR-0002 registra la adopción de Next.js y FastAPI sobre arquitectura hexagonal.

Los nombres de los ADR describen la decisión tomada.

**Evidencia:**

- [`ADR-0001`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0001-adoptar-arquitectura-hexagonal.md)
- [`ADR-0002`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0002-adoptar-nextjs-fastapi-arquitectura-hexagonal.md)

---

## 10. README con requisitos previos y comando de arranque

**Observación recibida:**

> README con requisitos previos y comando de arranque.

**Estado:** Corregido.

**Verificación:**

El README documenta los requisitos del backend y frontend, además del comando único de arranque del proyecto.

**Evidencia:**

- [`README.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/README.md)
- [`backend/requirements.txt`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/backend/requirements.txt)
- [`frontend/package.json`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/frontend/package.json)

---

## 11. Verificar/crear etiqueta `corte-1`

**Observación recibida:**

> Verificar/crear etiqueta `corte-1`.

**Estado:** Pendiente de decisión del equipo.

**Verificación:**

La etiqueta `corte-1` no existe en el repositorio. Crear una etiqueta nueva no modifica la fecha real de entrega del primer corte ni cambia la evaluación histórica.

No se realizará ningún commit, etiqueta o push mientras el equipo no lo autorice expresamente.

---

## 12. Registrar ADR del reto con alternativas y decisión

**Observación recibida:**

> Registrar ADR del reto con alternativas y decisión.

**Estado:** No aplica.

**Verificación:**

La actividad del reto arquitectónico ya no hace parte del alcance actual del proyecto. Por esta razón, no corresponde crear un ADR adicional para ese reto.

---

## 13. Medir línea base con procedimiento

**Observación recibida:**

> Medir línea base con procedimiento.

**Estado:** Corregido.

**Verificación:**

Se ejecutó una prueba de carga real sobre `GET /games/search?q=Minecraft` con k6 v2.2.0, usando 50 usuarios virtuales concurrentes y una solicitud por usuario.

La medición inicial registró un p95 de 14.63 segundos, por lo que no cumplía el objetivo E1. Después se optimizó el repositorio de Steam con caché temporal, límite de resultados y consulta paralela de detalles.

La medición posterior registró un p95 de 1.24 segundos, cumpliendo el límite de ≤ 3 segundos.

**Evidencia:**

- [`scripts/k6_baseline.js`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/scripts/k6_baseline.js)
- [`docs/evidencias/e1-linea-base.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/evidencias/e1-linea-base.md)
- [`backend/app/infrastructure/external/steam/steam_game_repository.py`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/backend/app/infrastructure/external/steam/steam_game_repository.py)

**Resultado:**

El escenario E1 quedó validado con 50 solicitudes exitosas, 0 % de fallos y p95 de 1.24 segundos.

---

## 14. Completar `aspectos.md` con 8 columnas

**Observación recibida:**

> Completar `aspectos.md` con 8 columnas.

**Estado:** Corregido.

**Verificación:**

La estructura de `docs/aspectos.md` incluye ocho columnas y la trazabilidad solicitada para los escenarios de calidad.

**Evidencia:**

- [`docs/aspectos.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/aspectos.md)

---

## 15. Añadir rechazos con motivo en `ia.md`

**Observación recibida:**

> Añadir rechazos con motivo en `ia.md`.

**Estado:** Corregido.

**Verificación:**

La documentación de uso de IA registra los rechazos realizados por el equipo y el motivo técnico correspondiente.

**Evidencia:**

- [`docs/ia.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/ia.md)