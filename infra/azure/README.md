# Infraestructura de Azure para DRIFT

Esta carpeta versiona la infraestructura del backend de DRIFT desplegado en Azure App Service. No contiene secretos.

## Recursos definidos

- Plan Linux de Azure App Service, SKU F1 (Free), en Mexico Central.
- Backend `drift-utb-202620` con Python 3.12.
- Inicio mediante `bash startup.sh`.
- HTTPS obligatorio, FTPS solamente y TLS mínimo 1.2.
- Variables públicas necesarias para compilación y CORS.

El código se despliega mediante el workflow
`.github/workflows/master_drift-utb-202620.yml`.

Los secretos de autenticación OIDC permanecen en GitHub Actions y no se incluyen en este repositorio ni en los archivos Bicep.

## Reproducir la infraestructura

Con Azure CLI autenticado y permisos sobre el grupo de recursos:

```powershell
az deployment group create `
  --resource-group rg-drift-as202620 `
  --template-file infra/azure/main.bicep `
  --parameters @infra/azure/main.parameters.json