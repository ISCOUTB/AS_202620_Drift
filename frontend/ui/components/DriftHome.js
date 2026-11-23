"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  addConsole,
  addPc,
  checkFavoriteAlerts,
  setFavoriteTarget,
  deleteAccount,
  listDevices,
  listFavorites,
  loadAccount,
  logout,
  removeDevice,
  removeFavorite,
} from "../../application/usecases/account";
import { estimateCompatibility } from "../../application/usecases/estimateCompatibility";
import { searchGames } from "../../application/usecases/searchGames";
import {
  getFeaturedGames,
  getStores,
} from "../../application/usecases/showcase";

import {
  PLATFORMS,
  canEstimatePcCompatibility,
  describeCachedSources,
  filterByPlatforms,
  hasColombiaPrice,
  sortPricesForPurchase,
} from "../../domain/model/Game";
import { gamePageUrl, hasGameDetails } from "../../domain/model/GameDetails";
import {
  ANONYMOUS_ACCOUNT,
  pcProfileOfDevice,
} from "../../domain/model/Account";

import { fastApiAccountRepository } from "../../infrastructure/http/FastApiAccountRepository";
import { fastApiCompatibilityRepository } from "../../infrastructure/http/FastApiCompatibilityRepository";
import { fastApiGameRepository } from "../../infrastructure/http/FastApiGameRepository";
import { fastApiShowcaseRepository } from "../../infrastructure/http/FastApiShowcaseRepository";
import { browserGameHandoffRepository } from "../../infrastructure/storage/BrowserGameHandoffRepository";
import { browserPcProfileRepository } from "../../infrastructure/storage/BrowserPcProfileRepository";
import { browserPlatformFilterRepository } from "../../infrastructure/storage/BrowserPlatformFilterRepository";

import styles from "./DriftHome.module.css";
import AccountPanel, { AccountButton } from "./AccountPanel";
import FavoritesPanel from "./FavoritesPanel";
import { formatPrice } from "./PurchaseOptions";
import StoresPanel from "./StoresPanel";
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
  {
    name: "Xbox",
    detail: "Tienda de Xbox Colombia, en COP",
  },
];

// La lista de arriba es el respaldo: la portada muestra los más vendidos del
// momento, que cambian con el tiempo, y solo usa esta si la API no responde.
const HERO_GAMES = 4;
const QUICK_LIST_GAMES = 6;

const FEATURED_INTERVAL_MS = 7000;
const CARD_PRICE_LIMIT = 3;

// Juegos de cada búsqueda que se comprueban solos contra «Mi PC».
const COMPATIBILITY_CHECK_LIMIT = 8;

const COMPATIBILITY_BADGES = {
  "Compatible": ["Tu PC: recomendado", "badgeGood"],
  "Compatible con limitaciones": ["Tu PC: mínimo", "badgeWarn"],
  "No compatible": ["Tu PC: no alcanza", "badgeBad"],
};


function getSortedPrices(prices = {}) {
  return sortPricesForPurchase(prices);
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


/** Carátula vertical; si no existe, la imagen horizontal y luego un fondo. */
function getPosterBackground(game) {
  const covers = [`url("${game.image}")`];

  if (game.header) {
    covers.push(`url("${game.header}")`);
  }

  covers.push("linear-gradient(135deg, #3a1a5c, #1d2a7c)");

  return covers.join(", ");
}


function PosterCard({ game, onOpen }) {
  return (
    <button
      type="button"
      className={styles.posterCard}
      onClick={() => onOpen(game)}
      title={`Ver ${game.name}`}
    >
      <span
        className={styles.posterArt}
        style={{ backgroundImage: getPosterBackground(game) }}
      >
        <span className={styles.posterAction}>Ver juego</span>
      </span>

      <strong>{game.name}</strong>

      <small>{game.genre}</small>
    </button>
  );
}


function ResultCard({ game, onOpen, compatibility }) {
  const prices = getSortedPrices(game.prices);
  const bestPrice = prices[0] || null;
  const visiblePrices = prices.slice(0, CARD_PRICE_LIMIT);
  const hiddenPrices = prices.length - visiblePrices.length;

  const badge =
    compatibility?.state === "done"
      ? COMPATIBILITY_BADGES[compatibility.data.status]
      : null;

  return (
    <article className={styles.resultCard}>
      <div
        className={styles.resultArt}
        style={{ backgroundImage: getCoverBackground(game) }}
      >
        <span className={styles.resultBadge}>
          {game.availability}
        </span>

        {badge && (
          <span
            className={`${styles.compatibilityBadge} ${styles[badge[1]]}`}
          >
            {badge[0]}
          </span>
        )}
      </div>

      <div className={styles.resultBody}>
        <h3>{game.name}</h3>

        {bestPrice ? (
          <>
            <div className={styles.bestLine}>
              <div>
                <small>{bestPrice[0]}</small>

                <strong>{formatPrice(bestPrice[1])}</strong>

                {game.discounts?.[bestPrice[0]] > 0 && (
                  <span className={styles.discountBadge}>
                    -{game.discounts[bestPrice[0]]}%
                  </span>
                )}
              </div>

              <span className={styles.bestTag}>
                {hasColombiaPrice(bestPrice[0])
                  ? "Más barato"
                  : "Referencia EE. UU."}
              </span>
            </div>

            <ul className={styles.priceList}>
              {visiblePrices.slice(1).map(([platform, price]) => (
                <li key={platform}>
                  <span>{platform}</span>

                  <span>
                    {game.discounts?.[platform] > 0 && (
                      <em className={styles.discountInline}>
                        -{game.discounts[platform]}%
                      </em>
                    )}

                    {formatPrice(price)}
                  </span>
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

        {describeCachedSources(game).length > 0 && (
          <p className={styles.unavailableNotice}>
            Precios guardados de{" "}
            {describeCachedSources(game).join(", ")}.
          </p>
        )}

        <Link
          href={gamePageUrl(game)}
          className={styles.resultAction}
          onClick={() => onOpen(game)}
        >
          Ver juego, tiendas y compatibilidad →
        </Link>
      </div>
    </article>
  );
}


/** Cuántos favoritos tienen alerta; cero si todavía no se revisaron. */
function countAlerts(alerts) {
  return alerts?.count ?? 0;
}


/** Cabecera: menú lateral, logo, buscador y cuenta. */
function TopBar({
  sidebarHidden,
  onToggleSidebar,
  onHome,
  query,
  onQueryChange,
  onSubmit,
  loading,
  account,
  accountOpen,
  onToggleAccount,
}) {
  return (
    <header className={styles.topBar}>
      <div className={styles.brand}>
        <button
          type="button"
          className={styles.menuButton}
          aria-label={sidebarHidden ? "Mostrar panel lateral" : "Ocultar panel lateral"}
          aria-expanded={!sidebarHidden}
          onClick={onToggleSidebar}
        >
          <span />
          <span />
          <span />
        </button>

        <a
          className={styles.logo}
          href="#inicio"
          aria-label="DRIFT, ir al inicio"
          onClick={onHome}
        >
          <span>DR</span>
          <span>IFT</span>
        </a>
      </div>

      <form className={styles.searchForm} onSubmit={onSubmit}>
        <span className={styles.searchIcon} aria-hidden="true" />

        <input
          id="game-search"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Busca un videojuego"
          aria-label="Buscar videojuego"
        />

        <button type="submit" disabled={loading}>
          {loading ? "Buscando…" : "Buscar"}
        </button>
      </form>

      {account.loginAvailable ? (
        <AccountButton
          account={account}
          loginUrl={fastApiAccountRepository.loginUrl()}
          isOpen={accountOpen}
          onToggle={onToggleAccount}
        />
      ) : (
        <div className={styles.profileChip}>
          <span className={styles.profileMoon} aria-hidden="true" />

          <span className={styles.profileName}>Jugador</span>

          <span className={styles.profileAvatar}>JD</span>
        </div>
      )}
    </header>
  );
}


/** Panel lateral: juegos listos para comparar y tiendas conectadas. */
function QuickSidebar({ games, onPick }) {
  return (
    <aside className={styles.sidebar}>
      <section className={styles.panel}>
        <h2 className={styles.panelTitle}>Listos para comparar</h2>

        <ul className={styles.quickList}>
          {games.map((game) => (
            <li key={game.id}>
              <button type="button" onClick={() => onPick(game)}>
                <span
                  className={styles.quickThumb}
                  style={{ backgroundImage: getPosterBackground(game) }}
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
        <h2 className={styles.panelTitle}>Tiendas conectadas</h2>

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
  );
}


/** Navegación principal del inicio; «Explorar» abre su propia página. */
function MainNav({
  activeTab,
  resultsCount,
  showStores,
  showFavorites,
  authenticated,
  favoritesCount,
  alerts,
  onHome,
  onResults,
  onStores,
  onFavorites,
}) {
  const activeIf = (condition) => (condition ? styles.navActive : "");
  const alertCount = countAlerts(alerts);
  const count = (value) => (value ? `(${value})` : "");

  return (
    <nav className={styles.nav} aria-label="Navegación principal">
      <button type="button" onClick={onHome} className={activeIf(activeTab === "Sugeridos")}>
        Inicio
      </button>

      <button type="button" onClick={onResults} className={activeIf(activeTab === "Resultados")}>
        Resultados {count(resultsCount)}
      </button>

      <Link href="/explorar">Explorar</Link>

      <button type="button" onClick={onStores} className={activeIf(showStores)}>
        Tiendas
      </button>

      {authenticated && (
        <button type="button" onClick={onFavorites} className={activeIf(showFavorites)}>
          Favoritos {count(favoritesCount)}
          {alertCount > 0 && (
            <span
              className={styles.alertDot}
              aria-label={`${alertCount} con alerta de precio`}
            >
              {alertCount}
            </span>
          )}
        </button>
      )}
    </nav>
  );
}


/** Aviso de favoritos que llegaron a su precio o bajaron. */
function AlertBanner({ visible, alerts, onOpen, onClose }) {
  const count = countAlerts(alerts);

  if (!visible || count <= 0) {
    return null;
  }

  return (
    <output className={styles.alertBanner}>
      <span>
        🔔{" "}
        {count === 1
          ? "Uno de tus favoritos llegó a tu precio o bajó."
          : `${count} de tus favoritos llegaron a tu precio o bajaron.`}
      </span>

      <button type="button" onClick={onOpen}>
        Ver favoritos
      </button>

      <button
        type="button"
        className={styles.alertBannerClose}
        aria-label="Cerrar el aviso"
        onClick={onClose}
      >
        ×
      </button>
    </output>
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


  // Equipo del usuario, guardado en su navegador.
  const [pcProfile, setPcProfile] =
    useState(null);

  // Resultado de compatibilidad por id de juego.
  const [compatibilityByGame, setCompatibilityByGame] =
    useState({});

  // Cuenta de Google y dispositivos registrados (ADR-0017).
  const [account, setAccount] =
    useState(ANONYMOUS_ACCOUNT);

  const [devices, setDevices] =
    useState([]);

  const [devicesError, setDevicesError] =
    useState("");

  // Juegos guardados por quien inició sesión (ADR-0020).
  const [favorites, setFavorites] =
    useState([]);

  const [favoritesError, setFavoritesError] =
    useState("");

  const [favoriteBusy, setFavoriteBusy] =
    useState(false);

  const router = useRouter();

  // Precio de hoy y alertas de los favoritos (ADR-0021).
  const [favoriteAlerts, setFavoriteAlerts] =
    useState(null);

  const [alertsDismissed, setAlertsDismissed] =
    useState(false);

  const [accountOpen, setAccountOpen] =
    useState(false);

  const [activePcDeviceId, setActivePcDeviceId] =
    useState(null);

  const [loginNotice, setLoginNotice] =
    useState("");

  // Plataformas que tiene el usuario; vacío significa «todas».
  const [platformFilter, setPlatformFilter] =
    useState([]);

  const visibleGames = useMemo(
    () => filterByPlatforms(games, platformFilter),
    [games, platformFilter],
  );


  const [sidebarHidden, setSidebarHidden] =
    useState(false);

  const [featuredIndex, setFeaturedIndex] =
    useState(0);

  const posterRowRef = useRef(null);
  const catalogRef = useRef(null);

  // Más vendidos del momento, por categoría y en general; llegan de la API.
  const [featuredByCategory, setFeaturedByCategory] =
    useState({});

  // Tiendas conectadas; se cargan al abrir la pestaña «Tiendas».
  const [storeDirectory, setStoreDirectory] =
    useState(null);


  // Se pide cada categoría una sola vez, cuando se elige.
  useEffect(() => {
    if (featuredByCategory[selectedCategory]) {
      return undefined;
    }

    let cancelled = false;

    void getFeaturedGames(
      selectedCategory === "Todo" ? null : selectedCategory,
      fastApiShowcaseRepository,
    ).then((featured) => {
      if (!cancelled) {
        setFeaturedByCategory((current) => ({
          ...current,
          [selectedCategory]: featured,
        }));
      }
    });

    return () => {
      cancelled = true;
    };
  }, [selectedCategory, featuredByCategory]);


  // Los populares del momento; la lista incluida solo si la API no responde.
  const popularGames = featuredByCategory.Todo?.length
    ? featuredByCategory.Todo
    : suggestions;

  const heroGames = popularGames.slice(0, HERO_GAMES);


  const displayedSuggestions = useMemo(() => {
    if (selectedCategory === "Todo") {
      return popularGames;
    }

    if (featuredByCategory[selectedCategory]?.length) {
      return featuredByCategory[selectedCategory];
    }

    return suggestions.filter((game) =>
      game.genre.includes(selectedCategory)
    );
  }, [selectedCategory, featuredByCategory, popularGames]);


  // Al cambiar de categoría el carrusel vuelve al principio.
  useEffect(() => {
    posterRowRef.current?.scrollTo({ left: 0 });
  }, [selectedCategory]);


  useEffect(() => {
    const timer = setInterval(() => {
      setFeaturedIndex((current) => (current + 1) % HERO_GAMES);
    }, FEATURED_INTERVAL_MS);

    return () => clearInterval(timer);
  }, []);


  const refreshDevices = async () => {
    try {
      setDevices(await listDevices(fastApiAccountRepository));
      setDevicesError("");
    } catch (error_) {
      setDevicesError(error_.message);
    }
  };


  const refreshFavorites = async () => {
    try {
      setFavorites(await listFavorites(fastApiAccountRepository));
      setFavoritesError("");
    } catch (error_) {
      setFavoritesError(error_.message);
    }
  };


  // Las alertas son un extra: si fallan, los favoritos se ven igual.
  const refreshFavoriteAlerts = async () => {
    try {
      setFavoriteAlerts(await checkFavoriteAlerts(fastApiAccountRepository));
    } catch {
      setFavoriteAlerts(null);
    }
  };


  // Al cargar: quién está usando DRIFT y qué dispositivos registró.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const result = params.get("login");
    const wantsFavorites = params.get("vista") === "favoritos";
    const wantsAccount = params.has("cuenta");

    if (result) {
      // El resultado del inicio de sesión no se queda en la dirección.
      window.history.replaceState(null, "", window.location.pathname);

      if (result === "ok") {
        setAccountOpen(true);
      } else {
        setLoginNotice(
          result === "unavailable"
            ? "No pudimos iniciar sesión en este momento. Inténtalo más tarde."
            : "No se pudo iniciar sesión con Google. Inténtalo de nuevo.",
        );
      }
    }

    let cancelled = false;

    void loadAccount(fastApiAccountRepository).then((loaded) => {
      if (cancelled) {
        return;
      }

      setAccount(loaded);

      if (loaded.authenticated) {
        void refreshDevices();
        void refreshFavorites();
        void refreshFavoriteAlerts();

        if (wantsFavorites) {
          openFavorites();
        } else if (wantsAccount) {
          setAccountOpen(true);
        }
      }
    });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);


  // «Mi PC» se edita en la página de cada juego; aquí solo se lee para las
  // insignias de compatibilidad de los resultados.
  useEffect(() => {
    setPcProfile(browserPcProfileRepository.load());
    setPlatformFilter(browserPlatformFilterRepository.load());
  }, []);


  useEffect(() => {
    if (!pcProfile) {
      setCompatibilityByGame({});
      return undefined;
    }

    // Solo los juegos de PC con requisitos conocidos (los de Steam).
    const gamesToCheck = visibleGames
      .filter(canEstimatePcCompatibility)
      .slice(0, COMPATIBILITY_CHECK_LIMIT);

    let cancelled = false;

    const store = (gameId, entry) => {
      if (!cancelled) {
        setCompatibilityByGame((current) => ({
          ...current,
          [gameId]: entry,
        }));
      }
    };

    setCompatibilityByGame(
      Object.fromEntries(
        gamesToCheck.map((game) => [game.id, { state: "loading" }]),
      ),
    );

    gamesToCheck.forEach((game) => {
      estimateCompatibility(
        game.id,
        pcProfile,
        fastApiCompatibilityRepository,
      )
        .then((data) => store(game.id, { state: "done", data }))
        .catch((compatibilityError) =>
          store(game.id, {
            state: "error",
            message: compatibilityError.message,
          }),
        );
    });

    return () => {
      cancelled = true;
    };
  }, [visibleGames, pcProfile]);


  const runSearch = async (term) => {
    setLoading(true);
    setError("");
    setActiveTab("Resultados");

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


  // Desde «Explorar» se llega con ?q= (comparar un juego), ?vista=tiendas,
  // ?vista=favoritos o ?cuenta=1. La dirección queda limpia después.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const term = params.get("q")?.trim();
    const view = params.get("vista");

    if (!term && !view && !params.has("cuenta")) {
      return;
    }

    window.history.replaceState(null, "", window.location.pathname);

    if (term) {
      setQuery(term);
      void runSearch(term);
    } else if (view === "tiendas") {
      openStores();
    }
    // Favoritos y cuenta esperan a saber si hay sesión (efecto de abajo).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);


  // La búsqueda entrega el juego a su página para no consultar de nuevo las tiendas.
  const openGame = (game) => {
    browserGameHandoffRepository.give(game);
  };


  // Portada y panel lateral: los juegos de Steam abren su página; los de la
  // lista incluida, que no tienen identificador de Steam, se buscan.
  const openSuggestion = (game) => {
    if (hasGameDetails(game.id)) {
      router.push(gamePageUrl(game));
    } else {
      searchSuggestion(game.name);
    }
  };


  const togglePlatform = (platform) => {
    const next = platformFilter.includes(platform)
      ? platformFilter.filter((current) => current !== platform)
      : PLATFORMS.filter(
          (current) =>
            current === platform || platformFilter.includes(current),
        );

    browserPlatformFilterRepository.save(next);
    setPlatformFilter(next);
  };


  const applyPlatforms = (platforms) => {
    browserPlatformFilterRepository.save(platforms);
    setPlatformFilter(platforms);
  };


  const usePcDevice = (device) => {
    const profile = pcProfileOfDevice(device);

    if (profile) {
      browserPcProfileRepository.save(profile);
      setPcProfile(profile);
      setActivePcDeviceId(device.id);
    }
  };


  const handleAddConsole = async (kind, name) => {
    await addConsole(kind, name, fastApiAccountRepository);
    await refreshDevices();
  };


  const handleAddPc = async (name) => {
    const saved = await addPc(name, pcProfile, fastApiAccountRepository);

    setActivePcDeviceId(saved.id);
    await refreshDevices();
  };


  const handleRemoveDevice = async (device) => {
    await removeDevice(device.id, fastApiAccountRepository);

    if (device.id === activePcDeviceId) {
      setActivePcDeviceId(null);
    }

    await refreshDevices();
  };


  const leaveAccount = () => {
    setAccount({ ...ANONYMOUS_ACCOUNT, loginAvailable: true });
    setDevices([]);
    setFavorites([]);
    setFavoritesError("");
    setFavoriteAlerts(null);
    setActivePcDeviceId(null);
    setAccountOpen(false);

    if (activeTab === "Favoritos") {
      setActiveTab("Sugeridos");
    }
  };


  const handleRemoveFavorite = async (favorite) => {
    setFavoriteBusy(true);

    try {
      await removeFavorite(favorite.gameId, fastApiAccountRepository);
      await refreshFavorites();
    } catch (error_) {
      setFavoritesError(error_.message);
    } finally {
      setFavoriteBusy(false);
    }
  };


  const openFavorites = () => {
    setActiveTab("Favoritos");
    setError("");
    setAlertsDismissed(true);

    // El servidor guarda cada precio una hora: volver a pedir es barato.
    void refreshFavoriteAlerts();
  };


  // Lanza el error para que el formulario de la tarjeta lo muestre.
  const handleSetTarget = async (favorite, text) => {
    await setFavoriteTarget(favorite.gameId, text, fastApiAccountRepository);
    await refreshFavorites();
    await refreshFavoriteAlerts();
  };


  // La página del favorito trae sus precios de hoy en todas las tiendas.
  const openFavorite = (favorite) => {
    router.push(gamePageUrl({ id: favorite.gameId, name: favorite.name }));
  };


  const handleLogout = async () => {
    await logout(fastApiAccountRepository);
    leaveAccount();
  };


  const handleDeleteAccount = async () => {
    await deleteAccount(fastApiAccountRepository);
    leaveAccount();
  };


  const clearPlatformFilter = () => {
    browserPlatformFilterRepository.save([]);
    setPlatformFilter([]);
  };


  const scrollPosters = (direction) => {
    posterRowRef.current?.scrollBy({
      left: direction * 340,
      behavior: "smooth",
    });
  };


  const featuredGame = heroGames[featuredIndex % heroGames.length];


  const goHome = (event) => {
    event?.preventDefault();

    setActiveTab("Sugeridos");
    setSelectedCategory("Todo");
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };


  const openStores = () => {
    setActiveTab("Tiendas");
    setError("");

    if (!storeDirectory) {
      void getStores(fastApiShowcaseRepository).then(setStoreDirectory);
    }
  };

  const showSuggestions = activeTab === "Sugeridos";
  const showStores = activeTab === "Tiendas";
  const showFavorites = activeTab === "Favoritos" && account.authenticated;

  const showSearch = activeTab === "Resultados";
  const showLoading = showSearch && loading;
  const showResults = showSearch && !loading && games.length > 0;
  const showEmptyState = showSearch && !loading && games.length === 0;


  return (
    <main className={styles.pageShell}>
      <WaveBackdrop />

      <div className={styles.app}>

        <TopBar
          sidebarHidden={sidebarHidden}
          onToggleSidebar={() => setSidebarHidden((hidden) => !hidden)}
          onHome={goHome}
          query={query}
          onQueryChange={setQuery}
          onSubmit={submitSearch}
          loading={loading}
          account={account}
          accountOpen={accountOpen}
          onToggleAccount={() => setAccountOpen((open) => !open)}
        />


        <div
          className={`${styles.layout} ${
            sidebarHidden ? styles.layoutWide : ""
          }`}
        >

          {!sidebarHidden && (
            <QuickSidebar
              games={popularGames.slice(0, QUICK_LIST_GAMES)}
              onPick={openSuggestion}
            />
          )}


          <div className={styles.content}>

            <MainNav
              activeTab={activeTab}
              resultsCount={games.length}
              showStores={showStores}
              showFavorites={showFavorites}
              authenticated={account.authenticated}
              favoritesCount={favorites.length}
              alerts={favoriteAlerts}
              onHome={() => {
                setActiveTab("Sugeridos");
                setError("");
              }}
              onResults={() => setActiveTab("Resultados")}
              onStores={openStores}
              onFavorites={openFavorites}
            />


            {loginNotice && (
              <p className={styles.unavailableNotice} role="alert">
                {loginNotice}
              </p>
            )}

            <AlertBanner
              visible={account.authenticated && !alertsDismissed && !showFavorites}
              alerts={favoriteAlerts}
              onOpen={openFavorites}
              onClose={() => setAlertsDismissed(true)}
            />

            {account.authenticated && accountOpen && (
              <AccountPanel
                account={account}
                devices={devices}
                devicesError={devicesError}
                browserPcProfile={pcProfile}
                activePcDeviceId={activePcDeviceId}
                onAddConsole={handleAddConsole}
                onAddPc={handleAddPc}
                onUsePc={usePcDevice}
                onRemoveDevice={handleRemoveDevice}
                onApplyPlatforms={applyPlatforms}
                onLogout={handleLogout}
                onDeleteAccount={handleDeleteAccount}
                onClose={() => setAccountOpen(false)}
              />
            )}

            {activeTab === "Sugeridos" && (
              <section
                className={styles.hero}
                id="inicio"
              >
                <div
                  key={featuredGame.id}
                  className={styles.heroArt}
                  style={{
                    // Si el juego no tiene imagen panorámica, la horizontal.
                    backgroundImage: featuredGame.header
                      ? `url("${featuredGame.hero}"), url("${featuredGame.header}")`
                      : `url("${featuredGame.hero}")`,
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
                    {heroGames.map((game, index) => (
                      <button
                        type="button"
                        key={game.id}
                        aria-label={`Destacar ${game.name}`}
                        className={
                          index === featuredIndex % heroGames.length
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
                    onClick={() => openSuggestion(featuredGame)}
                  >
                    <small>{featuredGame.name}</small>

                    <span>Ver juego</span>
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
                    <button
                      type="button"
                      className={`${styles.posterArrow} ${styles.posterArrowLeft}`}
                      aria-label="Ver juegos anteriores"
                      onClick={() => scrollPosters(-1)}
                    >
                      ‹
                    </button>

                    <div
                      className={styles.posterRow}
                      ref={posterRowRef}
                    >
                      {displayedSuggestions.map((game) => (
                        <PosterCard
                          key={game.id}
                          game={game}
                          onOpen={openSuggestion}
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

              {showStores && <StoresPanel directory={storeDirectory} />}

              {showFavorites && (
                <FavoritesPanel
                  favorites={favorites}
                  alerts={favoriteAlerts}
                  onSetTarget={handleSetTarget}
                  error={favoritesError}
                  busy={favoriteBusy}
                  onSearch={openFavorite}
                  onRemove={handleRemoveFavorite}
                />
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
                      Resultados ({visibleGames.length})
                    </h2>

                    <fieldset
                      className={styles.platformFilter}
                      aria-label="Filtrar por plataforma"
                    >
                      <span className={styles.platformFilterLabel}>
                        Tengo:
                      </span>

                      <button
                        type="button"
                        className={`${styles.platformChip} ${
                          platformFilter.length === 0
                            ? styles.platformChipActive
                            : ""
                        }`}
                        aria-pressed={platformFilter.length === 0}
                        onClick={clearPlatformFilter}
                      >
                        Todas
                      </button>

                      {PLATFORMS.map((platform) => {
                        const isActive =
                          platformFilter.includes(platform);

                        return (
                          <button
                            type="button"
                            key={platform}
                            className={`${styles.platformChip} ${
                              isActive ? styles.platformChipActive : ""
                            }`}
                            aria-pressed={isActive}
                            onClick={() => togglePlatform(platform)}
                          >
                            {platform}
                          </button>
                        );
                      })}
                    </fieldset>
                  </div>

                  {visibleGames.length === 0 && (
                    <p className={styles.emptyState}>
                      Ningún resultado se vende para{" "}
                      {platformFilter.join(" o ")}. Elige «Todas» para ver
                      las demás tiendas.
                    </p>
                  )}

                  <div className={styles.gameGrid}>

                    {visibleGames.map((game) => {

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
                          compatibility={
                            compatibilityByGame[game.id]
                          }
                          onOpen={openGame}
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
              <span>XBOX</span>

              <button
                type="button"
                className={styles.platformsLink}
                onClick={() => {
                  openStores();
                  catalogRef.current?.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                  });
                }}
              >
                Ver todas las tiendas
              </button>
            </footer>

            {/* Aviso de privacidad (docs/seguridad/privacidad.md, Ley 1581 de 2012). */}
            <details className={styles.privacyNotice}>
              <summary>Privacidad</summary>
              <p>
                Puedes usar DRIFT sin registrarte. Para funcionar y
                protegerse contra el abuso, el servicio y sus proveedores de
                alojamiento (el servidor de la Universidad Tecnológica de
                Bolívar) registran tu dirección IP
                y las búsquedas que haces, solo para operar y diagnosticar el
                servicio. El texto de las búsquedas se conserva hasta 72 horas,
                sin asociarlo a ti, como copia de respaldo de las tiendas. Sin
                sesión, el perfil de tu PC se guarda únicamente en tu navegador.
              </p>
              <p>
                Si inicias sesión con Google, DRIFT guarda tu nombre, tu
                correo y tu foto de perfil, los dispositivos que registres y
                los juegos que guardes en favoritos, para mostrarlos cuando
                vuelvas. Solo usa las cookies necesarias para iniciar y
                mantener tu sesión. Puedes borrar tu cuenta y todos esos
                datos desde «Mi cuenta». Al usar el sitio aceptas este
                tratamiento, conforme a la Ley 1581 de 2012.
              </p>
              <p>
                Consultas sobre tus datos:{" "}
                <a
                  href="https://github.com/ISCOUTB/AS_202620_Drift/issues"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  abre un caso en el repositorio del proyecto
                </a>
                .
              </p>
            </details>

          </div>
        </div>
      </div>
    </main>
  );
}
