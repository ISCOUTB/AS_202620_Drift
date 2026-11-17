"use client";

import {
  describeExcluded,
  describeExperience,
  describeReason,
} from "../../domain/model/Recommendation";

import styles from "./RecommendationPanel.module.css";

const money = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});

function formatPrice(price) {
  return price === 0 ? "Gratis" : money.format(price);
}

const TONE_OF_EXPERIENCE = {
  recommended: "good",
  console: "good",
  minimum: "warn",
  unverified: "neutral",
};

function whereToPlay(option) {
  if (option.device) {
    return `para jugar en ${option.device.name}`;
  }

  // «PlayStation para PlayStation» no dice nada.
  return option.store === option.platform ? "" : `para ${option.platform}`;
}

/** La opción de compra más conveniente según precio y dispositivos. */
export default function RecommendationPanel({
  entry,
  links = {},
  canSignIn = false,
}) {
  if (!entry || entry.state === "error") {
    // Sin recomendación la lista de precios sigue siendo suficiente.
    return null;
  }

  if (entry.state === "loading") {
    return (
      <section className={styles.panel} aria-label="Recomendación">
        <p className={styles.eyebrow}>RECOMENDACIÓN</p>
        <p className={styles.note}>Buscando tu mejor opción…</p>
      </section>
    );
  }

  const recommendation = entry.data;
  const best = recommendation.recommended;

  return (
    <section className={styles.panel} aria-label="Recomendación">
      <p className={styles.eyebrow}>
        {recommendation.usesDevices
          ? "RECOMENDACIÓN PARA TUS DISPOSITIVOS"
          : "RECOMENDACIÓN POR PRECIO"}
      </p>

      {best ? (
        <>
          <div className={styles.best}>
            <div className={styles.bestText}>
              <h3>
                Cómpralo en {best.store}{" "}
                <span>{whereToPlay(best)}</span>
              </h3>

              <p className={styles.reason}>
                {describeReason(recommendation, formatPrice)}
              </p>

              {best.experience && (
                <p
                  className={`${styles.experience} ${
                    styles[TONE_OF_EXPERIENCE[best.experience]]
                  }`}
                >
                  {best.device?.kind === "pc"
                    ? `${best.device.name} ${describeExperience(best.experience)}.`
                    : "Es la versión hecha para esa consola."}
                </p>
              )}
            </div>

            <div className={styles.bestPrice}>
              <strong>{formatPrice(best.price)}</strong>

              {best.discount > 0 && <small>-{best.discount}%</small>}

              {links[best.store] && (
                <a
                  href={links[best.store]}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Ir a la tienda ↗
                </a>
              )}
            </div>
          </div>

          {recommendation.alternatives.length > 0 && (
            <ul className={styles.alternatives}>
              {recommendation.alternatives.map((option) => (
                <li key={`${option.store}-${option.device?.id ?? ""}`}>
                  <span>
                    {option.store} {whereToPlay(option)}
                    {option.experience
                      ? ` · ${describeExperience(option.experience)}`
                      : ""}
                  </span>

                  <strong>{formatPrice(option.price)}</strong>
                </li>
              ))}
            </ul>
          )}
        </>
      ) : (
        <p className={styles.note}>
          {recommendation.usesDevices
            ? "Con tus dispositivos no encontramos una opción para jugarlo."
            : "No hay precios disponibles para recomendar una tienda."}
        </p>
      )}

      {recommendation.excluded.length > 0 && (
        <p className={styles.excluded}>
          No se tuvo en cuenta:{" "}
          {recommendation.excluded.map(describeExcluded).join("; ")}.
        </p>
      )}

      {!recommendation.usesDevices && (
        <p className={styles.hint}>
          {canSignIn
            ? "Inicia sesión y registra tus dispositivos, o guarda tu PC más abajo, para que la recomendación tenga en cuenta dónde puedes jugarlo."
            : "Guarda tu PC más abajo o marca tus consolas en «Tengo:» para que la recomendación tenga en cuenta dónde puedes jugarlo."}
        </p>
      )}
    </section>
  );
}
