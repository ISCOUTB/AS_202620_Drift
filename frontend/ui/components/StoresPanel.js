"use client";

import { useState } from "react";

import { groupStoresByPlatform, storeInitials } from "../../domain/model/Store";

import styles from "./StoresPanel.module.css";

function StoreLogo({ store }) {
  const [failed, setFailed] = useState(false);

  if (!store.logo || failed) {
    return (
      <span className={styles.initials} aria-hidden="true">
        {storeInitials(store.name)}
      </span>
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      className={styles.logo}
      src={store.logo}
      alt=""
      width="32"
      height="32"
      loading="lazy"
      referrerPolicy="no-referrer"
      onError={() => setFailed(true)}
    />
  );
}

function StoreCard({ store }) {
  const content = (
    <>
      <StoreLogo store={store} />

      <span className={styles.text}>
        <strong>{store.name}</strong>

        <small>{store.note}</small>
      </span>

      {store.url && (
        <span className={styles.go} aria-hidden="true">
          ↗
        </span>
      )}
    </>
  );

  if (!store.url) {
    return <div className={styles.card}>{content}</div>;
  }

  return (
    <a
      className={`${styles.card} ${styles.cardLink}`}
      href={store.url}
      target="_blank"
      rel="noopener noreferrer"
      title={`Abrir ${store.name} en una pestaña nueva`}
    >
      {content}
    </a>
  );
}

/** Todas las tiendas cuyos precios compara DRIFT, por plataforma. */
export default function StoresPanel({ directory }) {
  if (!directory) {
    return (
      <section className={styles.panel} aria-label="Tiendas">
        <h2>Tiendas</h2>

        <p className={styles.description}>Cargando las tiendas…</p>
      </section>
    );
  }

  const groups = groupStoresByPlatform(directory.stores);

  return (
    <section className={styles.panel} aria-label="Tiendas">
      <h2>Tiendas ({directory.stores.length})</h2>

      <p className={styles.description}>
        DRIFT compara los precios de estas tiendas. Cada una abre su página
        en una pestaña nueva.
      </p>

      {!directory.complete && (
        <p className={styles.warning}>
          No pudimos consultar la lista completa de tiendas de PC. Estas son
          las principales.
        </p>
      )}

      {groups.map((group) => (
        <div key={group.platform} className={styles.group}>
          <h3>
            {group.platform} ({group.stores.length})
          </h3>

          <div className={styles.grid}>
            {group.stores.map((store) => (
              <StoreCard key={store.name} store={store} />
            ))}
          </div>
        </div>
      ))}
    </section>
  );
}
