import {
  cachedAtForStore,
  describeAge,
  describeCachedSources,
  hasColombiaPrice,
  sortPricesForPurchase,
} from "../../domain/model/Game";

import styles from "./DriftHome.module.css";

export function formatPrice(price) {
  if (typeof price !== "number") {
    return "Precio por confirmar";
  }

  return `$${price.toLocaleString("es-CO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

/** Precio en una tienda; si se conoce su página de compra, es un enlace a ella. */
export function PurchaseOption({
  platform,
  price,
  link,
  isBestPrice,
  cachedAt,
  discount,
}) {
  const className = `${styles.purchaseOption} ${
    isBestPrice ? styles.bestPurchaseOption : ""
  } ${link ? styles.purchaseLink : ""}`;

  const content = (
    <>
      <span className={styles.purchasePlatform}>
        {platform}

        {link && <small className={styles.purchaseHint}>Comprar ↗</small>}

        {platform === "PlayStation" && (
          <small className={styles.storeHint}>
            Cobra en dólares; valor aproximado
          </small>
        )}

        {!hasColombiaPrice(platform) && (
          <small className={styles.storeHint}>
            Precio de EE. UU.; confirma que se venda en Colombia
          </small>
        )}

        {cachedAt && (
          <small className={styles.cachedHint}>
            Precio guardado {describeAge(cachedAt)}
          </small>
        )}
      </span>

      <div className={styles.purchasePriceContainer}>
        <span className={styles.priceStack}>
          {discount > 0 && (
            <span className={styles.discountBadge}>-{discount}%</span>
          )}

          <strong className={styles.purchasePrice}>{formatPrice(price)}</strong>
        </span>

        {isBestPrice && <span className={styles.bestPriceBadge}>Más barato</span>}
      </div>
    </>
  );

  if (!link) {
    return <div className={className}>{content}</div>;
  }

  return (
    <a
      className={className}
      href={link}
      target="_blank"
      rel="noopener noreferrer"
      title={`Abrir ${platform} en una pestaña nueva`}
    >
      {content}
    </a>
  );
}

/** Todas las tiendas de un juego, primero Colombia y de menor a mayor. */
export default function PurchaseOptions({ game }) {
  const prices = sortPricesForPurchase(game.prices);
  const cachedSources = describeCachedSources(game);

  return (
    <>
      <div className={styles.purchaseOptions}>
        {prices.map(([platform, price], index) => (
          <PurchaseOption
            key={platform}
            platform={platform}
            price={price}
            link={game.links?.[platform]}
            isBestPrice={index === 0 && hasColombiaPrice(platform)}
            cachedAt={cachedAtForStore(game, platform)}
            discount={game.discounts?.[platform]}
          />
        ))}

        {prices.length === 0 && (
          <p className={styles.noPurchaseOptions}>
            No hay precios disponibles en este momento.
          </p>
        )}
      </div>

      {game.unavailableSources?.length > 0 && (
        <p className={styles.unavailableNotice}>
          No se pudo consultar: {game.unavailableSources.join(", ")}.
        </p>
      )}

      {cachedSources.length > 0 && (
        <p className={styles.unavailableNotice}>
          Estas fuentes no respondieron y se muestra su último precio guardado:{" "}
          {cachedSources.join(", ")}.
        </p>
      )}
    </>
  );
}
