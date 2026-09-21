# Evidencia técnica — Prueba de contrato ante cambios incompatibles

## 1. Prueba ejecutada

La prueba se ejecutó desde `backend` mediante:

```bash
python -m pytest tests/test_contract.py -v
```
## Evidencia del run fallido en CI

La prueba de contrato fue ejecutada mediante GitHub Actions y el run presentó un resultado fallido debido a la detección de una solicitud que incumplía el contrato OpenAPI.

**Run de GitHub Actions:**  
[Ver ejecución fallida de CI](https://github.com/ISCOUTB/AS_202620_Drift/actions/runs/35549837357)

La prueba utiliza Schemathesis para validar los endpoints definidos en `openapi.yaml`.
### 2. Resultado
El endpoint afectado fue:

```text
POST /games/{game_id}/compatibility
```

Schemathesis detectó que la API aceptó un valor inválido para `gpu_score`:

```json
{
    "ram_gb": 16,
    "gpu_score": false
}
```

La API respondió `200 OK`, aunque el contrato define `gpu_score` como entero.
Schemathesis reportó:

```text
API accepted schema-violating request
Invalid component: in body - gpu_score: Incorrect type
```

Resultado:

```text
1 failed, 13 passed, 2 warnings in 14.19s
```

## 3. Conclusión
La evidencia demuestra que Schemathesis detecta automáticamente cuando la API acepta datos que incumplen el contrato OpenAPI, identificando el endpoint y el campo que presenta el problema.
