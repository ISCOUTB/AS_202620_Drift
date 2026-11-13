# ADR-0019: Recomendar la opción de compra con una regla explicable

- **Estado:** Propuesto
- **Fecha:** 2026-11-13
- **Decisores:** Equipo de desarrollo de DRIFT
- **Relacionado con:** [ADR-0002](0002-adoptar-nextjs-fastapi-arquitectura-hexagonal.md) (la regla vive en el dominio), [ADR-0012](0012-limitacion-de-tasa-en-la-api.md) (límite de tasa), [ADR-0017](0017-inicio-de-sesion-con-google-y-dispositivos.md) (dispositivos del usuario)

## Contexto

La ficha del problema pide **recomendar la opción más conveniente considerando precio, compatibilidad y rendimiento**. DRIFT ya mostraba los precios, la compatibilidad de un PC y los dispositivos del usuario, pero por separado: la persona tenía que cruzarlos a mano.

## Alternativas

1. **Regla fija y corta, calculada en el dominio.** Se puede explicar en una frase y probar sin red.
2. **Puntaje ponderado** (por ejemplo 60 % precio, 40 % experiencia). Más flexible, pero los pesos son arbitrarios y el usuario no puede saber por qué ganó una opción.
3. **Calcularla en la página.** No necesita ruta nueva, pero deja una regla de negocio fuera del dominio y sin pruebas del backend.

## Decisión

Se adopta la **alternativa 1**: `domain/services/recommendation.py`, expuesta en `POST /games/{game_id}/recommendation`.

### La regla

1. Por cada dispositivo del usuario se toma la **tienda más barata de su plataforma**.
2. Se descartan los dispositivos para los que el juego no se vende y los PC que **no alcanzan los requisitos mínimos**.
3. Gana la opción **más barata**. La excepción: si otra opción da mejor experiencia y cuesta **hasta 10 % más**, gana esa.

«Mejor experiencia» tiene dos escalones:

| Escalón | Qué incluye |
|---|---|
| Alto | Un PC que alcanza los requisitos recomendados; una consola (lo que vende su tienda corre en ella) |
| Bajo | Un PC que solo alcanza los mínimos; un PC cuyos requisitos no se pudieron comprobar |

Sin dispositivos no hay compatibilidad que considerar: se recomienda la tienda más barata y la respuesta lo dice (`uses_devices: false`).

### De dónde salen los datos

- **Precios:** los envía la página, que ya los tiene de la búsqueda. La API no vuelve a consultar las tiendas, así que la recomendación no gasta cuota ni suma a los 2,5 s de una búsqueda.
- **Dispositivos:** también los envía la página. Con sesión son los de la cuenta; sin sesión, el PC guardado en el navegador y las consolas marcadas en el filtro de plataformas. Así la recomendación funciona sin iniciar sesión y sin depender de la base de datos.
- **Compatibilidad de cada PC:** la calcula el caso de uso que ya existía (`EstimateCompatibility`). Si la fuente de requisitos falla, ese PC queda «sin comprobar» y la recomendación sigue por precio.

## Consecuencias

**A favor**

- Se cumple el último punto de la ficha.
- La respuesta trae el motivo (`cheapest`, `better_experience`, `only_option`) y los dispositivos descartados con su causa, de modo que la página puede explicarla.
- No agrega fuentes externas, tablas ni secretos.

**En contra**

- **El 10 % es una elección del equipo**, sin datos de usuarios que la respalden.
- **«Rendimiento» sigue siendo un nivel** (mínimo o recomendado), no una estimación de cuadros por segundo.
- **Una consola siempre cuenta como experiencia alta.** No se distingue una generación de otra ni si el juego salió para la consola exacta del usuario: los dispositivos solo guardan «PlayStation» o «Xbox».
- **Los precios llegan del cliente.** Alguien puede enviar precios inventados, pero solo cambia la recomendación que él mismo recibe. Los valores se validan (máximo 60 tiendas, 10 dispositivos, precios no negativos) y la ruta entra en el límite de tasa.
- Las tiendas de PC distintas de Steam siguen con precios en dólares convertidos (ADR-0016), así que una diferencia pequeña entre plataformas puede deberse a la tasa de cambio.

## Lo que se verificó y lo que no

- **Verificado con pruebas** (`backend/tests/test_recomendacion.py`): la regla completa, el paso de la compatibilidad a la experiencia, la respuesta cuando la fuente de requisitos falla y el rechazo de cuerpos inválidos.
- **Verificado en un equipo de desarrollo (13 de noviembre de 2026):** con los requisitos reales de Elden Ring, un PC con RTX 3060 quedó recomendado, uno con 4 GB de RAM quedó descartado y la consola quedó como alternativa. La página mostró la recomendación sin dispositivos y con una consola marcada.
- **No verificado:** con una sesión real de Google y dispositivos guardados en la cuenta. Tampoco con usuarios, para saber si el 10 % es razonable.

## Cuándo revisar esta decisión

- Se guarda el modelo exacto de la consola o se estima el rendimiento con más detalle.
- Hay datos de uso que muestren que el 10 % no refleja lo que la gente elige.
