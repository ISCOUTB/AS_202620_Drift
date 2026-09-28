# ADR-0005: Estrategias de Despliegue

* **Estado:** Aceptado
* **Fecha:** 2026-09-27
* **Decisores:** Equipo DRIFT
* **Relacionado con:** ADR-0006 — Despliegue serverless para la API de búsqueda de DRIFT

---

## 1. Contexto

El sistema DRIFT requiere definir dónde se ejecutarán las diferentes piezas de la aplicación y cómo se distribuirán entre servicios de infraestructura.

Actualmente el sistema cuenta con un frontend y un backend desplegados públicamente. La base de datos será incorporada posteriormente como parte de la evolución del sistema.

La distribución considerada es:

* Frontend: Vercel.
* Backend/API: Azure App Service.
* Base de datos: Supabase, para una implementación futura.
* Repositorio: GitHub.
* Integración y despliegue: GitHub Actions.

La decisión debe considerar:

* Disponibilidad pública del sistema.
* Costo para el escenario académico.
* Facilidad de despliegue y operación.
* Separación entre frontend, backend y persistencia.
* Posibilidad de evolución futura.
* Facilidad de reversión.

---

## 2. Problema

Se necesita establecer una estrategia de despliegue que permita mantener separadas las diferentes piezas de DRIFT sin introducir una dependencia innecesaria entre ellas.

Además, el proyecto debe mantener los costos bajo control. Para el backend se dispone del beneficio académico de Azure for Students, mientras que el frontend puede utilizar Vercel dentro de sus condiciones de uso.

La base de datos todavía no forma parte del entorno desplegado, pero se necesita establecer una plataforma prevista para cuando se implemente la persistencia de datos.

---

## 3. Alternativas consideradas

### Alternativa A — Ejecutar todos los componentes en una única plataforma

Mantener frontend, backend y base de datos dentro de una misma infraestructura.

Ventajas:

* Administración centralizada.
* Menor cantidad de plataformas externas.
* Configuración inicialmente más sencilla.

Desventajas:

* Mayor acoplamiento entre los componentes.
* Los cambios de una pieza pueden afectar el despliegue de las demás.
* Reduce la independencia entre frontend, backend y base de datos.
* Puede limitar las alternativas disponibles para cada componente.

### Alternativa B — Separar los componentes por responsabilidad

Utilizar una plataforma específica para cada pieza:

* Vercel para frontend.
* Azure App Service para backend.
* Supabase para base de datos.

Ventajas:

* Separación clara de responsabilidades.
* Frontend y backend pueden desplegarse independientemente.
* El backend aprovecha el beneficio de Azure for Students.
* La base de datos puede incorporarse posteriormente sin modificar la ubicación del frontend.
* Permite mantener la infraestructura de cada componente desacoplada.

Desventajas:

* Se utilizan varios proveedores.
* Es necesario configurar correctamente la comunicación entre servicios.
* Se deben revisar periódicamente los límites y condiciones de cada plataforma.

---

## 4. Decisión

Se decide utilizar una arquitectura de despliegue distribuida por componente:

| Componente    | Plataforma        | Estado                              |
| ------------- | ----------------- | ----------------------------------- |
| Frontend      | Vercel            | En uso                              |
| Backend/API   | Azure App Service | En uso                              |
| Base de datos | Supabase          | Prevista para implementación futura |
| Repositorio   | GitHub            | En uso                              |
| CI/CD         | GitHub Actions    | En uso                              |

### Frontend — Vercel

El frontend se despliega en Vercel.

Vercel se utiliza como plataforma de alojamiento y despliegue del frontend, permitiendo mantener esta pieza independiente del backend.

### Backend — Azure App Service

El backend se despliega en Azure App Service.

Esta decisión aprovecha el beneficio académico de Azure for Students disponible para el proyecto.

El backend se encuentra disponible públicamente mediante:

```text
https://drift-utb-202620-g5fvchdcgpcthkeg.mexicocentral-01.azurewebsites.net
```

### Base de datos — Supabase

Se establece Supabase como la plataforma prevista para la base de datos.

Actualmente Supabase **no se encuentra implementado en el entorno desplegado**. La integración se realizará cuando el sistema incorpore la persistencia de datos.

La decisión permite mantener la base de datos como un servicio independiente del backend.

---

## 5. Arquitectura resultante

La distribución de las piezas queda representada de la siguiente manera:

```text
                    ┌──────────────┐
                    │    Usuario   │
                    └───────┬──────┘
                            │
                            ▼
                    ┌──────────────┐
                    │    Vercel    │
                    │   Frontend   │
                    └───────┬──────┘
                            │
                            │ HTTP/HTTPS
                            ▼
                 ┌──────────────────────┐
                 │   Azure App Service  │
                 │       Backend        │
                 └──────────┬───────────┘
                            │
                            │ Futuramente
                            ▼
                    ┌──────────────┐
                    │   Supabase   │
                    │ Base de datos│
                    └──────────────┘
```

---

## 6. Costos y límites

El proyecto utiliza el beneficio **Azure for Students** para el backend.

El frontend utiliza Vercel dentro de las condiciones de su plan gratuito.

Para el escenario académico se establece como objetivo mantener:

```text
Gasto adicional esperado = $0 USD/mes
```

La decisión deberá revisarse si el consumo supera las condiciones o beneficios disponibles en las plataformas utilizadas.

Los principales factores que pueden afectar el costo son:

* Aumento del tráfico.
* Incremento de solicitudes al backend.
* Consumo de recursos de Azure.
* Uso de almacenamiento.
* Transferencia de datos.
* Límites del plan utilizado.

---

## 7. Compatibilidad con la arquitectura

La decisión de despliegue no modifica la separación de responsabilidades de la aplicación.

Las plataformas de despliegue pertenecen a la infraestructura y no deben introducir dependencias innecesarias dentro del dominio de DRIFT.

Conceptualmente:

```text
Usuario
   │
   ▼
Vercel
   │
   ▼
Frontend
   │
   ▼
Azure App Service
   │
   ▼
Backend / API
   │
   ▼
Casos de uso
   │
   ▼
Dominio
   │
   ▼
Supabase
   │
   ▼
Base de datos
```

Supabase se incorporará únicamente cuando se implemente la persistencia de datos.

---

## 8. Reversibilidad

La decisión es reversible porque las piezas del sistema mantienen responsabilidades separadas.

Para cambiar la plataforma de despliegue se puede:

* Mantener el código del frontend y desplegarlo en otra plataforma.
* Mantener el backend y ejecutarlo en otro entorno compatible.
* Cambiar el servicio de base de datos mediante una nueva configuración de persistencia.
* Mantener los contratos existentes entre los componentes.

El objetivo es que la infraestructura de despliegue no determine la lógica principal de la aplicación.

---

## 9. Consecuencias positivas

* Permite desplegar frontend y backend de forma independiente.
* El backend cuenta con una URL pública.
* Se aprovecha el beneficio académico de Azure for Students.
* Permite incorporar Supabase posteriormente sin cambiar la ubicación del frontend.
* Mantiene separadas las responsabilidades de cada componente.
* Facilita la evolución independiente de las diferentes piezas.
* Permite utilizar GitHub Actions para automatizar los despliegues.

## 10. Consecuencias negativas

* El sistema depende de varias plataformas externas.
* Se deben mantener configuraciones diferentes para cada servicio.
* La comunicación entre servicios debe configurarse correctamente.
* Los límites y condiciones de los proveedores deben revisarse periódicamente.
* La incorporación futura de Supabase agregará otra dependencia externa.

---

## 11. Criterios para revisar la decisión

La decisión deberá revisarse si:

* El consumo de Azure supera las condiciones disponibles mediante Azure for Students.
* El tráfico del sistema aumenta significativamente.
* Los límites de Vercel dejan de ser suficientes.
* Se requiere una capacidad de base de datos diferente a la ofrecida por Supabase.
* Los costos dejan de ser compatibles con las restricciones del proyecto.
* Se identifica una dependencia de alguno de los proveedores que dificulte la evolución o reversión del sistema.

---

## 12. Relación con otros documentos

Esta decisión complementa:

* **ADR-0006 — Despliegue serverless para la API de búsqueda de DRIFT.**
* **arc42 sección 7 — Vista de despliegue.**
* **arc42 sección 2 — Restricciones y límites de costo.**

---

## 13. Estado final

**Aceptado.**

La estrategia de despliegue de DRIFT utiliza actualmente Vercel para el frontend y Azure App Service para el backend.

Supabase queda establecido como la plataforma prevista para la futura implementación de la base de datos, pero actualmente no forma parte del entorno desplegado.
