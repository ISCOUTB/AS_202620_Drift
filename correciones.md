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

>
> `docs/aspectos.md` en prosa, sin la tabla de 8 columnas ni enlaces a escenarios ni al ADR.
>

**Estado:** Corregido.

**Verificación:**

Se revisó `docs/aspectos.md` y se incorporó la estructura solicitada para los atributos de calidad, incluyendo la trazabilidad correspondiente hacia los escenarios E1–E5 y la decisión arquitectónica documentada en ADR-0002.

**Evidencia:**

- [`docs/aspectos.md`](docs/aspectos.md)
- [`docs/escenarios.md`](docs/escenarios.md)
- [`docs/adr/0002-arquitectura-base.md`](docs/adr/adr/0002-arquitectura-base.md)

---

### 2. Ficha del problema sin tensiones de calidad

**Observación recibida:**

>
> Ficha del problema sin tensiones de calidad.
>

**Estado:** Corregido.

**Verificación:**

Se revisó la ficha del problema y se incorporaron las tensiones entre los objetivos de calidad relevantes para DRIFT, especialmente mantenibilidad, rendimiento, disponibilidad, usabilidad y compatibilidad.

**Evidencia:**

- [`docs/aspectos.md`](docs/aspectos.md)
- [`docs/arc42/arc42_1_introduccion_objetivos.md`](docs/arc42/arc42_1_introduccion_objetivos.md)

---

### 3. Desbalance de contribución

**Observación recibida:**

>
> Desbalance de contribución en el periodo (51 vs 9 commits en S3).
>

**Estado:** Observación válida.

**Verificación:**

El repositorio efectivamente presentaba una distribución desigual de commits entre los integrantes durante el periodo indicado. Este hallazgo no corresponde a una ausencia documental o técnica que pueda considerarse corregida mediante un cambio en la arquitectura.

**Evidencia:**

- Historial de Git del repositorio.
- Distribución de contribuciones registrada en la planilla de equipo.

**Acción:**

El equipo equilibró la participación y mantener evidencia de las contribuciones de todos los integrantes durante los siguientes periodos.

---

### 4. README con arranque contradictorio

**Observación recibida:**

>
> README con arranque contradictorio (mvn sin pom.xml / uvicorn solo backend) y sin comando único.
>

**Estado:** Corregido.

**Verificación:**

El README fue actualizado para reflejar el stack tecnológico real del proyecto. Se eliminó la referencia incorrecta a Maven/Spring Boot y se documentó el arranque del backend mediante FastAPI/Uvicorn y del frontend mediante Next.js.

**Evidencia:**

```bash
cd backend  
python -m pip install -r requirements.txt  
uvicorn app.main:app --reload
```

#### 5. Sin pipeline / evidencia de CI en verde

**Observación recibida:**

> 
> Sin pipeline: prueba existe sin evidencia de verde.
> 

**Estado:** Corregido.

**Verificación:**

El repositorio cuenta con un workflow de integración continua en `.github/workflows/ci.yml`.

El pipeline ejecuta las pruebas automatizadas del backend y, posteriormente, realiza un smoke test de integración entre el backend y el frontend. Durante la ejecución se inicia la API FastAPI, se verifica su disponibilidad, se instalan las dependencias del frontend, se compila la aplicación Next.js y se comprueba que la portada responda correctamente.

La ejecución analizada finalizó exitosamente. Las pruebas del backend reportaron `2 passed` y el job de frontend conectado a la API también finalizó correctamente.

**Evidencia:**

- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
- [`backend/tests/test_health.py`](../backend/tests/test_health.py)
- [Ejecución exitosa del backend en GitHub Actions](https://github.com/ISCOUTB/AS_202620_Drift/actions/runs/34060984657/job/101561346006)
- [Ejecución exitosa del frontend conectado a la API en GitHub Actions](https://github.com/ISCOUTB/AS_202620_Drift/actions/runs/34060984657/job/101561376057)

**Resultado:**

El pipeline se ejecutó correctamente y los jobs definidos finalizaron en verde.

## 6. Matriz de estilos sin referencia a E1–E5

**Observación recibida:** Matriz de estilos sin referencia a los escenarios E1–E5.

**Estado:** Corregido.

\*\*Verificación:\*\*Se actualizó la documentación arquitectónica para mantener trazabilidad entre los atributos y objetivos de calidad y los escenarios E1–E5 definidos para DRIFT.

**Evidencia:**

- [`docs/aspectos.md`](docs/aspectos.md)
- [`docs/escenarios.md`](docs/escenarios.md)
- [`docs/arc42/arc42_10_requisitos_de_calidad.md`](docs/arc42/arc42_10_requisitos_de_calidad.md)

---

## 7. Prueba automatizada del recorrido completo

**Observación recibida:** Prueba automatizada del recorrido completo.

**Estado:** Corregido.

\*\*Verificación:\*\*Se implementó una prueba automatizada del recorrido vertical de búsqueda de videojuegos.

El recorrido verificado es:

```
GET /games/search    
↓    
FastAPI    
↓    
SearchGames    
↓    
GameRepository    
↓    
SteamGameRepository    
↓    
Game    
↓    
Respuesta HTTP
```

La prueba utiliza un mock de `httpx.get` para simular las respuestas de Steam y verificar el resultado sin depender de la disponibilidad de la API externa.

**Evidencia:**

- [`backend/tests/test_health.py`](../backend/tests/test_health.py)
- [`backend/app/main.py`](../backend/app/main.py)
- [`backend/app/application/usecases/search_games.py`](../backend/app/application/usecases/search_games.py)
- [`backend/app/infrastructure/external/steam/steam_game_repository.py`](../backend/app/infrastructure/external/steam/steam_game_repository.py)

---

## 8. Tabla de trazabilidad en docs/aspectos.md

**Observación recibida:** Tabla de trazabilidad en `docs/aspectos.md`.

**Estado:** Corregido.

\*\*Verificación:\*\*La documentación fue actualizada para relacionar los atributos de calidad con los escenarios E1–E5 y la decisión arquitectónica correspondiente.

**Evidencia:**

- [`docs/aspectos.md`](docs/aspectos.md)
- [`docs/escenarios.md`](docs/escenarios.md)
- [`docs/adr/0002-arquitectura-base.md`](docs/adr/0002-arquitectura-base.md)

---

## 9. ADR con trazabilidad y marcado de reemplazo

**Observación recibida:** ADR con trazabilidad y marcado de reemplazo.

**Estado:** Corregido.

\*\*Verificación:\*\*Los ADR fueron actualizados para indicar su estado y la relación entre las decisiones arquitectónicas.

- ADR-0001 conserva la decisión inicial de Arquitectura Hexagonal y registra que el stack tecnológico fue posteriormente actualizado.
- ADR-0002 registra la actualización del stack a Next.js + FastAPI y mantiene la Arquitectura Hexagonal como decisión arquitectónica.
- Ambos ADR incluyen una sección de trazabilidad.

**Evidencia:**

- [`docs/adr/0001-arquitectura-base.md`](docs/adr/0001-arquitectura-base.md)
- [`docs/adr/0002-arquitectura-base.md`](docs/adr/0002-arquitectura-base.md)

---

## 10. README con requisitos previos y comando de arranque

**Observación recibida:** README con requisitos previos y comando de arranque.

**Estado:** Corregido.

\*\*Verificación:\*\*El README documenta los requisitos y comandos necesarios para instalar las dependencias y ejecutar el backend y frontend del proyecto.

**Evidencia:**

- [`README.md`](../README.md)
- [`backend/requirements.txt`](../backend/requirements.txt)
- [`frontend/package.json`](../frontend/package.json)

---

## 11. Verificar/crear etiqueta corte-1

**Observación recibida:** Verificar/crear etiqueta `corte-1`.

**Estado:** Pendiente.

\*\*Verificación:\*\*La etiqueta `corte-1` debe apuntar al commit exacto que será presentado como entrega del primer corte.

No se debe crear la etiqueta hasta finalizar las correcciones y verificaciones correspondientes al corte.

**Acción pendiente:**

Una vez finalizados los cambios:

```bash
git add .    
git commit -m "Preparación entrega corte 1"    
git tag corte-1    
git push origin master    
git push origin corte-1
```

La rama utilizada deberá corresponder a la rama principal actual del repositorio.

**Evidencia pendiente:**

- Hash del commit correspondiente al corte.
- Etiqueta `corte-1` visible en GitHub.

---

## 12. Registrar ADR del reto con alternativas y decisión

**Observación recibida:** Registrar ADR del reto con alternativas y decisión.

**Estado:** Pendiente.

\*\*Verificación:\*\*Esta observación corresponde al reto arquitectónico que será asignado para la evaluación.

El ADR correspondiente deberá registrar el problema planteado por el reto, las alternativas consideradas, los criterios de decisión, la alternativa seleccionada, sus consecuencias y la trazabilidad correspondiente.

\*\*Acción pendiente:\*\*Una vez definido el reto arquitectónico, crear el ADR correspondiente y asociarlo al commit donde se registre la decisión.

---

## 13. Medir línea base con procedimiento

**Observación recibida:** Medir línea base con procedimiento.

**Estado:** Parcialmente corregido.

\*\*Verificación:\*\*Los escenarios de calidad ya contienen medidas verificables y se incorporó un método de verificación para cada escenario.

Por ejemplo, el escenario E1 establece un límite de ≤ 3 segundos en p95 para la búsqueda con hasta 50 usuarios concurrentes y define un procedimiento para realizar la prueba de carga y calcular el percentil 95.

**Evidencia:**

- [`docs/escenarios.md`](docs/escenarios.md)

**Pendiente:**

- Ejecutar las mediciones reales y conservar evidencia de los resultados obtenidos, incluyendo el procedimiento utilizado y los valores registrados.

---

## 14. Completar aspectos.md con 8 columnas

**Observación recibida:** Completar `aspectos.md` con 8 columnas.

**Estado:** Corregido.

\*\*Verificación:\*\*La estructura de `docs/aspectos.md` fue actualizada para incorporar la información requerida para los atributos de calidad y su trazabilidad con los escenarios correspondientes.

**Evidencia:**

- [`docs/aspectos.md`](docs/aspectos.md)

---

## 15. Añadir rechazos con motivo en ia.md

**Observación recibida:** Añadir rechazos con motivo en `ia.md`.

**Estado:** Corregido.

\*\*Verificación:\*\*La documentación de uso de IA registra los rechazos realizados por el equipo y el motivo correspondiente.

**Evidencia:**

- [`docs/ia.md`](ia.md)

---

### 16. Evidenciar run de CI en verde

**Observación recibida:**

> 
> Evidenciar run de CI en verde.
> 

**Estado:** Corregido.

**Verificación:**

Se ejecutó el workflow de integración continua en GitHub Actions sobre el commit `d0db91e45d2ca17bac6e360aacd97d012ee02354`.

La ejecución finalizó exitosamente. Las pruebas automatizadas del backend reportaron `2 passed`, el smoke test del frontend conectado a la API finalizó correctamente y el análisis de SonarCloud obtuvo `Quality Gate passed`.

**Evidencia disponible:**

- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
- [`backend/tests/test_health.py`](../backend/tests/test_health.py)
- [Ejecución exitosa del backend en GitHub Actions](https://github.com/ISCOUTB/AS_202620_Drift/actions/runs/34060984657/job/101561346006)
- [Ejecución exitosa del frontend conectado a la API en GitHub Actions](https://github.com/ISCOUTB/AS_202620_Drift/actions/runs/34060984657/job/101561376057)

**Resultado:**

La ejecución de CI quedó en verde, proporcionando evidencia verificable de la ejecución exitosa del pipeline.

 
