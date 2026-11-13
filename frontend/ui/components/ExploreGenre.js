"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { exploreGames } from "../../application/usecases/explore";
import {
  DEFAULT_FILTERS,
  EXPLORE_PRICES,
  EXPLORE_SORTS,
  EXPLORE_TAGS,
  MAX_EXPLORE_PAGE,
  MAX_SELECTED_TAGS,
  activeFilterChips,
  filtersToSearch,
  findGenre,
  formatReleaseDate,
  posterOf,
  reviewTone,
} from "../../domain/model/Explore";
import { fastApiExploreRepository } from "../../infrastructure/http/FastApiExploreRepository";

import driftStyles from "./DriftHome.module.css";
import styles from "./Explore.module.css";
import { GenreTabs, PriceTag, cover } from "./ExploreParts";
import SiteHeader, { compareUrl, useAccountSummary } from "./SiteHeader";
import WaveBackdrop from "./WaveBackdrop";

function FilterGroup({ title, children, defaultOpen = true }) {
  return (
    <details className={styles.filterGroup} open={defaultOpen}>
      <summary>{title}</summary>
      <div className={styles.filterOptions}>{children}</div>
    </details>
  );
}

function Filters({ filters, onChange }) {
  const [tagSearch, setTagSearch] = useState("");
  // En pantallas angostas los grupos empiezan cerrados: la lista queda a la vista.
  const [narrow, setNarrow] = useState(false);
  const chips = activeFilterChips(filters);

  useEffect(() => {
    setNarrow(window.matchMedia("(max-width: 860px)").matches);
  }, []);

  const shownTags = EXPLORE_TAGS.filter((tag) =>
    tag.name.toLocaleLowerCase("es").includes(tagSearch.trim().toLocaleLowerCase("es")),
  );

  const toggleTag = (slug) => {
    const tags = filters.tags.includes(slug)
      ? filters.tags.filter((tag) => tag !== slug)
      : [...filters.tags, slug].slice(0, MAX_SELECTED_TAGS);

    onChange({ ...filters, tags });
  };

  return (
    <aside className={styles.filters} aria-label="Filtros">
      <div className={styles.filterHead}>
        <h2>Filtros</h2>

        {chips.length > 0 && (
          <button type="button" className={styles.clearFilters} onClick={() => onChange({ ...DEFAULT_FILTERS })}>
            Quitar todos
          </button>
        )}
      </div>

      {chips.length > 0 && (
        <ul className={styles.activeChips}>
          {chips.map((chip) => (
            <li key={chip.key}>
              <button type="button" onClick={() => onChange(chip.remove(filters))} aria-label={`Quitar ${chip.label}`}>
                <span aria-hidden="true">×</span> {chip.label}
              </button>
            </li>
          ))}
        </ul>
      )}

      <FilterGroup key={`orden-${narrow}`} title="Ordenar por" defaultOpen={!narrow}>
        {EXPLORE_SORTS.map((sort) => (
          <label key={sort.slug} className={styles.filterOption}>
            <input
              type="radio"
              name="orden"
              checked={filters.sort === sort.slug}
              onChange={() => onChange({ ...filters, sort: sort.slug })}
            />
            <span>{sort.name}</span>
          </label>
        ))}
      </FilterGroup>

      <FilterGroup key={`precio-${narrow}`} title="Precio" defaultOpen={!narrow}>
        {EXPLORE_PRICES.map((price) => (
          <label key={price.slug} className={styles.filterOption}>
            <input
              type="radio"
              name="precio"
              checked={filters.price === price.slug}
              onChange={() => onChange({ ...filters, price: price.slug })}
            />
            <span>{price.name}</span>
          </label>
        ))}
      </FilterGroup>

      <FilterGroup key={`etiquetas-${narrow}`} title="Etiquetas" defaultOpen={!narrow}>
        <input
          className={styles.tagSearch}
          type="search"
          value={tagSearch}
          onChange={(event) => setTagSearch(event.target.value)}
          placeholder="Buscar etiqueta"
          aria-label="Buscar etiqueta"
        />

        {shownTags.map((tag) => {
          const checked = filters.tags.includes(tag.slug);

          return (
            <label key={tag.slug} className={styles.filterOption}>
              <input
                type="checkbox"
                checked={checked}
                disabled={!checked && filters.tags.length >= MAX_SELECTED_TAGS}
                onChange={() => toggleTag(tag.slug)}
              />
              <span>{tag.name}</span>
            </label>
          );
        })}

        {shownTags.length === 0 && <p className={styles.filterEmpty}>Ninguna etiqueta coincide.</p>}
      </FilterGroup>
    </aside>
  );
}

/** Un juego de la lista: carátula, datos, imagen grande y barra de precio. */
function GameRow({ game }) {
  const released = formatReleaseDate(game.releaseDate);
  const tone = reviewTone(game);

  return (
    <article className={styles.gameRow}>
      <Link href={compareUrl(game.name)} className={styles.gameRowPoster} aria-label={`Comparar precios de ${game.name}`}>
        <span style={{ backgroundImage: cover(posterOf(game), game.header) }} />
      </Link>

      <div className={styles.gameRowInfo}>
        <h3>
          <Link href={compareUrl(game.name)}>{game.name}</Link>
        </h3>

        {game.description && <p className={styles.gameRowText}>{game.description}</p>}

        <dl className={styles.gameRowFacts}>
          {game.tags.length > 0 && (
            <div>
              <dt>Etiquetas</dt>
              <dd className={styles.tagRow}>
                {game.tags.map((tag) => (
                  <span key={tag} className={styles.tagChip}>
                    {tag}
                  </span>
                ))}
              </dd>
            </div>
          )}

          {released && (
            <div>
              <dt>Lanzamiento</dt>
              <dd>{released}</dd>
            </div>
          )}

          {game.developers.length > 0 && (
            <div>
              <dt>Desarrollador</dt>
              <dd>{game.developers.join(", ")}</dd>
            </div>
          )}
        </dl>

        {game.review && (
          <p className={styles.gameRowReview}>
            <span className={styles[`review_${tone}`]}>{game.review}</span>
            {game.reviewPercent !== null && <> · {game.reviewPercent} % positivas</>}
          </p>
        )}
      </div>

      <div
        className={styles.gameRowMedia}
        style={{ backgroundImage: cover(game.hero, game.capsule, game.header) }}
        aria-hidden="true"
      />

      <div className={styles.gameRowBar}>
        <span className={styles.gameRowStore}>Precio en Steam</span>

        <PriceTag game={game} />

        <Link href={compareUrl(game.name)} className={styles.compareButton}>
          Comparar precios
        </Link>
      </div>
    </article>
  );
}

function SkeletonRows({ count = 3 }) {
  return Array.from({ length: count }, (_, index) => (
    <div key={index} className={`${styles.gameRow} ${styles.skeleton}`} aria-hidden="true" />
  ));
}

export default function ExploreGenre({ genre, initialFilters }) {
  const { account } = useAccountSummary();
  const genreInfo = findGenre(genre);

  const [filters, setFilters] = useState(initialFilters);
  const [games, setGames] = useState([]);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const sentinel = useRef(null);
  // Cada cambio de filtros invalida las respuestas que aún no llegan.
  const generation = useRef(0);
  const filtersKey = useMemo(() => JSON.stringify(filters), [filters]);

  const loadPage = useCallback(
    async (nextPage) => {
      const ticket = generation.current;

      setLoading(true);
      setError("");

      try {
        const answer = await exploreGames(
          { genre, ...JSON.parse(filtersKey), page: nextPage },
          fastApiExploreRepository,
        );

        if (ticket !== generation.current) {
          return;
        }

        setGames((current) => {
          const known = new Set(current.map((game) => game.id));
          return [...current, ...answer.items.filter((game) => !known.has(game.id))];
        });
        setPage(nextPage);
        setHasMore(answer.hasMore && nextPage < MAX_EXPLORE_PAGE);
      } catch {
        if (ticket === generation.current) {
          setError("No pudimos cargar más juegos de Steam. Inténtalo de nuevo.");
        }
      } finally {
        if (ticket === generation.current) {
          setLoading(false);
        }
      }
    },
    [genre, filtersKey],
  );

  // Filtros nuevos: lista desde cero y la dirección los recuerda.
  useEffect(() => {
    generation.current += 1;
    setGames([]);
    setPage(0);
    setHasMore(true);
    setLoading(false);

    window.history.replaceState(null, "", `/explorar/${genre}${filtersToSearch(JSON.parse(filtersKey))}`);

    void loadPage(1);
  }, [genre, filtersKey, loadPage]);

  // Al acercarse al final de la lista se pide la página siguiente.
  useEffect(() => {
    const element = sentinel.current;

    if (!element || !hasMore || loading || error || page === 0) {
      return undefined;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          void loadPage(page + 1);
        }
      },
      { rootMargin: "600px 0px" },
    );

    observer.observe(element);

    return () => observer.disconnect();
  }, [hasMore, loading, error, page, loadPage]);

  const changeFilters = (next) => {
    setFilters({ tags: [...next.tags], sort: next.sort, price: next.price });
  };

  return (
    <main className={driftStyles.pageShell}>
      <WaveBackdrop />

      <div className={driftStyles.app}>
        <SiteHeader account={account} active="explorar" />

        <GenreTabs active={genre} />

        <header className={styles.genreHeader}>
          <p className={styles.eyebrow}>Explorar por género</p>
          <h1>{genreInfo.name}</h1>
          <p>Juegos de {genreInfo.name.toLocaleLowerCase("es")} en Steam Colombia. Elige uno para comparar su precio en todas las tiendas.</p>
        </header>

        <div className={styles.genreLayout}>
          <Filters filters={filters} onChange={changeFilters} />

          <section className={styles.gameList} aria-live="polite" aria-busy={loading}>
            {games.map((game) => (
              <GameRow key={game.id} game={game} />
            ))}

            {loading && <SkeletonRows count={games.length ? 2 : 4} />}

            {!loading && !error && games.length === 0 && page > 0 && (
              <p className={styles.notice}>Ningún juego cumple estos filtros. Prueba con menos etiquetas.</p>
            )}

            {error && (
              <div className={styles.notice} role="alert">
                <span>{error}</span>
                <button type="button" onClick={() => loadPage(page + 1)}>
                  Reintentar
                </button>
              </div>
            )}

            {!hasMore && games.length > 0 && <p className={styles.listEnd}>No hay más juegos con estos filtros.</p>}

            <div ref={sentinel} className={styles.sentinel} aria-hidden="true" />
          </section>
        </div>
      </div>
    </main>
  );
}
