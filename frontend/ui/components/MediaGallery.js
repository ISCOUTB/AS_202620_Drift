"use client";

import { useEffect, useRef, useState } from "react";

import styles from "./GamePage.module.css";

const HLS_TYPE = "application/vnd.apple.mpegurl";

/** Si quien navega pidió menos movimiento, los tráilers no empiezan solos. */
function prefersReducedMotion() {
  return Boolean(
    globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches,
  );
}

/**
 * Tráiler de Steam. Steam los publica como transmisión HLS: Safari la
 * reproduce solo; en los demás navegadores se carga hls.js, únicamente
 * en esta página. El video va de la CDN de Steam al navegador, sin pasar
 * por el servidor de DRIFT.
 */
function TrailerVideo({ trailer, autoPlay, onFailed }) {
  const videoRef = useRef(null);
  // El aviso de fallo cambia en cada render; el video no debe reiniciarse.
  const failedRef = useRef(onFailed);
  failedRef.current = onFailed;

  useEffect(() => {
    const video = videoRef.current;

    if (!video) {
      return undefined;
    }

    let hls = null;
    let cancelled = false;
    const fail = () => {
      if (!cancelled) {
        failedRef.current();
      }
    };

    if (video.canPlayType(HLS_TYPE)) {
      video.src = trailer.hls;
    } else {
      void import("hls.js")
        .then(({ default: Hls }) => {
          if (cancelled) {
            return;
          }

          if (!Hls.isSupported()) {
            fail();
            return;
          }

          hls = new Hls({
            // Calidad según el tamaño del reproductor y poco búfer: menos
            // datos y menos memoria en el equipo de quien mira.
            capLevelToPlayerSize: true,
            maxBufferLength: 20,
          });

          hls.on(Hls.Events.ERROR, (_event, data) => {
            if (data.fatal) {
              fail();
            }
          });

          hls.loadSource(trailer.hls);
          hls.attachMedia(video);
        })
        .catch(fail);
    }

    return () => {
      cancelled = true;
      hls?.destroy();
      video.removeAttribute("src");
      video.load();
    };
  }, [trailer.hls]);

  return (
    <video
      ref={videoRef}
      className={styles.stageMedia}
      poster={trailer.thumbnail}
      controls
      muted
      autoPlay={autoPlay}
      playsInline
      preload="metadata"
      aria-label={trailer.name}
    />
  );
}

/** Tráilers y capturas del juego, como en la página de la tienda. */
export default function MediaGallery({ media, gameName, fallbackImage, storeUrl }) {
  const [selected, setSelected] = useState(0);
  const [failed, setFailed] = useState({});
  const [userPicked, setUserPicked] = useState(false);
  const stripRef = useRef(null);

  const current = media[selected] ?? null;

  const markFailed = (key) =>
    setFailed((known) => (known[key] ? known : { ...known, [key]: true }));

  const pick = (index) => {
    setSelected(index);
    setUserPicked(true);
  };

  const scrollStrip = (direction) => {
    stripRef.current?.scrollBy({ left: direction * 360, behavior: "smooth" });
  };

  if (!current) {
    return (
      <div className={styles.stage}>
        {fallbackImage ? (
          <img className={styles.stageMedia} src={fallbackImage} alt={gameName} />
        ) : (
          <div className={styles.stageEmpty}>Sin imágenes de este juego.</div>
        )}
      </div>
    );
  }

  const trailerFailed = current.kind === "trailer" && failed[current.key];

  return (
    <div className={styles.gallery}>
      <div className={styles.stage}>
        {current.kind === "trailer" && !trailerFailed && (
          <TrailerVideo
            key={current.key}
            trailer={current.trailer}
            autoPlay={userPicked || !prefersReducedMotion()}
            onFailed={() => markFailed(current.key)}
          />
        )}

        {trailerFailed && (
          <div className={styles.stageFallback} style={{ backgroundImage: `url("${current.thumbnail}")` }}>
            <p>
              No pudimos reproducir este tráiler aquí.{" "}
              {storeUrl && (
                <a href={storeUrl} target="_blank" rel="noopener noreferrer">
                  Verlo en Steam ↗
                </a>
              )}
            </p>
          </div>
        )}

        {current.kind === "screenshot" && (
          <img
            key={current.key}
            className={styles.stageMedia}
            src={current.full}
            alt={`${gameName}: ${current.title.toLocaleLowerCase("es")}`}
          />
        )}
      </div>

      {media.length > 1 && (
        <div className={styles.stripWrap}>
          <button
            type="button"
            className={styles.stripArrow}
            aria-label="Ver miniaturas anteriores"
            onClick={() => scrollStrip(-1)}
          >
            ‹
          </button>

          <div className={styles.strip} ref={stripRef} role="list">
            {media.map((item, index) => (
              <button
                type="button"
                role="listitem"
                key={item.key}
                className={`${styles.thumb} ${index === selected ? styles.thumbActive : ""}`}
                style={{ backgroundImage: `url("${item.thumbnail}")` }}
                aria-label={item.kind === "trailer" ? `Ver tráiler: ${item.title}` : `Ver ${item.title.toLocaleLowerCase("es")}`}
                aria-current={index === selected ? "true" : undefined}
                onClick={() => pick(index)}
              >
                {item.kind === "trailer" && <span className={styles.playIcon} aria-hidden="true" />}
              </button>
            ))}
          </div>

          <button
            type="button"
            className={styles.stripArrow}
            aria-label="Ver más miniaturas"
            onClick={() => scrollStrip(1)}
          >
            ›
          </button>
        </div>
      )}
    </div>
  );
}
