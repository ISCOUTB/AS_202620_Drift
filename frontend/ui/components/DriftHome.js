"use client";

import { useMemo, useState } from "react";

import { estimateCompatibility } from "../../application/usecases/estimateCompatibility";
import { searchGames } from "../../application/usecases/searchGames";

import { fastApiCompatibilityRepository } from "../../infrastructure/http/FastApiCompatibilityRepository";
import { fastApiGameRepository } from "../../infrastructure/http/FastApiGameRepository";

import styles from "./DriftHome.module.css";


const suggestions = [
  {
    id: "hades",
    name: "Hades II",
    genre: "Roguelike · Acción",
    price: "Desde $29.99",
    image:
      "https://images.unsplash.com/photo-1593305841991-05c297ba4575?auto=format&fit=crop&w=900&q=85",
  },
  {
    id: "rdr2",
    name: "Red Dead Redemption 2",
    genre: "Aventura · Mundo abierto",
    price: "Desde $19.99",
    image:
      "https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=900&q=85",
  },
  {
    id: "cyberpunk",
    name: "Cyberpunk 2077",
    genre: "RPG · Ciencia ficción",
    price: "Desde $26.49",
    image:
      "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=900&q=85",
  },
  {
    id: "forza",
    name: "Forza Horizon 5",
    genre: "Carreras · Mundo abierto",
    price: "Desde $35.99",
    image:
      "https://images.unsplash.com/photo-1504215680853-026ed2a45def?auto=format&fit=crop&w=900&q=85",
  },
  {
    id: "elden",
    name: "Elden Ring",
    genre: "RPG · Fantasía oscura",
    price: "Desde $35.99",
    image:
      "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=900&q=85",
  },
  {
    id: "fc25",
    name: "EA Sports FC 25",
    genre: "Deportes · Fútbol",
    price: "Desde $27.99",
    image:
      "https://images.unsplash.com/photo-1575361204480-aadea25e6e68?auto=format&fit=crop&w=900&q=85",
  },
  {
    id: "baldurs",
    name: "Baldur's Gate 3",
    genre: "RPG · Estrategia",
    price: "Desde $47.99",
    image:
      "https://images.unsplash.com/photo-1534423861386-85a16f5d13fd?auto=format&fit=crop&w=900&q=85",
  },
  {
    id: "spider",
    name: "Marvel's Spider-Man",
    genre: "Acción · Superhéroes",
    price: "Desde $38.99",
    image:
      "https://images.unsplash.com/photo-1531259683007-016a7b628fc3?auto=format&fit=crop&w=900&q=85",
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

function getAvailabilityLabel(availablePlatforms) {
  if (availablePlatforms.length > 1) {
    return `Disponible en ${availablePlatforms.length} plataformas`;
  }

  if (availablePlatforms.length === 1) {
    return `Disponible en ${availablePlatforms[0]}`;
  }

  return "Plataforma por confirmar";
}


function Stars() {
  return (
    <span
      className={styles.stars}
      aria-label="Valoración de cinco estrellas"
    >
      ★★★★★
    </span>
  );
}


function GameCard({ game, onSelect }) {
  const prices = Object.entries(game.prices || {});

  const bestPrice = getBestPrice(game.prices || {});

  return (
    <article
      className={styles.gameCard}
      onClick={() => onSelect?.(game)}
      role={onSelect ? "button" : undefined}
      tabIndex={onSelect ? 0 : undefined}
      onKeyDown={(event) => {
        if (
          onSelect &&
          (event.key === "Enter" || event.key === " ")
        ) {
          event.preventDefault();
          onSelect(game);
        }
      }}
      style={{
        backgroundImage: `linear-gradient(0deg, rgba(6, 8, 20, .98) 3%, rgba(6, 8, 20, .12) 75%), url("${game.image}")`,
      }}
    >
      <div className={styles.cardTop}>
        <Stars />

        {onSelect ? (
          <span
            className={styles.addButton}
            title="Ver opciones y compatibilidad"
          >
            PC
          </span>
        ) : (
          <span className={styles.addButton}>+</span>
        )}
      </div>

      <div className={styles.cardInfo}>
        <p>{game.genre}</p>

        <h2>{game.name}</h2>

        <p className={styles.purchaseTitle}>
          OPCIONES DE COMPRA
        </p>

        {prices.length > 0 ? (
          <div className={styles.priceOptions}>
            {prices.map(([platform, price]) => {
              const isBest =
                bestPrice &&
                bestPrice[0] === platform;

              return (
                <div
                  key={platform}
                  className={`${styles.priceOption} ${
                    isBest ? styles.bestPrice : ""
                  }`}
                >
                  <span>{platform}</span>

                  <div className={styles.priceValue}>
                    <strong>
                      {formatPrice(price)}
                    </strong>

                    {isBest && (
                      <small>
                        Más barato
                      </small>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className={styles.noPrice}>
            Precio por confirmar
          </p>
        )}

        {game.unavailableSources?.length > 0 && (
          <p className={styles.unavailableNotice}>
            Aviso: no se pudo consultar{" "}
            {game.unavailableSources.join(", ")}.
          </p>
        )}
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


  const displayedSuggestions = useMemo(() => {
    if (selectedCategory === "Todo") {
      return suggestions;
    }

    return suggestions.filter((game) =>
      game.genre.includes(selectedCategory)
    );
  }, [selectedCategory]);


  const submitSearch = async (event) => {
    event?.preventDefault();

    setLoading(true);
    setError("");

    setSelectedGame(null);
    setCompatibility(null);
    setCompatibilityError("");

    try {
      const results = await searchGames(
        query,
        fastApiGameRepository
      );

      setGames(results);
      setActiveTab("Resultados");

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


  const selectGameForCompatibility = (game) => {
    setSelectedGame(game);
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


  return (
    <main className={styles.pageShell}>
      <div className={styles.ambientGlow} />

      <div className={styles.container}>

        <header className={styles.header}>
          <a
            className={styles.logo}
            href="#inicio"
            aria-label="DRIFT, inicio"
          >
            <span>DR</span>
            <span>IFT</span>
          </a>

          <nav
            className={styles.nav}
            aria-label="Navegación principal"
          >
            <a href="#explorar">
              Explorar
            </a>

            <a href="#ofertas">
              Ofertas
            </a>

            <a href="#biblioteca">
              Mi biblioteca
            </a>

            <a href="#novedades">
              Novedades
            </a>
          </nav>

          <div className={styles.headerActions}>
            <button
              type="button"
              className={styles.iconButton}
              aria-label="Abrir búsqueda"
              onClick={() =>
                document
                  .getElementById("game-search")
                  ?.focus()
              }
            >
              <span className={styles.searchIcon} />
            </button>

            <button
              type="button"
              className={styles.profileButton}
              aria-label="Abrir perfil"
            >
              JD
            </button>
          </div>
        </header>


        <section
          className={styles.hero}
          id="inicio"
        >
          <p className={styles.eyebrow}>
            TU PRÓXIMA AVENTURA EMPIEZA AQUÍ
          </p>

          <h1>
            Encuentra tu próxima
            <br />
            <em>gran partida.</em>
          </h1>

          <p className={styles.heroCopy}>
            Compara precios entre plataformas y
            descubre juegos que encajan contigo.
          </p>

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
        </section>


        <section
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
        </section>


        <section
          className={styles.catalog}
          id="explorar"
          aria-live="polite"
        >
          <div className={styles.catalogHeader}>
            <div className={styles.tabs}>
              <button
                type="button"
                onClick={() => {
                  setActiveTab("Sugeridos");
                  setError("");
                }}
                className={
                  activeTab === "Sugeridos"
                    ? styles.tabActive
                    : ""
                }
              >
                Sugeridos
              </button>

              <button
                type="button"
                onClick={() =>
                  setActiveTab("Resultados")
                }
                className={
                  activeTab === "Resultados"
                    ? styles.tabActive
                    : ""
                }
              >
                Resultados{" "}
                {games.length
                  ? `(${games.length})`
                  : ""}
              </button>
            </div>

            <button
              type="button"
              className={styles.viewAll}
            >
              Ver todo <span>↗</span>
            </button>
          </div>


          {error && (
            <p className={styles.notice}>
              {error}
            </p>
          )}


          {selectedGame && (
              <section className={styles.selectedGamePanel}>
                <div className={styles.selectedGameHeader}>
                  <div>
                    <p className={styles.purchaseEyebrow}>OPCIONES DE COMPRA</p>

                    <h2>{selectedGame.name}</h2>

                    <p className={styles.selectedGameDescription}>
                      El precio más bajo está resaltado. Puedes elegir la plataforma que
                      prefieras.
                    </p>
                  </div>

                  <button                                         
                    type="button"
                    className={styles.closeSelection}
                    onClick={() => {
                      setSelectedGame(null);
                      setCompatibility(null);
                      setCompatibilityError("");
                    }}
                    aria-label="Cerrar detalles del juego"
                  >
                    ×
                  </button>
                </div>

                <div className={styles.purchaseOptions}>
                  {Object.entries(selectedGame.prices || {}).map(
                    ([platform, price]) => {
                      const bestPrice = getBestPrice(selectedGame.prices);
                      const isBestPrice =
                        bestPrice && bestPrice[0] === platform;

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

                  {Object.keys(selectedGame.prices || {}).length === 0 && (
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


          {activeTab === "Resultados" &&
          games.length > 0 ? (

            <div className={styles.gameGrid}>

              {games.map((game, index) => {

                const availablePlatforms =
                  Object.keys(
                    game.prices || {}
                  );

                const art =
                  suggestions[
                    index % suggestions.length
                  ];

                const availability =
                  getAvailabilityLabel(
                    availablePlatforms
                  );

                return (
                  <GameCard
                    key={game.id}
                    game={{
                      ...game,
                      genre: availability,
                      image: art.image,
                    }}
                    onSelect={
                      selectGameForCompatibility
                    }
                  />
                );
              })}

            </div>

          ) : activeTab === "Sugeridos" ? (

            <div className={styles.gameGrid}>

              {displayedSuggestions.map(
                (game) => (
                  <GameCard
                    key={game.id}
                    game={game}
                  />
                )
              )}

            </div>

          ) : (

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
          <span>PLAYSTATION</span>
          <span>XBOX</span>
          <span>NINTENDO</span>
        </footer>

      </div>
    </main>
  );
}