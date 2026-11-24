# ADR-0025: Una página propia para cada juego, con su ficha y tráilers de Steam

- **Estado:** Aceptado
- **Fecha:** 2026-11-23
- **Decisores:** Equipo de desarrollo de DRIFT
- **Complementa a:** [ADR-0019](0019-recomendacion-de-compra.md), [ADR-0016](0016-isthereanydeal-e-historial-de-precios.md) y [ADR-0015](0015-copia-de-respaldo-de-las-fuentes.md): la recomendación, el historial y la copia de respaldo no cambian, solo dónde se muestran.
- **Respeta:** [ADR-0010](0010-costo-de-reversion-de-las-decisiones-de-datos.md): no cambia el modelo público del juego ni las rutas que ya existían.

## Contexto

Hasta ahora, al elegir un juego, sus precios, su historial y la compatibilidad se abrían en un panel dentro del inicio. La página «Explorar» ya tenía su propia pantalla, pero un juego no: no se podía compartir su enlace, y el panel no mostraba qué juego era (ni tráiler ni sinopsis).

El equipo pidió una pantalla propia para cada juego, parecida a la de la tienda: tráilers y capturas arriba, sinopsis y datos al lado, y al bajar las tiendas con sus precios, el historial y la compatibilidad.

Restricciones:

- Steam publica los tráilers solo como transmisión adaptable (HLS `.m3u8` y DASH `.mpd`), no como archivo de video. Safari reproduce HLS; Chrome y Firefox, no siempre.
- El servidor del laboratorio tiene un límite de memoria para todo el equipo (1000 MB desde noviembre de 2026). El video no debe pasar por la API.
- Algunos juegos no tienen identificador de Steam (solo están en PlayStation, Xbox u otra tienda de PC).

## Alternativas

1. **Página `/juego/{id}` con la ficha de Steam y reproductor `hls.js`.** El video va de la CDN de Steam al navegador; la API solo entrega la ficha (un JSON pequeño, en caché una hora).
2. **Página con capturas y un enlace al tráiler en Steam.** Sin dependencia nueva, pero el tráiler se ve fuera de DRIFT.
3. **Seguir con el panel dentro del inicio y agregarle la ficha.** Menos cambios, pero sigue sin enlace propio y la página principal crece aún más.
4. **Pasar el video por la API.** Daría control total, pero cada visita consumiría ancho de banda y memoria del laboratorio.

## Decisión

Se adopta la **alternativa 1**.

### Backend

- Ruta nueva `GET /games/{game_id}/details` (contrato en [`openapi.yaml`](../api/drift/openapi.yaml)): nombre, sinopsis en texto plano, imágenes, fecha, desarrollador, editor, géneros, hasta 8 tráilers y 12 capturas.
- Caso de uso `GetGameDetails`, puerto `GameDetailsSource` y adaptador `SteamGameDetailsSource` (appdetails de Steam, en español y para Colombia). Una llamada sin reintento, timeout de 3 s (`DRIFT_STEAM_DETAILS_*`) y caché de una hora; un fallo no se guarda.
- Solo se aceptan direcciones HTTPS de `*.steamstatic.com`: la página no carga imágenes ni video de otro sitio.
- Un juego sin identificador de Steam responde 404 sin llamar a Steam. Si Steam no responde, 503: la página sigue con los precios.
- La ruta tiene el mismo límite de tasa que las demás que salen a fuentes externas (ADR-0012).

### Frontend

- Página `/juego/[id]?nombre=…`. Arriba, tráilers y capturas (`MediaGallery`) y la ficha; al bajar, la recomendación y las tiendas, el historial y la compatibilidad, los mismos componentes que antes vivían en el panel.
- `hls.js` 1.7.4 (Apache-2.0, sin dependencias) se carga solo en esta página y solo si el navegador no reproduce HLS por sí mismo. Pide la calidad según el tamaño del reproductor y guarda poco búfer. Se usa la versión completa: los tráilers de Steam traen el audio en una pista aparte (`EXT-X-MEDIA TYPE=AUDIO`), que la versión `hls.js/light` no reproduce.
- **Precios sin consultar dos veces:** al abrir un juego desde la búsqueda, la página recibe en `sessionStorage` los precios que ya se mostraron (válidos 10 minutos). Con un enlace directo, busca por el nombre en todas las tiendas con el integrador de búsqueda y elige el mismo juego por identificador o nombre; si el título completo no aparece, intenta una vez con la parte antes del guion.
- Un juego sin ficha de Steam abre la misma página, sin tráiler ni sinopsis, con un aviso y sus precios.
- La búsqueda, la portada, el panel lateral, Explorar y los favoritos llevan a esta página. El inicio ya no carga los catálogos de GPU y CPU: solo los usa la compatibilidad, que ahora está en la página del juego.

## Consecuencias

**A favor**

- Cada juego tiene un enlace que se puede compartir.
- Se ve qué juego es antes de comparar precios, como en la tienda.
- El video no consume memoria ni ancho de banda del laboratorio: la API agrega solo una consulta JSON por juego cada hora.
- El inicio es más liviano: el panel del detalle y dos llamadas a la API por visita salen de él.

**En contra**

- Una dependencia nueva en el frontend (`hls.js`, unos 180 KB comprimidos con gzip en el build de producción), aunque solo se descarga en la página de un juego y solo en navegadores sin HLS propio.
- Los tráilers dependen de la CDN de Steam y de que siga permitiendo cargarlos desde otro dominio (`Access-Control-Allow-Origin: *`, comprobado el 23 de noviembre de 2026).
- Un enlace directo a un juego hace una búsqueda en todas las tiendas, igual que buscarlo desde el inicio.
- Abrir la página de un juego de Steam llama dos veces a appdetails (ficha y requisitos), cada una con su caché.

## Lo que se verificó y lo que no

- **Verificado con pruebas** (`backend/tests/test_ficha_del_juego.py`): la ficha completa, la sinopsis sin HTML, el rechazo de medios de otros sitios, los topes de listas, la caché, el 404 sin llamar a Steam, el 503 con Steam caído y que el fallo no se guarda.
- **Verificado contra Steam real** el 23 de noviembre de 2026 con FINAL FANTASY VII REBIRTH, Hades II y Portal 2, y la ruta contra el contrato con Schemathesis.
- **Verificado en el navegador** (Chrome, servidor de desarrollo): el tráiler se reproduce con el HLS propio de Chrome y también forzando `hls.js` (video y audio decodificados), las capturas cambian, la página llega desde la búsqueda sin repetirla, desde la portada y desde Explorar, un juego sin ficha y un enlace a un juego inexistente; en escritorio y en pantalla de celular.
- **No verificado:** Safari y Firefox, y la página en el despliegue del laboratorio.

## Cuándo revisar esta decisión

- Steam deja de publicar HLS o de permitir cargar sus tráilers desde otro dominio.
- Se agrega otra fuente con fichas de juegos (por ejemplo, para los de consola).
- La medición de E1 muestra que las búsquedas por enlace directo pesan en el servidor.
