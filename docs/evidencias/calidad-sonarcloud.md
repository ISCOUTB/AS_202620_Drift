# Evidencia pública de SonarCloud y del Quality Gate

Responde a la fila «Pipeline, SonarCloud y Quality Gate públicos» de la evaluación del 17 de noviembre de 2026. Todo se puede comprobar sin credenciales del equipo.

## Revisión verificada

| Evidencia | Valor |
|---|---|
| Commit | `a0e18f99f9a98b2220b4bf1d753cef62eb3308e3` (`master`, 16 de noviembre de 2026) |
| Configuración del análisis | [`sonar-project.properties`](../../sonar-project.properties) |
| Línea que invoca el scanner | `.github/workflows/ci.yml`, job `sonarqube`, paso «Analizar con SonarQube Cloud», con `-Dsonar.qualitygate.wait=true` |
| Run de CI exitoso | [run 43991386520](https://github.com/ISCOUTB/AS_202620_Drift/actions/runs/43991386520) |
| Análisis público | [ISCOUTB_AS_202620_Drift](https://sonarcloud.io/project/overview?id=ISCOUTB_AS_202620_Drift) |
| Análisis de esa revisión | 2026-11-17T00:56:56+00:00, revisión `a0e18f9` |
| Quality Gate | **OK** (consultado el 22 de noviembre de 2026) |

## Cómo comprobarlo

Revisión del último análisis:

```bash
curl -s "https://sonarcloud.io/api/project_analyses/search?project=ISCOUTB_AS_202620_Drift&ps=1"
```

Estado del Quality Gate:

```bash
curl -s "https://sonarcloud.io/api/qualitygates/project_status?projectKey=ISCOUTB_AS_202620_Drift"
```

La revisión del primer comando debe ser igual al último commit de `master`.

## Al cerrar el proyecto

Esta tabla describe `a0e18f9`. Después de fusionar el último cambio hay que actualizar el commit, el run y la fecha con los valores del commit final.
