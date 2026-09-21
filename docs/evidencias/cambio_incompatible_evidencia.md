# Evidencia técnica — Prueba de contrato ante cambios incompatibles

## 1. Prueba ejecutada

La prueba de contrato se ejecutó desde el directorio `backend` mediante el siguiente comando:

```bash
python -m pytest tests/test_contract.py -v
```

El archivo utilizado para realizar la prueba es:

```text
tests/test_contract.py
```

Este archivo utiliza Schemathesis para cargar el contrato OpenAPI y validar automáticamente los endpoints:

```python
import schemathesis

schema = schemathesis.openapi.from_path(
    "../docs/api/drift/openapi.yaml"
)

schema.config.base_url = "http://localhost:8000"


@schema.parametrize()
def test_api_contract(case):
    case.call_and_validate()
```

De esta manera, cada endpoint definido en el contrato es probado automáticamente y su respuesta es comparada con las condiciones establecidas en `openapi.yaml`.

---

## 2. Resultado de la ejecución

Durante la ejecución se obtuvieron los siguientes resultados:

```text
tests/test_contract.py::test_api_contract[GET /] PASSED
tests/test_contract.py::test_api_contract[GET /games/search] PASSED
tests/test_contract.py::test_api_contract[POST /games/sync/playstation] PASSED
tests/test_contract.py::test_api_contract[POST /games/{game_id}/compatibility] FAILED
```

El resumen de la ejecución fue:

```text
1 failed, 3 passed
```

Por lo tanto, se identificó específicamente un incumplimiento en el endpoint:

```text
POST /games/{game_id}/compatibility
```

Mientras que los otros tres endpoints evaluados cumplieron correctamente las condiciones del contrato.

---

## 3. Cambio utilizado para la prueba

Como parte de la validación se realizó un cambio en el modelo de datos utilizado por el endpoint de compatibilidad.

Actualmente, el modelo contiene:

```python
class CompatibilityRequest(BaseModel):
    ram_gb: StrictInt
    gpu_score: int
```

El uso de `StrictInt` establece una condición más estricta para el campo `ram_gb`, ya que el valor recibido debe cumplir específicamente con el tipo entero esperado.

Este tipo de modificación permite comprobar que las pruebas de contrato pueden detectar diferencias entre el comportamiento implementado y las condiciones definidas en el contrato OpenAPI.

---

## 4. Evidencia del fallo

La ejecución de las pruebas muestra que el endpoint de compatibilidad es identificado automáticamente como el endpoint que presenta el problema:

```text
POST /games/{game_id}/compatibility FAILED
```

Además, el resumen final confirma que la ejecución no fue exitosa:

```text
1 failed, 3 passed
```

Esto demuestra que el mecanismo de pruebas no considera válida la implementación cuando existe una incompatibilidad con el contrato.

---

## 5. Interpretación de la evidencia

La prueba permite verificar dos comportamientos importantes:

* Los endpoints que cumplen las especificaciones del contrato son marcados como `PASSED`.
* Cuando un endpoint presenta una condición incompatible con el contrato, Schemathesis lo identifica como `FAILED`.

En este caso, el fallo se localiza específicamente en:

```text
/games/{game_id}/compatibility
```

por lo que la prueba permite identificar rápidamente qué parte de la API necesita ser revisada.

---

## 6. Evidencia técnica

Las capturas utilizadas como evidencia muestran:

1. La ejecución de `pytest` utilizando Schemathesis.
2. Los tres endpoints que pasan correctamente las pruebas.
3. El endpoint de compatibilidad marcado como `FAILED`.
4. El resumen final de la ejecución:

```text
1 failed, 3 passed
```

5. El cambio realizado en el modelo `CompatibilityRequest`.

Estas evidencias permiten comprobar que las pruebas automatizadas responden ante modificaciones que pueden generar incompatibilidades con el contrato de la API.

---

## 7. Conclusión

La prueba realizada demuestra que el contrato OpenAPI de DRIFT está siendo utilizado para validar automáticamente el comportamiento de la API.

Al introducir un cambio que afecta las condiciones esperadas por el contrato, la prueba identifica el endpoint afectado y finaliza con un resultado fallido:

```text
1 failed, 3 passed
```

Por lo tanto, la evidencia demuestra que el mecanismo implementado permite **detectar cambios incompatibles en la API antes de considerar válida la implementación**.
