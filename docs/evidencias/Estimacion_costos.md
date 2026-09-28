## 9. Estimación de costo mensual

### Supuestos de volumen

Para estimar el costo mensual del sistema DRIFT se toma como escenario un proyecto académico con tráfico moderado:

| Concepto | Volumen mensual supuesto |
|---|---:|
| Peticiones a la API | 50.000 |
| Búsquedas realizadas | 10.000 |
| Datos almacenados | < 1 GB |
| Tráfico de salida | < 10 GB |
| Ejecución del backend | 24 horas/día |
| Frontend | Alojamiento estático en Vercel |

### Costo estimado

El frontend se encuentra desplegado en Vercel utilizando el plan Hobby, cuyo costo es de **$0 USD/mes**. El plan incluye alojamiento y despliegue automático para proyectos dentro de sus límites de uso.

El backend se encuentra desplegado en Azure App Service utilizando el beneficio **Azure for Students**, por lo que el costo del recurso se encuentra cubierto por el beneficio académico disponible.

| Componente | Servicio | Costo mensual estimado |
|---|---|---:|
| Frontend | Vercel Hobby | $0 USD |
| Backend | Azure App Service — Azure for Students | $0 USD de gasto adicional |
| CI/CD | GitHub Actions | $0 USD |
| **Total estimado** | | **$0 USD/mes de gasto adicional** |

### Punto de ruptura de la capa gratuita

La principal restricción considerada para el backend es el **crédito y las condiciones de uso disponibles mediante Azure for Students**.

Por lo tanto, el escenario planteado mantiene un costo de **$0 USD/mes de gasto adicional** mientras los recursos utilizados permanezcan cubiertos por el beneficio de Azure for Students y dentro de sus condiciones de uso.

Si el consumo de los recursos supera el crédito o las condiciones disponibles en Azure for Students, sería necesario reducir el consumo, cambiar la configuración del servicio o utilizar una alternativa de despliegue que no genere costos adicionales.

En Vercel, el plan Hobby tiene límites de uso; al superar dichos límites se debe revisar la configuración del proyecto o cambiar al plan correspondiente.

### Conclusión de la estimación

Con el volumen supuesto de **50.000 peticiones mensuales**, menos de **1 GB de almacenamiento** y menos de **10 GB de tráfico de salida**, el costo esperado para el escenario académico es de:

**$0 USD/mes de gasto adicional**, mientras el backend permanezca cubierto por **Azure for Students** y el frontend permanezca dentro de los límites de Vercel Hobby.

> Los valores corresponden al escenario académico utilizado para la estimación. El consumo debe revisarse periódicamente para evitar superar las condiciones o el crédito disponible de Azure for Students.
