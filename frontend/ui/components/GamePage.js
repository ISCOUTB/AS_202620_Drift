"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  listDevices,
  listFavorites,
  loadAccount,
  removeFavorite,
  saveFavorite,
} from "../../application/usecases/account";
import { estimateCompatibility } from "../../application/usecases/estimateCompatibility";
import { getGameDetails, loadGamePrices } from "../../application/usecases/gamePage";
import { getPriceHistory } from "../../application/usecases/getPriceHistory";
import { getRecommendation } from "../../application/usecases/getRecommendation";
import {
  listGraphicsCards,
  listProcessors,
} from "../../application/usecases/listHardwareOptions";

import { ANONYMOUS_ACCOUNT } from "../../domain/model/Account";
import { findFavorite, priceChangeSince } from "../../domain/model/Favorite";
import {
  canEstimatePcCompatibility,
  filterByPlatforms,
  hasColombiaPrice,
  sortPricesForPurchase,
} from "../../domain/model/Game";
import { mediaOf, steamIdOf } from "../../domain/model/GameDetails";
import { canHavePriceHistory } from "../../domain/model/PriceHistory";
import {
  devicesForRecommendation,
  recommendationKey,
} from "../../domain/model/Recommendation";

import { fastApiAccountRepository } from "../../infrastructure/http/FastApiAccountRepository";
import { fastApiCompatibilityRepository } from "../../infrastructure/http/FastApiCompatibilityRepository";
import { fastApiGameDetailsRepository } from "../../infrastructure/http/FastApiGameDetailsRepository";
import { fastApiGameRepository } from "../../infrastructure/http/FastApiGameRepository";
import {
  fastApiCpuCatalogRepository,
  fastApiGpuCatalogRepository,
} from "../../infrastructure/http/FastApiHardwareCatalogRepository";
import { fastApiPriceHistoryRepository } from "../../infrastructure/http/FastApiPriceHistoryRepository";
import { fastApiRecommendationRepository } from "../../infrastructure/http/FastApiRecommendationRepository";
import { browserGameHandoffRepository } from "../../infrastructure/storage/BrowserGameHandoffRepository";
import { browserPcProfileRepository } from "../../infrastructure/storage/BrowserPcProfileRepository";
import { browserPlatformFilterRepository } from "../../infrastructure/storage/BrowserPlatformFilterRepository";

import CompatibilityPanel from "./CompatibilityPanel";
import driftStyles from "./DriftHome.module.css";
import styles from "./GamePage.module.css";
import MediaGallery from "./MediaGallery";
import PriceHistoryPanel from "./PriceHistoryPanel";
import PurchaseOptions, { formatPrice } from "./PurchaseOptions";
import RecommendationPanel from "./RecommendationPanel";
import SiteHeader from "./SiteHeader";
import WaveBackdrop from "./WaveBackdrop";

const STEAM_APP = "https://store.steampowered.com/app";

/** Cuenta, dispositivos y favoritos de quien navega. */
function useAccount() {
  const [account, setAccount] = useState(ANONYMOUS_ACCOUNT);
  const [devices, setDevices] = useState([]);
  const [favorites, setFavorites] = useState([]);

  useEffect(() => {
    let cancelled = false;

    void loadAccount(fastApiAccountRepository).then(async (loaded) => {
      if (cancelled) {
        return;
      }

      setAccount(loaded);

      if (!loaded.authenticated) {
        return;
      }

      // Sin dispositivos o favoritos la página sigue igual.
      const [savedDevices, savedFavorites] = await Promise.allSettled([
        listDevices(fastApiAccountRepository),
        listFavorites(fastApiAccountRepository),
      ]);

      if (!cancelled) {
        if (savedDevices.status === "fulfilled") setDevices(savedDevices.value);
        if (savedFavorites.status === "fulfilled") setFavorites(savedFavorites.value);
      }
    });

    return () => {
      cancelled = true;
    };
  }, []);

  const refreshFavorites = async () => {
    setFavorites(await listFavorites(fastApiAccountRepository));
  };

  return { account, devices, favorites, refreshFavorites };
}

/** Perfil del PC, plataformas y catálogos de hardware del navegador. */
function useBrowserSetup() {
  const [pcProfile, setPcProfile] = useState(null);
  const [platformFilter, setPlatformFilter] = useState([]);
  const [gpuOptions, setGpuOptions] = useState([]);
  const [cpuOptions, setCpuOptions] = useState([]);

  useEffect(() => {
    setPcProfile(browserPcProfileRepository.load());
    setPlatformFilter(browserPlatformFilterRepository.load());

    let cancelled = false;

    // Estas listas nunca rechazan: ante un fallo devuelven la lista incluida.
    void listGraphicsCards(fastApiGpuCatalogRepository).then((options) => {
      if (!cancelled) setGpuOptions(options);
    });

    void listProcessors(fastApiCpuCatalogRepository).then((options) => {
      if (!cancelled) setCpuOptions(options);
    });

    return () => {
      cancelled = true;
    };
  }, []);

  const savePcProfile = (profile) => {
    browserPcProfileRepository.save(profile);
    setPcProfile(profile);
  };

  return { pcProfile, savePcProfile, platformFilter, gpuOptions, cpuOptions };
}

function Facts({ details }) {
  const facts = [
    ["Lanzamiento", details.comingSoon ? `Próximamente${details.releaseDate ? ` · ${details.releaseDate}` : ""}` : details.releaseDate],
    ["Desarrollador", details.developers.join(", ")],
    ["Editor", details.publishers.join(", ")],
  ].filter(([, value]) => value);

  return (
    <dl className={styles.facts}>
      {facts.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

/** Mejor precio de Colombia, o el de referencia si no hay de Colombia. */
function BestPrice({ game }) {
  const [best] = sortPricesForPurchase(game?.prices);

  if (!best) {
    return null;
  }

  const [store, price] = best;
  const discount = game.discounts?.[store];

  return (
    <a className={styles.bestPrice} href="#tiendas">
      <span>
        <small>{hasColombiaPrice(store) ? "Mejor precio" : "Precio de referencia"}</small>
        <strong>{formatPrice(price)}</strong>
      </span>

      <span className={styles.bestPriceStore}>
        {discount > 0 && <em>-{discount}%</em>}
        en {store} · ver tiendas ↓
      </span>
    </a>
  );
}

export default function GamePage({ gameId, initialName }) {
  const router = useRouter();
  const { account, devices, favorites, refreshFavorites } = useAccount();
  const { pcProfile, savePcProfile, platformFilter, gpuOptions, cpuOptions } = useBrowserSetup();

  const steamId = steamIdOf(gameId);

  // Ficha de Steam: { state: "loading" | "done" | "error", data }.
  const [details, setDetails] = useState({ state: steamId ? "loading" : "done", data: null });
  // Juego con sus precios: { state, data }.
  const [prices, setPrices] = useState({ state: "loading", data: null });
  const [showAllStores, setShowAllStores] = useState(false);

  const [history, setHistory] = useState(null);
  const [recommendation, setRecommendation] = useState(null);
  const [compatibility, setCompatibility] = useState(null);

  const [favoriteBusy, setFavoriteBusy] = useState(false);
  const [favoriteError, setFavoriteError] = useState("");

  // El nombre de la dirección permite buscar los precios sin esperar la ficha.
  const searchName = initialName || details.data?.name || "";
  const name = details.data?.name || initialName || "";

  useEffect(() => {
    if (!steamId) {
      return undefined;
    }

    let cancelled = false;

    getGameDetails(steamId, fastApiGameDetailsRepository)
      .then((data) => !cancelled && setDetails({ state: "done", data }))
      .catch(() => !cancelled && setDetails({ state: "error", data: null }));

    return () => {
      cancelled = true;
    };
  }, [steamId]);

  // Sin nombre en la dirección hay que esperar la ficha para saber qué buscar.
  const waitingForName = !searchName && details.state === "loading";

  useEffect(() => {
    if (!searchName) {
      if (!waitingForName) {
        setPrices({ state: "done", data: null });
      }

      return undefined;
    }

    let cancelled = false;

    setPrices({ state: "loading", data: null });

    loadGamePrices(
      { gameId, name: searchName },
      {
        handoffRepository: browserGameHandoffRepository,
        gameRepository: fastApiGameRepository,
      },
    )
      .then((data) => !cancelled && setPrices({ state: "done", data }))
      .catch(() => !cancelled && setPrices({ state: "error", data: null }));

    return () => {
      cancelled = true;
    };
  }, [gameId, searchName, waitingForName]);

  const game = prices.data;

  // Con el filtro «Tengo:» solo se ven las tiendas de esas plataformas.
  const visibleGame = useMemo(() => {
    if (!game || showAllStores || !platformFilter.length) {
      return game;
    }

    return filterByPlatforms([game], platformFilter)[0] ?? { ...game, prices: {}, links: {}, discounts: {} };
  }, [game, platformFilter, showAllStores]);

  const hiddenStores =
    game && visibleGame ? Object.keys(game.prices).length - Object.keys(visibleGame.prices).length : 0;

  // El historial se pide una vez por juego.
  useEffect(() => {
    if (!game || !canHavePriceHistory(game)) {
      setHistory(null);
      return undefined;
    }

    let cancelled = false;

    setHistory({ state: "loading" });

    getPriceHistory(game.id, fastApiPriceHistoryRepository)
      .then((data) => !cancelled && setHistory({ state: "done", data }))
      .catch(() => !cancelled && setHistory({ state: "error" }));

    return () => {
      cancelled = true;
    };
  }, [game]);

  // La recomendación cambia con los dispositivos y las plataformas.
  useEffect(() => {
    if (!visibleGame || Object.keys(visibleGame.prices).length === 0) {
      setRecommendation(null);
      return undefined;
    }

    const ownDevices = devicesForRecommendation({
      accountDevices: account.authenticated ? devices : [],
      pcProfile,
      platformFilter,
    });

    const key = recommendationKey(visibleGame, ownDevices);
    let cancelled = false;

    setRecommendation((current) => (current?.key === key ? current : { key, state: "loading" }));

    getRecommendation(visibleGame, ownDevices, fastApiRecommendationRepository)
      .then((data) => !cancelled && setRecommendation({ key, state: "done", data }))
      .catch(() => !cancelled && setRecommendation({ key, state: "error" }));

    return () => {
      cancelled = true;
    };
  }, [visibleGame, account, devices, pcProfile, platformFilter]);

  // La compatibilidad con «Mi PC», para juegos de PC con ficha de Steam.
  const compatibilityGame = game ?? (steamId ? { id: steamId, platforms: [] } : null);

  useEffect(() => {
    if (!pcProfile || !canEstimatePcCompatibility(compatibilityGame)) {
      setCompatibility(null);
      return undefined;
    }

    let cancelled = false;

    setCompatibility({ state: "loading" });

    estimateCompatibility(compatibilityGame.id, pcProfile, fastApiCompatibilityRepository)
      .then((data) => !cancelled && setCompatibility({ state: "done", data }))
      .catch((error) => !cancelled && setCompatibility({ state: "error", message: error.message }));

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [compatibilityGame?.id, compatibilityGame?.platforms?.join(), pcProfile]);

  const favorite = findFavorite(favorites, game);
  const priceChange = priceChangeSince(favorite, game);

  const toggleFavorite = async () => {
    setFavoriteBusy(true);
    setFavoriteError("");

    try {
      if (favorite) {
        await removeFavorite(game.id, fastApiAccountRepository);
      } else {
        await saveFavorite(game, fastApiAccountRepository);
      }

      await refreshFavorites();
    } catch (error) {
      setFavoriteError(error.message);
    } finally {
      setFavoriteBusy(false);
    }
  };

  const media = mediaOf(details.data);
  const storeUrl = steamId ? `${STEAM_APP}/${steamId}` : null;
  const notFound = details.state !== "loading" && prices.state !== "loading" && !details.data && !game;
  const heroBackground = details.data?.backgroundImage;
  // Sin llave de IsThereAnyDeal el servidor no ofrece historial: no se muestra.
  const showHistory =
    game &&
    canHavePriceHistory(game) &&
    !(history?.state === "done" && history.data.reason === "not_configured");

  return (
    <main className={driftStyles.pageShell}>
      <WaveBackdrop />

      <div className={driftStyles.app}>
        <SiteHeader account={account} active="juego" />

        <div className={styles.topLine}>
          <button type="button" className={styles.backButton} onClick={() => router.back()}>
            ← Volver
          </button>

          {details.data?.genres.length > 0 && (
            <p className={styles.breadcrumb}>
              <Link href="/explorar">Explorar</Link> · {details.data.genres.join(" · ")}
            </p>
          )}
        </div>

        <header className={styles.titleRow}>
          <h1>{name || (details.state === "loading" ? "Cargando juego…" : "Juego")}</h1>

          {storeUrl && (
            <a className={styles.storeLink} href={storeUrl} target="_blank" rel="noopener noreferrer">
              Ver en Steam ↗
            </a>
          )}
        </header>

        {notFound && (
          <p className={styles.notice} role="alert">
            No encontramos este juego. Búscalo de nuevo desde el <Link href="/">inicio</Link>.
          </p>
        )}

        {!notFound && (
          <section
            className={styles.hero}
            style={heroBackground ? { "--hero-bg": `url("${heroBackground}")` } : undefined}
            aria-label="Tráilers e información del juego"
          >
            {details.state === "loading" ? (
              <div className={`${styles.stage} ${styles.skeleton}`} aria-hidden="true" />
            ) : (
              <MediaGallery
                media={media}
                gameName={name}
                fallbackImage={details.data?.headerImage || game?.image}
                storeUrl={storeUrl}
              />
            )}

            <aside className={styles.infoCard}>
              {(details.data?.headerImage || game?.image) && (
                <img className={styles.capsule} src={details.data?.headerImage || game?.image} alt="" />
              )}

              {details.state === "error" && (
                <p className={styles.muted}>No pudimos cargar la ficha de Steam. Los precios siguen abajo.</p>
              )}

              {details.data?.description && <p className={styles.description}>{details.data.description}</p>}

              {!steamId && (
                <p className={styles.muted}>
                  Este juego no tiene ficha de Steam, así que no hay tráiler ni sinopsis. Abajo están sus precios.
                </p>
              )}

              {details.data && <Facts details={details.data} />}

              {details.data?.genres.length > 0 && (
                <ul className={styles.genres} aria-label="Géneros">
                  {details.data.genres.map((genre) => (
                    <li key={genre}>{genre}</li>
                  ))}
                </ul>
              )}

              <BestPrice game={visibleGame} />

              {account.authenticated && game && (
                <div className={driftStyles.favoriteLine}>
                  <button
                    type="button"
                    className={`${driftStyles.favoriteButton} ${favorite ? driftStyles.favoriteOn : ""}`}
                    aria-pressed={Boolean(favorite)}
                    disabled={favoriteBusy}
                    onClick={toggleFavorite}
                  >
                    {favorite ? "★ En favoritos" : "☆ Guardar en favoritos"}
                  </button>

                  {priceChange && (
                    <span className={priceChange.direction === "down" ? driftStyles.favoriteDown : driftStyles.favoriteUp}>
                      {priceChange.direction === "down" ? "Bajó" : "Subió"} {formatPrice(priceChange.amount)} desde que
                      lo guardaste.
                    </span>
                  )}

                  {favoriteError && (
                    <span className={driftStyles.favoriteUp} role="alert">
                      {favoriteError}
                    </span>
                  )}
                </div>
              )}
            </aside>
          </section>
        )}

        {!notFound && (
          <>
            <section id="tiendas" className={styles.section} aria-labelledby="titulo-tiendas">
              <p className={driftStyles.purchaseEyebrow}>OPCIONES DE COMPRA</p>
              <h2 id="titulo-tiendas">Dónde comprarlo</h2>
              <p className={styles.sectionCopy}>
                Primero los precios de Colombia y después los de EE. UU., cada grupo de menor a mayor. Elige una tienda para
                abrir su página de compra en otra pestaña.
              </p>

              {prices.state === "loading" && <div className={`${styles.pricesSkeleton} ${styles.skeleton}`} aria-hidden="true" />}

              {prices.state === "error" && (
                <p className={styles.notice} role="alert">
                  No pudimos consultar las tiendas. Recarga la página para intentarlo de nuevo.
                </p>
              )}

              {prices.state === "done" && !game && !notFound && (
                <p className={styles.notice}>Ninguna tienda tiene este juego a la venta en este momento.</p>
              )}

              {visibleGame && (
                <>
                  <RecommendationPanel
                    entry={recommendation}
                    links={visibleGame.links}
                    canSignIn={account.loginAvailable && !account.authenticated}
                  />

                  <PurchaseOptions game={visibleGame} />

                  {hiddenStores > 0 && (
                    <button type="button" className={styles.linkButton} onClick={() => setShowAllStores(true)}>
                      Ver {hiddenStores === 1 ? "1 tienda más" : `${hiddenStores} tiendas más`} de otras plataformas
                    </button>
                  )}
                </>
              )}
            </section>

            {showHistory && (
              <div className={styles.section}>
                <PriceHistoryPanel entry={history} />
              </div>
            )}

            <div className={styles.section}>
              {canEstimatePcCompatibility(compatibilityGame) ? (
                <CompatibilityPanel
                  profile={pcProfile}
                  compatibility={compatibility}
                  gpuOptions={gpuOptions}
                  cpuOptions={cpuOptions}
                  onSaveProfile={savePcProfile}
                />
              ) : (
                <p className={driftStyles.consoleNotice}>
                  {game?.platforms?.length && !game.platforms.includes("PC")
                    ? `Esta edición se vende para ${game.platforms.join(" y ")}: funciona en la consola, sin requisitos de PC que revisar.`
                    : "No tenemos los requisitos de PC de este juego, así que no podemos estimar si corre en tu equipo."}
                </p>
              )}
            </div>
          </>
        )}
      </div>
    </main>
  );
}
