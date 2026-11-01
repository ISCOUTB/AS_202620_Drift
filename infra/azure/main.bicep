targetScope = 'resourceGroup'

param location string = 'mexicocentral'
param appServicePlanName string = 'ASP-rgdriftas202620-8b10'
param appName string = 'drift-utb-202620'
param corsAllowedOrigins string = 'https://drift-frontend-as202620.vercel.app,http://localhost:3000'

@secure()
@description('Token de las operaciones administrativas (ADR-0011). Se pasa al desplegar; no se versiona.')
param driftAdminToken string = ''

resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: appServicePlanName
  location: location
  kind: 'linux'

  sku: {
    name: 'F1'
    tier: 'Free'
    capacity: 1
  }

  properties: {
    reserved: true
  }
}

resource backendApp 'Microsoft.Web/sites@2023-12-01' = {
  name: appName
  location: location
  kind: 'app,linux'

  identity: {
    type: 'SystemAssigned'
  }

  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true

    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      appCommandLine: 'bash startup.sh'
      ftpsState: 'FtpsOnly'
      minTlsVersion: '1.2'

      appSettings: [
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'CORS_ALLOWED_ORIGINS'
          value: corsAllowedOrigins
        }
        {
          name: 'DRIFT_ADMIN_TOKEN'
          value: driftAdminToken
        }
        {
          name: 'DRIFT_RATE_LIMIT_PER_MINUTE'
          value: '60'
        }
        {
          // El front-end de App Service agrega la IP del cliente (con puerto) al final.
          name: 'DRIFT_TRUST_FORWARDED_FOR'
          value: 'true'
        }
      ]
    }
  }
}

output backendBaseUrl string = 'https://${backendApp.properties.defaultHostName}'
