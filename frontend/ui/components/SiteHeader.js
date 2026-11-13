"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { listFavorites, loadAccount } from "../../application/usecases/account";
import { ANONYMOUS_ACCOUNT } from "../../domain/model/Account";
import { fastApiAccountRepository } from "../../infrastructure/http/FastApiAccountRepository";

import { AccountButton } from "./AccountPanel";
import styles from "./DriftHome.module.css";

/** Sesión y favoritos de quien navega, para las páginas fuera del inicio. */
export function useAccountSummary() {
  const [account, setAccount] = useState(ANONYMOUS_ACCOUNT);
  const [favorites, setFavorites] = useState([]);

  useEffect(() => {
    let cancelled = false;

    void loadAccount(fastApiAccountRepository).then(async (loaded) => {
      if (cancelled) {
        return;
      }

      setAccount(loaded);

      if (loaded.authenticated) {
        try {
          const saved = await listFavorites(fastApiAccountRepository);

          if (!cancelled) {
            setFavorites(saved);
          }
        } catch {
          // Sin favoritos la página sigue igual.
        }
      }
    });

    return () => {
      cancelled = true;
    };
  }, []);

  return { account, favorites };
}

/** Dirección del inicio que compara los precios de un juego. */
export function compareUrl(name) {
  return `/?q=${encodeURIComponent(name)}`;
}

/**
 * Cabecera de las páginas fuera del inicio: el buscador y la cuenta llevan
 * al inicio, donde viven la comparación de precios y el panel de la cuenta.
 */
export default function SiteHeader({ account, active }) {
  const router = useRouter();
  const [query, setQuery] = useState("");

  const submit = (event) => {
    event.preventDefault();

    if (query.trim()) {
      router.push(compareUrl(query.trim()));
    }
  };

  return (
    <>
      <header className={styles.topBar}>
        <div className={styles.brand}>
          <Link className={styles.logo} href="/" aria-label="DRIFT, ir al inicio">
            <span>DR</span>
            <span>IFT</span>
          </Link>
        </div>

        <form className={styles.searchForm} onSubmit={submit} role="search">
          <span className={styles.searchIcon} aria-hidden="true" />

          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Busca un videojuego"
            aria-label="Buscar videojuego"
          />

          <button type="submit">Buscar</button>
        </form>

        {account.loginAvailable ? (
          <AccountButton
            account={account}
            loginUrl={fastApiAccountRepository.loginUrl()}
            isOpen={false}
            onToggle={() => router.push("/?cuenta=1")}
          />
        ) : (
          <span />
        )}
      </header>

      <nav className={styles.nav} aria-label="Navegación principal">
        <Link href="/" className={active === "inicio" ? styles.navActive : ""}>
          Inicio
        </Link>

        <Link
          href="/explorar"
          className={active === "explorar" ? styles.navActive : ""}
          aria-current={active === "explorar" ? "page" : undefined}
        >
          Explorar
        </Link>

        <Link href="/?vista=tiendas">Tiendas</Link>

        {account.authenticated && <Link href="/?vista=favoritos">Favoritos</Link>}
      </nav>
    </>
  );
}
