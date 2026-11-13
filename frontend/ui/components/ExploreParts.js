"use client";

import Link from "next/link";
import { useRef } from "react";

import {
  EXPLORE_GENRES,
  describeSteamPrice,
  posterOf,
} from "../../domain/model/Explore";

import styles from "./Explore.module.css";
import { compareUrl } from "./SiteHeader";

const FALLBACK = "linear-gradient(135deg, #3a1a5c, #1d2a7c)";

/** Fondo con la imagen y, si no carga, un degradado. */
export function cover(...urls) {
  return [...urls.filter(Boolean).map((url) => `url("${url}")`), FALLBACK].join(", ");
}

/** Pestañas de géneros, como las de una tienda: «Destacados» y cada género. */
export function GenreTabs({ active }) {
  return (
    <nav className={styles.genreTabs} aria-label="Géneros">
      <Link
        href="/explorar"
        className={active ? "" : styles.genreTabActive}
        aria-current={active ? undefined : "page"}
      >
        Destacados
      </Link>

      {EXPLORE_GENRES.map((genre) => (
        <Link
          key={genre.slug}
          href={`/explorar/${genre.slug}`}
          className={active === genre.slug ? styles.genreTabActive : ""}
          aria-current={active === genre.slug ? "page" : undefined}
        >
          {genre.name}
        </Link>
      ))}
    </nav>
  );
}

/** Precio de Steam: gratis, con descuento (tachado) o normal. */
export function PriceTag({ game, compact = false }) {
  const price = describeSteamPrice(game);

  return (
    <span className={`${styles.priceTag} ${compact ? styles.priceTagCompact : ""}`}>
      {price.discount > 0 && <span className={styles.discount}>-{price.discount}%</span>}

      {price.original && <s className={styles.originalPrice}>{price.original}</s>}

      <strong>{price.text}</strong>
    </span>
  );
}

/** Carrusel horizontal con flechas; con el dedo o la rueda también se desliza. */
export function Carousel({ title, subtitle, children, action }) {
  const track = useRef(null);

  const move = (direction) => {
    const element = track.current;

    if (element) {
      element.scrollBy({ left: direction * element.clientWidth * 0.9, behavior: "smooth" });
    }
  };

  return (
    <section className={styles.shelf}>
      <div className={styles.shelfHeader}>
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>

        {action}
      </div>

      <div className={styles.carousel}>
        <button
          type="button"
          className={`${styles.carouselArrow} ${styles.carouselPrev}`}
          aria-label={`Anteriores de ${title}`}
          onClick={() => move(-1)}
        >
          ‹
        </button>

        <div className={styles.carouselTrack} ref={track}>
          {children}
        </div>

        <button
          type="button"
          className={`${styles.carouselArrow} ${styles.carouselNext}`}
          aria-label={`Siguientes de ${title}`}
          onClick={() => move(1)}
        >
          ›
        </button>
      </div>
    </section>
  );
}

/** Carátula vertical con el precio abajo; lleva a comparar precios. */
export function PosterTile({ game }) {
  return (
    <Link className={styles.posterTile} href={compareUrl(game.name)} title={`Comparar precios de ${game.name}`}>
      <span
        className={styles.posterTileArt}
        style={{ backgroundImage: cover(posterOf(game), game.header) }}
        role="img"
        aria-label={game.name}
      />

      <span className={styles.posterTileFooter}>
        <span className={styles.posterTileName}>{game.name}</span>
        <PriceTag game={game} compact />
      </span>
    </Link>
  );
}

/** Tarjetas vacías mientras carga una fila. */
export function SkeletonTiles({ count = 5 }) {
  return Array.from({ length: count }, (_, index) => (
    <span key={index} className={`${styles.posterTile} ${styles.skeleton}`} aria-hidden="true" />
  ));
}
