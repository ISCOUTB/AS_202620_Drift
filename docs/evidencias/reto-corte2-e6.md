# DRIFT --- Cambios pendientes para la entrega del segundo corte

**Proyecto:** Arquitectura de Software AS_202620\
**Escenario:** E6 --- Degradación de una fuente bajo carga\
**Fecha del informe de referencia:** 11 de octubre de 2026\
**Repositorio:** https://github.com/ISCOUTB/AS_202620_Drift\
**Entorno:** https://drift.iscoutb.dev

> Este documento se ajusta al informe `reto-corte2-e6.pdf`. No repitas
> el experimento E1 de rendimiento como si fuera el reto actual: el
> escenario documentado aquí es E6, relacionado con una fuente externa
> lenta y respuestas degradadas sin aviso.

## 1. Qué ya está definido en el informe E6

El informe establece esta hipótesis:

> Con 50 usuarios concurrentes haciendo búsquedas distintas, caché fría
> y CheapShark tardando más de 5 segundos en cerca del 35 % de las
> consultas, liberar el lock durante la E/S, esperar a cada fuente
> secundaria como máximo 3 segundos y registrar la fuente faltante
> permitirá mantener p95 ≤ 5 s, solicitudes fallidas \< 1 % y cero
> respuestas degradadas sin aviso.

El informe registra estos resultados de las pruebas con fuentes
simuladas:

  -----------------------------------------------------------------------
  Métrica            Antes (mediana   Después (mediana             Umbral
                         reportada)         reportada) 
  -------------- ------------------ ------------------ ------------------
  p95 de                    93,54 s             3,61 s              ≤ 5 s
  búsqueda                                             

  p50 de                    52,09 s             0,70 s                ---
  búsqueda                                             

  Respuestas                     18                  0                  0
  degradadas sin                                       
  aviso por                                            
  corrida                                              

  Solicitudes                     0                  0             \< 1 %
  fallidas                                             
  -----------------------------------------------------------------------

**Limitación que debe conservarse en la entrega:** el experimento se
ejecutó localmente con fuentes simuladas, en un solo equipo y con 50
solicitudes por corrida. El 36 % de consultas lentas se basa en una
observación inicial de 4 de 11 búsquedas. El informe indica que el
despliegue de laboratorio aún ejecutaba la versión anterior al cambio al
momento de la verificación. Por tanto, no afirmes que el cambio ya está
desplegado hasta verificarlo de nuevo.

## 2. ADR-0008: persistencia y modelo de ejecución

Archivo: `docs/adr/0008-persistencia-y-modelo-de-ejecucion.md`

### Correcciones necesarias

-   Comprueba que el encabezado diga `ADR-0008`, no `ADR-0007`.
-   Mantén el estado como `Propuesto` hasta que el equipo confirme la
    decisión.
-   Explica que el catálogo se mantiene en memoria y que la ejecución es
    síncrona, si esa es la decisión confirmada por el equipo y coincide
    con el código.
-   Documenta por separado el cambio de tolerancia a fallos: liberación
    del lock durante la E/S, plazo por fuente secundaria y registro de
    fuentes no disponibles.
-   Registra alternativas, consecuencias y límites medidos.

Texto sugerido para incorporar o adaptar en la sección de decisión:

``` markdown
## Decisión

Se propone mantener el catálogo en memoria y la ejecución síncrona para el MVP, dado que no existe un adaptador o servicio MySQL implementado y el catálogo se reconstruye desde las fuentes externas. La decisión definitiva requiere confirmación del equipo.

Para el escenario E6, se aplica degradación controlada en la infraestructura, sin modificar el dominio, los puertos ni los casos de uso:

- Liberar el lock durante las operaciones de entrada/salida HTTP.
- Mantener como máximo una carga en vuelo por clave.
- Aplicar un plazo configurable de 3 segundos por fuente secundaria mediante `DRIFT_SOURCE_TIMEOUT_SECONDS`.
- Informar las fuentes no disponibles mediante `unavailable_sources` y registrar el evento correspondiente.

La hipótesis y los resultados de esta modificación se documentan en la evidencia del escenario E6. La aceptación definitiva de este ADR requiere confirmación del equipo.
```

Adapta este texto al contenido real del ADR y verifica que los nombres
de configuración y respuesta existan en el código.

### ADR-0004

Según el informe E6, la sustitución se declara en ADR-0008 y **ADR-0004
se conserva sin cambios**. No modifiques su estado ni su contenido si
esa es la convención acordada en el proyecto y el documento nuevo
registra explícitamente que lo sustituye.

## 3. Evidencia del experimento E6

Archivo sugerido: `docs/evidencias/reto-s10-e6.md` (usa la ruta que ya
tenga el repositorio si la evidencia está guardada en otra ubicación).

Asegúrate de que la evidencia incluya:

-   Hipótesis cuantificable y umbrales.
-   Herramienta y versión de k6.
-   Carga de 50 usuarios virtuales y consultas distintas.
-   Fuentes simuladas y latencias configuradas.
-   Degradación de CheapShark en 18 de 50 consultas.
-   Commit usado como versión inicial y commit de la versión modificada.
-   Tres corridas por versión, intercaladas y con caché fría.
-   Tabla completa de resultados antes y después.
-   Cálculo y conclusión frente a cada umbral.
-   Límites del experimento y factores de confusión.

Comandos que el informe menciona:

``` bash
python scripts/e6_corrida.py <backend> <nombre>
```

No inventes el SHA final de la versión modificada. Regístralo después de
confirmar el commit real.

## 4. arc42 --- sección 11.7

Archivo: `docs/arc42/arc42-11-riesgos-y-deuda-tecnica.md`

Añade o actualiza la subsección 11.7 para registrar la deuda del costo
del cliente HTTP y los límites del experimento. No dupliques riesgos que
ya estén documentados: integra estos puntos en la tabla o subsección
existente.

Texto sugerido:

``` markdown
### 11.7. Límites del experimento E6 y deuda técnica

El experimento E6 utiliza fuentes externas simuladas y se ejecuta en un único
equipo local. Por tanto, sus resultados permiten comparar las dos versiones
bajo condiciones controladas, pero no garantizan el mismo rendimiento en el
servidor desplegado ni bajo degradación sostenida.

| Riesgo o deuda | Impacto | Seguimiento |
|---|---|---|
| Fuentes externas simuladas | Las latencias y fallos no reproducen todas las condiciones reales de los proveedores. | Verificar el comportamiento en el entorno desplegado y documentar las diferencias. |
| Muestra limitada a 50 solicitudes por corrida | No demuestra el comportamiento durante una degradación prolongada. | Ejecutar una prueba sostenida si el alcance y los recursos lo permiten. |
| Proporción del 36 % de consultas lentas basada en una observación inicial de 4/11 búsquedas | La frecuencia real de degradación puede ser distinta. | Tratar el porcentaje como supuesto experimental, no como una tasa poblacional demostrada. |
| Costo de creación del contexto TLS del cliente HTTP, estimado en 0,5 s de CPU por llamada en el equipo de medición | Puede afectar la latencia medida y limitar la extrapolación a otros entornos. | Conservar el detalle metodológico y evaluar su impacto en una medición posterior. |
| Despliegue aún no actualizado al cambio medido | La evidencia local no demuestra que la versión corregida esté activa en producción/laboratorio. | Desplegar el commit integrado y verificar nuevamente el flujo completo. |

Estos riesgos no deben marcarse como resueltos únicamente por actualizar la
documentación. Cada cierre requiere evidencia verificable.
```

## 5. Matriz de trazabilidad

Actualiza el archivo de matriz de trazabilidad que ya exista en el
repositorio. No crees una segunda matriz si ya hay una oficial.

Asegúrate de que incluya el escenario E6 y relacione cada elemento con
rutas reales:

  -----------------------------------------------------------------------------------------
  Requisito o    Decisión       Código                  Prueba               Evidencia
  hipótesis                                                                  
  -------------- -------------- ----------------------- -------------------- --------------
  Esperar como   ADR-0008       Configuración y         Prueba de timeout de Resultado de
  máximo 3 s por                adaptador reales que    fuente               E6
  fuente                        aplican el plazo                             
  secundaria                                                                 

  No retener el  ADR-0008       Adaptadores afectados   Prueba de            Resultados
  lock durante                                          concurrencia/carga   antes y
  E/S HTTP                                                                   después

  Informar las   ADR-0008       Campo                   Pruebas de respuesta Resultado de
  fuentes no                    `unavailable_sources` y degradada y logging  E6
  disponibles                   log correspondiente, si                      
                                existen con esos                             
                                nombres                                      

  Mantener p95 ≤ Escenario E6   Flujo completo de       k6 con las           Tabla de
  5 s bajo la                   búsqueda                condiciones          resultados E6
  carga definida                                        documentadas         

  Mantener       Escenario E6   API y manejo de errores Prueba de carga      Tabla de
  solicitudes                                                                resultados E6
  fallidas por                                                               
  debajo del 1 %                                                             
  -----------------------------------------------------------------------------------------

Sustituye los nombres genéricos por las rutas exactas de las clases y
pruebas reales del repositorio. No declares un requisito cubierto si la
prueba correspondiente no existe o no se ha ejecutado.

## 6. Pruebas y calidad

Ejecuta las pruebas del backend y del frontend según las instrucciones
actuales del repositorio. El informe menciona 27 pruebas de backend en
verde, 7 nuevas pruebas y 2 pruebas de arquitectura; vuelve a ejecutar
la suite y confirma que ese sigue siendo el resultado del commit que
entregarás.

Verifica también:

-   Que las pruebas cubran el timeout, las fuentes no disponibles y la
    concurrencia.
-   Que el núcleo no importe módulos de infraestructura.
-   Que el workflow de CI ejecute los análisis configurados.
-   Que exista un resultado verificable de SonarCloud/Quality Gate, si
    forma parte de la entrega.
-   Que los nombres de métricas, campos y variables documentados
    coincidan con el código.

No marques CI, SonarCloud o las pruebas como aprobados basándote
únicamente en resultados históricos.

## 7. Verificación del despliegue

El informe indica que `https://drift.iscoutb.dev` respondió
correctamente para portada, salud, búsqueda de `portal 2` y
compatibilidad, pero que en ese momento ejecutaba la versión anterior al
cambio.

Después de integrar y desplegar la modificación:

1.  Identifica el SHA del commit desplegado.
2.  Comprueba la portada y el endpoint de salud.
3.  Ejecuta una búsqueda real de videojuegos.
4.  Comprueba que una fuente secundaria no disponible se comunica de
    forma explícita cuando corresponda.
5.  Guarda la fecha, URL, respuesta y evidencia.
6.  No afirmes que el cambio está desplegado hasta comprobar que el
    entorno ejecuta el commit correcto.

## 8. Entrega final

Antes de crear o actualizar la etiqueta `corte-2`, verifica que:

-   [ ] ADR-0008 tiene el identificador correcto y refleja la decisión
    confirmada.
-   [ ] ADR-0004 se conserva sin cambios si ADR-0008 lo sustituye según
    la convención del informe.
-   [ ] La documentación arc42 refleja los riesgos y límites reales.
-   [ ] La matriz de trazabilidad apunta a código y pruebas existentes.
-   [ ] La evidencia E6 incluye las tres corridas por versión y las
    limitaciones.
-   [ ] Las pruebas se ejecutaron sobre el commit final.
-   [ ] El despliegue se verificó después de integrar el cambio.
-   [ ] El PDF de dos páginas y la evidencia Markdown coinciden en
    métricas, fechas y commits.
-   [ ] El commit y la etiqueta de entrega apuntan a la versión
    correcta.

## Conclusión

Los resultados del informe E6 muestran una mejora en el experimento
local simulado: el p95 reportado baja de 93,54 s a 3,61 s y las
respuestas degradadas sin aviso pasan de 18 a 0 por corrida. La entrega
debe conservar las limitaciones del experimento y verificar el
despliegue del cambio antes de afirmar que el problema quedó resuelto en
el laboratorio.
