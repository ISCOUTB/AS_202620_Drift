"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { exploreSection } from "../../application/usecases/explore";
import { describeSteamPrice } from "../../domain/model/Explore";
import { fastApiExploreRepository } from "../../infrastructure/http/FastApiExploreRepository";

import driftStyles from "./DriftHome.module.css";
import styles from "./Explore.module.css";
import {
  Carousel,
  GenreTabs,
  PosterTile,
  PriceTag,
  SkeletonTiles,
  cover,
} from "./ExploreParts";
import SiteHeader, { compareUrl, useAccountSummary } from "./SiteHeader";
import WaveBackdrop from "./WaveBackdrop";

const SPOTLIGHT_GAMES = 8;
const SPOTLIGHT_INTERVAL_MS = 8000;

// Filas de la portada: qué se pide a la API para cada una.
const SHELVES = [
  { key: "ofertas", title: "En oferta", subtitle: "Descuentos activos en Steam", query: { price: "ofertas" } },
  { key: "gratis", title: "Gratis para jugar", subtitle: "Sin pagar nada para empezar", query: { price: "gratis" } },
  { key: "valorados", title: "Mejor valorados", subtitle: "Las reseñas más positivas de la tienda", query: { sort: "valorados" } },
];

function useSection(query) {
  const [items, setItems] = useState(null);
  const key = JSON.stringify(query);

  useEffect(() => {
    let cancelled = false;

    void exploreSection({ page: 1, ...JSON.parse(key) }, fastApiExploreRepository).then((games) => {
      if (!cancelled) {
        setItems(games);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [key]);

  return items;
}

/** El destacado grande: imagen panorámica, datos del juego y miniaturas. */
function Spotlight({ games }) {
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const count = games.length;

  useEffect(() => {
    if (paused || count < 2) {
      return undefined;
    }

    const timer = setInterval(() => setIndex((current) => (current + 1) % count), SPOTLIGHT_INTERVAL_MS);

    return () => clearInterval(timer);
  }, [paused, count]);

  const game = games[index % count];
  const price = describeSteamPrice(game);

  return (
    <section
      className={styles.spotlight}
      aria-roledescription="carrusel"
      aria-label="Destacados"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <button
        type="button"
        className={`${styles.spotlightArrow} ${styles.spotlightPrev}`}
        aria-label="Destacado anterior"
        onClick={() => setIndex((index - 1 + count) % count)}
      >
        ‹
      </button>

      <Link
        key={game.id}
        href={compareUrl(game.name)}
        className={styles.spotlightCard}
        aria-label={`${game.name}: comparar precios`}
      >
        <span
          className={styles.spotlightArt}
          style={{ backgroundImage: cover(game.capsule, game.hero, game.header) }}
        />

        <span className={styles.spotlightInfo}>
          <span className={styles.spotlightName}>{game.name}</span>

          {game.description && <span className={styles.spotlightText}>{game.description}</span>}

          {game.tags.length > 0 && (
            <span className={styles.tagRow}>
              {game.tags.slice(0, 4).map((tag) => (
                <span key={tag} className={styles.tagChip}>
                  {tag}
                </span>
              ))}
            </span>
          )}

          <span className={styles.spotlightFooter}>
            <span className={styles.spotlightBadge}>
              {price.discount > 0 ? "Oferta" : "Más vendido"}
            </span>

            <PriceTag game={game} />
          </span>
        </span>
      </Link>

      <button
        type="button"
        className={`${styles.spotlightArrow} ${styles.spotlightNext}`}
        aria-label="Destacado siguiente"
        onClick={() => setIndex((index + 1) % count)}
      >
        ›
      </button>

      <div className={styles.spotlightDots}>
        {games.map((item, position) => (
          <button
            type="button"
            key={item.id}
            aria-label={`Ver ${item.name}`}
            aria-current={position === index % count ? "true" : undefined}
            className={position === index % count ? styles.dotActive : ""}
            onClick={() => setIndex(position)}
          />
        ))}
      </div>
    </section>
  );
}

/** Lo que la persona guardó en favoritos, con el precio de cuando lo guardó. */
function FavoritesShelf({ favorites }) {
  return (
    <section className={`${styles.shelf} ${styles.favoritesShelf}`}>
      <div className={styles.shelfHeader}>
        <div>
          <h2>En tus favoritos</h2>
          <p>Compara de nuevo sus precios de hoy</p>
        </div>

        <Link className={styles.shelfLink} href="/?vista=favoritos">
          Ver todos
        </Link>
      </div>

      <div className={styles.favoriteGrid}>
        {favorites.slice(0, 3).map((favorite) => (
          <Link key={favorite.gameId} href={compareUrl(favorite.name)} className={styles.favoriteCard}>
            <span
              className={styles.favoriteArt}
              style={{ backgroundImage: cover(favorite.image) }}
              role="img"
              aria-label={favorite.name}
            />

            <span className={styles.favoriteBadge}>★ En favoritos</span>

            <span className={styles.favoriteFooter}>
              <span>{favorite.name}</span>
              {favorite.price !== null && (
                <strong>
                  ${favorite.price.toLocaleString("es-CO", { maximumFractionDigits: 0 })}
                </strong>
              )}
            </span>
          </Link>
        ))}
      </div>
    </section>
  );
}

function Shelf({ title, subtitle, query }) {
  const items = useSection(query);

  if (items && items.length === 0) {
    return null;
  }

  return (
    <Carousel title={title} subtitle={subtitle}>
      {items ? items.map((game) => <PosterTile key={game.id} game={game} />) : <SkeletonTiles />}
    </Carousel>
  );
}

export default function ExploreHome() {
  const { account, favorites } = useAccountSummary();
  const topSellers = useSection({ sort: "populares" });

  const spotlight = topSellers?.slice(0, SPOTLIGHT_GAMES) ?? [];
  const bestSellers = topSellers?.slice(SPOTLIGHT_GAMES) ?? null;

  return (
    <main className={driftStyles.pageShell}>
      <WaveBackdrop />

      <div className={driftStyles.app}>
        <SiteHeader account={account} active="explorar" />

        <GenreTabs active={null} />

        <div className={styles.exploreBody}>
          {topSellers === null && <div className={`${styles.spotlight} ${styles.skeleton}`} aria-hidden="true" />}

          {spotlight.length > 0 && <Spotlight games={spotlight} />}

          {topSellers !== null && topSellers.length === 0 && (
            <p className={styles.notice} role="status">
              No pudimos cargar el catálogo de Steam en este momento. Inténtalo de nuevo en un rato.
            </p>
          )}

          {account.authenticated && favorites.length > 0 && <FavoritesShelf favorites={favorites} />}

          {(bestSellers === null || bestSellers.length > 0) && (
            <Carousel title="Más vendidos" subtitle="Lo que más se compra hoy en Steam Colombia">
              {bestSellers ? bestSellers.map((game) => <PosterTile key={game.id} game={game} />) : <SkeletonTiles />}
            </Carousel>
          )}

          {SHELVES.map((shelf) => (
            <Shelf key={shelf.key} title={shelf.title} subtitle={shelf.subtitle} query={shelf.query} />
          ))}
        </div>
      </div>
    </main>
  );
}
