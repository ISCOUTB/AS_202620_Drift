"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { estimateCompatibility } from "../../application/usecases/estimateCompatibility";
import { searchGames } from "../../application/usecases/searchGames";

import { fastApiCompatibilityRepository } from "../../infrastructure/http/FastApiCompatibilityRepository";
import { fastApiGameRepository } from "../../infrastructure/http/FastApiGameRepository";

import styles from "./DriftHome.module.css";
import WaveBackdrop from "./WaveBackdrop";


const STEAM_IMAGES = "https://cdn.cloudflare.steamstatic.com/steam/apps";

function steamImage(appId, file) {
  return `${STEAM_IMAGES}/${appId}/${file}`;
}


const suggestions = [
  {
    id: "hades",
    name: "Hades II",
    genre: "Roguelike · Acción",
    price: "Desde $29.99",
    image: steamImage(1145350, "library_600x900.jpg"),
    hero: steamImage(1145350, "library_hero.jpg"),
  },
  {
    id: "rdr2",
    name: "Red Dead Redemption 2",
    genre: "Aventura · Mundo abierto",
    price: "Desde $19.99",
    image: steamImage(1174180, "library_600x900.jpg"),
    hero: steamImage(1174180, "library_hero.jpg"),
  },
  {
    id: "cyberpunk",
    name: "Cyberpunk 2077",
    genre: "RPG · Ciencia ficción",
    price: "Desde $26.49",
    image: steamImage(1091500, "library_600x900.jpg"),
    hero: steamImage(1091500, "library_hero.jpg"),
  },
  {
    id: "forza",
    name: "Forza Horizon 5",
    genre: "Carreras · Mundo abierto",
    price: "Desde $35.99",
    image: steamImage(1551360, "library_600x900.jpg"),
    hero: steamImage(1551360, "library_hero.jpg"),
  },
  {
    id: "elden",
    name: "Elden Ring",
    genre: "RPG · Fantasía oscura",
    price: "Desde $35.99",
    image: steamImage(1245620, "library_600x900.jpg"),
    hero: steamImage(1245620, "library_hero.jpg"),
  },
  {
    id: "fc25",
    name: "EA Sports FC 25",
    genre: "Deportes · Fútbol",
    price: "Desde $27.99",
    image: steamImage(2669320, "library_600x900.jpg"),
    hero: steamImage(2669320, "library_hero.jpg"),
  },
  {
    id: "baldurs",
    name: "Baldur's Gate 3",
    genre: "RPG · Estrategia",
    price: "Desde $47.99",
    image: steamImage(1086940, "library_600x900.jpg"),
    hero: steamImage(1086940, "library_hero.jpg"),
  },
  {
    id: "spider",
    name: "Marvel's Spider-Man",
    genre: "Acción · Superhéroes",
    price: "Desde $38.99",
    image: steamImage(1817070, "library_600x900.jpg"),
    hero: steamImage(1817070, "library_hero.jpg"),
  },
];


const categories = [
  "Acción",
  "Aventura",
  "Carreras",
  "Deportes",
  "RPG",
  "Estrategia",
];

const connectedStores = [
  {
    name: "Steam",
    detail: "Precio directo en COP",
  },
  {
    name: "Tiendas de PC",
    detail: "GOG, Epic, Humble, Fanatical y más",
  },
  {
    name: "PlayStation",
    detail: "PlayStation Store Colombia",
  },
];

const featuredGames = suggestions.slice(0, 4);

const FEATURED_INTERVAL_MS = 7000;
const CARD_PRICE_LIMIT = 3;


function formatPrice(price) {
  if (typeof price !== "number") {
    return "Precio por confirmar";
  }

  return `$${price.toLocaleString("es-CO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}


function getBestPrice(prices = {}) {
  const entries = Object.entries(prices);

  return entries.reduce((bestPrice, currentPrice) => {
    if (
      bestPrice === null ||
      Number(currentPrice[1]) < Number(bestPrice[1])
    ) {
      return currentPrice;
    }

    return bestPrice;
  }, null);
}

function getSortedPrices(prices = {}) {
  return Object.entries(prices).sort(
    (first, second) => Number(first[1]) - Number(second[1])
  );
}

function getAvailabilityLabel(availablePlatforms) {
  if (availablePlatforms.length > 1) {
    return `Disponible en ${availablePlatforms.length} tiendas`;
  }

  if (availablePlatforms.length === 1) {
    return `Disponible en ${availablePlatforms[0]}`;
  }

  return "Tienda por confirmar";
}

/**
 * Portada del juego: la que entrega el catálogo, luego la de Steam según
 * el appid y, si ninguna carga, un fondo neutro.
 */
function getCoverBackground(game) {
  const covers = [];

  if (game.image) {
    covers.push(`url("${game.image}")`);
  }

  if (/^\d+$/.test(game.id)) {
    covers.push(`url("${steamImage(game.id, "header.jpg")}")`);
  }

  covers.push("linear-gradient(135deg, #3a1a5c, #1d2a7c)");

  return covers.join(", ");
}


function PosterCard({ game, onSearch }) {
  return (
    <button
      type="button"
      className={styles.posterCard}
      onClick={() => onSearch(game.name)}
      title={`Comparar precios de ${game.name}`}
    >
      <span
        className={styles.posterArt}
        style={{ backgroundImage: `url("${game.image}")` }}
      >
        <span className={styles.posterAction}>Comparar</span>
      </span>

      <strong>{game.name}</strong>

      <small>{game.genre}</small>
    </button>
  );
}


function ResultCard({ game, isSelected, onSelect }) {
  const prices = getSortedPrices(game.prices);
  const bestPrice = prices[0] || null;
  const visiblePrices = prices.slice(0, CARD_PRICE_LIMIT);
  const hiddenPrices = prices.length - visiblePrices.length;

  return (
    <article
      className={`${styles.resultCard} ${
        isSelected ? styles.resultCardSelected : ""
      }`}
    >
      <div
        className={styles.resultArt}
        style={{ backgroundImage: getCoverBackground(game) }}
      >
        <span className={styles.resultBadge}>
          {game.availability}
        </span>
      </div>

      <div className={styles.resultBody}>
        <h3>{game.name}</h3>

        {bestPrice ? (
          <>
            <div className={styles.bestLine}>
              <div>
                <small>{bestPrice[0]}</small>

                <strong>{formatPrice(bestPrice[1])}</strong>
              </div>

              <span className={styles.bestTag}>Más barato</span>
            </div>

            <ul className={styles.priceList}>
              {visiblePrices.slice(1).map(([platform, price]) => (
                <li key={platform}>
                  <span>{platform}</span>

                  <span>{formatPrice(price)}</span>
                </li>
              ))}
            </ul>

            {hiddenPrices > 0 && (
              <p className={styles.morePrices}>
                +{hiddenPrices} tiendas más
              </p>
            )}
          </>
        ) : (
          <p className={styles.noPrice}>Precio por confirmar</p>
        )}

        {game.unavailableSources?.length > 0 && (
          <p className={styles.unavailableNotice}>
            Aviso: no se pudo consultar{" "}
            {game.unavailableSources.join(", ")}.
          </p>
        )}

        <button
          type="button"
          className={styles.resultAction}
          onClick={() => onSelect(game)}
        >
          Ver opciones y compatibilidad →
        </button>
      </div>
    </article>
  );
}


export default function DriftHome() {
  const [query, setQuery] = useState("");

  const [selectedCategory, setSelectedCategory] =
    useState("Todo");

  const [activeTab, setActiveTab] =
    useState("Sugeridos");

  const [games, setGames] = useState([]);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");


  const [selectedGame, setSelectedGame] =
    useState(null);

  const [ramGb, setRamGb] =
    useState("");

  const [gpuScore, setGpuScore] =
    useState("");

  const [compatibility, setCompatibility] =
    useState(null);

  const [compatibilityLoading, setCompatibilityLoading] =
    useState(false);

  const [compatibilityError, setCompatibilityError] =
    useState("");


  const [sidebarHidden, setSidebarHidden] =
    useState(false);

  const [featuredIndex, setFeaturedIndex] =
    useState(0);

  const posterRowRef = useRef(null);
  const selectedPanelRef = useRef(null);
  const catalogRef = useRef(null);


  const displayedSuggestions = useMemo(() => {
    if (selectedCategory === "Todo") {
      return suggestions;
    }

    return suggestions.filter((game) =>
      game.genre.includes(selectedCategory)
    );
  }, [selectedCategory]);


  useEffect(() => {
    const timer = setInterval(() => {
      setFeaturedIndex(
        (current) => (current + 1) % featuredGames.length
      );
    }, FEATURED_INTERVAL_MS);

    return () => clearInterval(timer);
  }, []);


  useEffect(() => {
    if (selectedGame) {
      selectedPanelRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }
  }, [selectedGame]);


  const runSearch = async (term) => {
    setLoading(true);
    setError("");
    setActiveTab("Resultados");

    setSelectedGame(null);
    setCompatibility(null);
    setCompatibilityError("");

    try {
      const results = await searchGames(
        term,
        fastApiGameRepository
      );

      setGames(results);

      if (!results.length) {
        setError(
          "No encontramos juegos para esa búsqueda."
        );
      }
    } catch (searchError) {
      setGames([]);

      setError(
        searchError.message ===
          "Escribe el nombre de un videojuego."
          ? searchError.message
          : "No pudimos conectar con el catálogo. Inténtalo de nuevo."
      );
    } finally {
      setLoading(false);
    }
  };


  const submitSearch = (event) => {
    event?.preventDefault();

    void runSearch(query);
  };


  const searchSuggestion = (name) => {
    setQuery(name);
    void runSearch(name);

    catalogRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };


  const selectGameForCompatibility = (game) => {
    setSelectedGame(game);
    setCompatibility(null);
    setCompatibilityError("");
  };


  const closeSelectedGame = () => {
    setSelectedGame(null);
    setCompatibility(null);
    setCompatibilityError("");
  };


  const submitCompatibility = async (event) => {
    event.preventDefault();

    if (!selectedGame) {
      return;
    }

    setCompatibilityLoading(true);
    setCompatibilityError("");
    setCompatibility(null);

    try {
      const result = await estimateCompatibility(
        selectedGame.id,
        {
          ramGb,
          gpuScore,
        },
        fastApiCompatibilityRepository
      );

      setCompatibility(result);
    } catch (compatibilityRequestError) {
      setCompatibilityError(
        compatibilityRequestError.message
      );
    } finally {
      setCompatibilityLoading(false);
    }
  };


  const scrollPosters = (direction) => {
    posterRowRef.current?.scrollBy({
      left: direction * 340,
      behavior: "smooth",
    });
  };


  const featuredGame = featuredGames[featuredIndex];

  const selectedPrices = getSortedPrices(
    selectedGame?.prices
  );

  const showSuggestions = activeTab === "Sugeridos";
  const showLoading = !showSuggestions && loading;
  const showResults =
    !showSuggestions && !loading && games.length > 0;
  const showEmptyState =
    !showSuggestions && !loading && games.length === 0;


  return (
    <main className={styles.pageShell}>
      <WaveBackdrop />

      <div className={styles.app}>

        <header className={styles.topBar}>
          <div className={styles.brand}>
            <button
              type="button"
              className={styles.menuButton}
              aria-label={
                sidebarHidden
                  ? "Mostrar panel lateral"
                  : "Ocultar panel lateral"
              }
              aria-expanded={!sidebarHidden}
              onClick={() =>
                setSidebarHidden((hidden) => !hidden)
              }
            >
              <span />
              <span />
              <span />
            </button>

            <a
              className={styles.logo}
              href="#inicio"
              aria-label="DRIFT, inicio"
            >
              <span>DR</span>
              <span>IFT</span>
            </a>
          </div>

          <form
            className={styles.searchForm}
            onSubmit={submitSearch}
          >
            <span
              className={styles.searchIcon}
              aria-hidden="true"
            />

            <input
              id="game-search"
              value={query}
              onChange={(event) =>
                setQuery(event.target.value)
              }
              placeholder="Busca un videojuego"
              aria-label="Buscar videojuego"
            />

            <button
              type="submit"
              disabled={loading}
            >
              {loading
                ? "Buscando…"
                : "Buscar"}
            </button>
          </form>

          <div className={styles.profileChip}>
            <span className={styles.profileMoon} aria-hidden="true" />

            <span className={styles.profileName}>Jugador</span>

            <span className={styles.profileAvatar}>JD</span>
          </div>
        </header>


        <div
          className={`${styles.layout} ${
            sidebarHidden ? styles.layoutWide : ""
          }`}
        >

          {!sidebarHidden && (
            <aside className={styles.sidebar}>
              <section className={styles.panel}>
                <h2 className={styles.panelTitle}>
                  Listos para comparar
                </h2>

                <ul className={styles.quickList}>
                  {suggestions.slice(0, 6).map((game) => (
                    <li key={game.id}>
                      <button
                        type="button"
                        onClick={() =>
                          searchSuggestion(game.name)
                        }
                      >
                        <span
                          className={styles.quickThumb}
                          style={{
                            backgroundImage: `url("${game.image}")`,
                          }}
                        />

                        <span className={styles.quickText}>
                          <strong>{game.name}</strong>

                          <small>{game.genre}</small>
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </section>

              <section className={styles.panel}>
                <h2 className={styles.panelTitle}>
                  Tiendas conectadas
                </h2>

                <ul className={styles.storeList}>
                  {connectedStores.map((store) => (
                    <li key={store.name}>
                      <span className={styles.storeDot} />

                      <span className={styles.quickText}>
                        <strong>{store.name}</strong>

                        <small>{store.detail}</small>
                      </span>
                    </li>
                  ))}
                </ul>
              </section>
            </aside>
          )}


          <div className={styles.content}>

            <nav
              className={styles.nav}
              aria-label="Navegación principal"
            >
              <button
                type="button"
                onClick={() => {
                  setActiveTab("Sugeridos");
                  setError("");
                }}
                className={
                  activeTab === "Sugeridos"
                    ? styles.navActive
                    : ""
                }
              >
                Inicio
              </button>

              <button
                type="button"
                onClick={() =>
                  setActiveTab("Resultados")
                }
                className={
                  activeTab === "Resultados"
                    ? styles.navActive
                    : ""
                }
              >
                Resultados{" "}
                {games.length
                  ? `(${games.length})`
                  : ""}
              </button>

              <a href="#explorar">Explorar</a>

              <a href="#ofertas">Tiendas</a>
            </nav>


            {activeTab === "Sugeridos" && (
              <section
                className={styles.hero}
                id="inicio"
              >
                <div
                  key={featuredGame.id}
                  className={styles.heroArt}
                  style={{
                    backgroundImage: `url("${featuredGame.hero}")`,
                  }}
                />

                <div className={styles.heroShade} />

                <div className={styles.heroText}>
                  <p className={styles.eyebrow}>
                    TU PRÓXIMA AVENTURA EMPIEZA AQUÍ
                  </p>

                  <h1>
                    Encuentra tu próxima
                    <br />
                    <em>gran partida.</em>
                  </h1>

                  <p className={styles.heroCopy}>
                    Compara precios entre tiendas y
                    descubre juegos que encajan contigo.
                  </p>
                </div>

                <div className={styles.heroFooter}>
                  <div className={styles.heroDots}>
                    {featuredGames.map((game, index) => (
                      <button
                        type="button"
                        key={game.id}
                        aria-label={`Destacar ${game.name}`}
                        className={
                          index === featuredIndex
                            ? styles.heroDotActive
                            : ""
                        }
                        onClick={() =>
                          setFeaturedIndex(index)
                        }
                      />
                    ))}
                  </div>

                  <button
                    type="button"
                    className={styles.heroCta}
                    onClick={() =>
                      searchSuggestion(featuredGame.name)
                    }
                  >
                    <small>{featuredGame.name}</small>

                    <span>Comparar precios</span>
                  </button>
                </div>
              </section>
            )}


            <section
              className={styles.catalog}
              id="explorar"
              ref={catalogRef}
              aria-live="polite"
            >

              {error && (
                <p className={styles.notice}>
                  {error}
                </p>
              )}


              {selectedGame && (
                <section
                  className={styles.selectedGamePanel}
                  ref={selectedPanelRef}
                >
                  <div className={styles.selectedGameHeader}>
                    <div>
                      <p className={styles.purchaseEyebrow}>OPCIONES DE COMPRA</p>

                      <h2>{selectedGame.name}</h2>

                      <p className={styles.selectedGameDescription}>
                        Ordenadas de menor a mayor precio. El más bajo está
                        resaltado.
                      </p>
                    </div>

                    <button
                      type="button"
                      className={styles.closeSelection}
                      onClick={closeSelectedGame}
                      aria-label="Cerrar detalles del juego"
                    >
                      ×
                    </button>
                  </div>

                  <div className={styles.purchaseOptions}>
                    {selectedPrices.map(
                      ([platform, price], index) => {
                        const isBestPrice = index === 0;

                        return (
                          <div
                            key={platform}
                            className={`${styles.purchaseOption} ${
                              isBestPrice ? styles.bestPurchaseOption : ""
                            }`}
                          >
                            <span className={styles.purchasePlatform}>
                              {platform}
                            </span>

                            <div className={styles.purchasePriceContainer}>
                              <strong className={styles.purchasePrice}>
                                {formatPrice(price)}
                              </strong>

                              {isBestPrice && (
                                <span className={styles.bestPriceBadge}>
                                  Más barato
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      },
                    )}

                    {selectedPrices.length === 0 && (
                      <p className={styles.noPurchaseOptions}>
                        No hay precios disponibles en este momento.
                      </p>
                    )}
                  </div>

                  {selectedGame.unavailableSources?.length > 0 && (
                    <p className={styles.unavailableNotice}>
                      No se pudo consultar:{" "}
                      {selectedGame.unavailableSources.join(", ")}.
                    </p>
                  )}

                  <div className={styles.compatibilityDivider} />

                  <div className={styles.compatibilitySection}>
                    <h3>¿Tu PC puede ejecutarlo?</h3>

                    <p className={styles.compatibilityDescription}>
                      GPU: 1 = básica, 2 = media, 3 = alta.
                    </p>

                    <form
                      className={styles.compatibilityForm}
                      onSubmit={submitCompatibility}
                    >
                      <label>
                        <span>RAM disponible (GB)</span>

                        <input
                          type="number"
                          min="1"
                          value={ramGb}
                          onChange={(event) => setRamGb(event.target.value)}
                        />
                      </label>

                      <label>
                        <span>Nivel de GPU</span>

                        <input
                          type="number"
                          min="1"
                          max="3"
                          value={gpuScore}
                          onChange={(event) => setGpuScore(event.target.value)}
                        />
                      </label>

                      <button
                        type="submit"
                        disabled={compatibilityLoading}
                      >
                        {compatibilityLoading
                          ? "Analizando…"
                          : "Comprobar compatibilidad"}
                      </button>
                    </form>

                    {compatibilityError && (
                      <p className={styles.compatibilityError}>
                        {compatibilityError}
                      </p>
                    )}

                    {compatibility && (
                      <div className={styles.compatibilityResult}>
                        <strong>
                          Resultado: {compatibility.status}
                        </strong>

                        {compatibility.minimum_ram_gb && (
                          <p>
                            RAM mínima: {compatibility.minimum_ram_gb} GB ·
                            RAM recomendada: {compatibility.recommended_ram_gb} GB
                          </p>
                        )}

                        {compatibility.minimum_gpu_score && (
                          <p>
                            GPU mínima: {compatibility.minimum_gpu_score} ·
                            GPU recomendada: {compatibility.recommended_gpu_score}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </section>
              )}


              {showSuggestions && (

                <>
                  <div className={styles.sectionHeader}>
                    <h2>Más populares</h2>

                    <div
                      className={styles.categories}
                      aria-label="Categorías de videojuegos"
                    >
                      <button
                        type="button"
                        onClick={() =>
                          setSelectedCategory("Todo")
                        }
                        className={
                          selectedCategory === "Todo"
                            ? styles.categoryActive
                            : ""
                        }
                      >
                        Todo
                      </button>

                      {categories.map((category) => (
                        <button
                          type="button"
                          key={category}
                          onClick={() =>
                            setSelectedCategory(category)
                          }
                          className={
                            selectedCategory === category
                              ? styles.categoryActive
                              : ""
                          }
                        >
                          {category}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className={styles.posterWrap}>
                    <div
                      className={styles.posterRow}
                      ref={posterRowRef}
                    >
                      {displayedSuggestions.map((game) => (
                        <PosterCard
                          key={game.id}
                          game={game}
                          onSearch={searchSuggestion}
                        />
                      ))}
                    </div>

                    <button
                      type="button"
                      className={styles.posterArrow}
                      aria-label="Ver más juegos"
                      onClick={() => scrollPosters(1)}
                    >
                      ›
                    </button>
                  </div>
                </>

              )}

              {showLoading && (

                <div className={styles.gameGrid}>
                  {[0, 1, 2, 3].map((skeleton) => (
                    <div
                      key={skeleton}
                      className={styles.skeletonCard}
                    />
                  ))}
                </div>

              )}

              {showResults && (

                <>
                  <div className={styles.sectionHeader}>
                    <h2>
                      Resultados ({games.length})
                    </h2>
                  </div>

                  <div className={styles.gameGrid}>

                    {games.map((game) => {

                      const availability =
                        getAvailabilityLabel(
                          Object.keys(
                            game.prices || {}
                          )
                        );

                      return (
                        <ResultCard
                          key={game.id}
                          game={{
                            ...game,
                            availability,
                          }}
                          isSelected={
                            selectedGame?.id === game.id
                          }
                          onSelect={
                            selectGameForCompatibility
                          }
                        />
                      );
                    })}

                  </div>
                </>

              )}

              {showEmptyState && (

                <p className={styles.emptyState}>
                  Busca un videojuego para comparar
                  sus precios.
                </p>

              )}

            </section>


            <footer
              className={styles.platforms}
              id="ofertas"
            >
              <span>STEAM</span>
              <span>EPIC GAMES</span>
              <span>GOG</span>
              <span>PLAYSTATION</span>
              <span>HUMBLE</span>
            </footer>

          </div>
        </div>
      </div>
    </main>
  );
}
