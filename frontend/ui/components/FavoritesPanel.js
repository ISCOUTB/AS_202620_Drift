"use client";

import { useState } from "react";

import styles from "./FavoritesPanel.module.css";

const money = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});

const shortDate = new Intl.DateTimeFormat("es-CO", {
  day: "numeric",
  month: "short",
  year: "numeric",
});

function formatMoney(price) {
  return price === 0 ? "gratis" : money.format(price);
}

function savedLine(favorite) {
  const when = favorite.savedAt
    ? ` el ${shortDate.format(favorite.savedAt)}`
    : "";

  if (favorite.price === null) {
    return `Guardado${when}, sin precio`;
  }

  return `Guardado${when} a ${formatMoney(favorite.price)} en ${favorite.store}`;
}

function TodayLine({ status, checking }) {
  if (checking) {
    return <small className={styles.today}>Consultando el precio de hoy…</small>;
  }

  if (!status?.current) {
    return (
      <small className={styles.today}>
        Hoy: sin consultar. Las alertas revisan solo tiendas de PC.
      </small>
    );
  }

  return (
    <small className={styles.today}>
      Hoy: <strong>{formatMoney(status.current.price)}</strong> en{" "}
      {status.current.store}
    </small>
  );
}

function AlertBadge({ alert, favorite }) {
  if (!alert) {
    return null;
  }

  const saved =
    alert.savedDifference > 0
      ? ` Cuesta ${money.format(alert.savedDifference)} menos que cuando lo guardaste.`
      : "";

  return (
    <p className={styles.alert}>
      {alert.reason === "target_reached"
        ? `🔔 Llegó a tu precio objetivo de ${money.format(favorite.targetPrice)}.${saved}`
        : `🔔 Bajó ${money.format(alert.savedDifference)} desde que lo guardaste.`}
    </p>
  );
}

function TargetForm({ favorite, onSetTarget }) {
  const [text, setText] = useState(
    favorite.targetPrice ? String(Math.round(favorite.targetPrice)) : "",
  );
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);

  const save = async (value) => {
    setSaving(true);
    setMessage("");

    try {
      await onSetTarget(favorite, value);
      setText(value);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setSaving(false);
    }
  };

  const inputId = `objetivo-${favorite.gameId}`;

  return (
    <form
      className={styles.target}
      onSubmit={(event) => {
        event.preventDefault();
        void save(text);
      }}
    >
      <label htmlFor={inputId}>Avísame si baja de</label>

      <div className={styles.targetRow}>
        <span aria-hidden="true">$</span>

        <input
          id={inputId}
          inputMode="numeric"
          autoComplete="off"
          placeholder="Precio en pesos"
          value={text}
          onChange={(event) => setText(event.target.value)}
        />

        <button type="submit" disabled={saving}>
          Guardar
        </button>

        {favorite.targetPrice !== null && (
          <button
            type="button"
            className={styles.clearTarget}
            disabled={saving}
            onClick={() => save("")}
          >
            Quitar
          </button>
        )}
      </div>

      {message && (
        <small className={styles.targetError} role="alert">
          {message}
        </small>
      )}

      {!message && favorite.targetPrice === null && (
        <small className={styles.targetHint}>
          Sin precio objetivo te avisamos si baja 5 % o más.
        </small>
      )}
    </form>
  );
}

function FavoriteCard({ favorite, status, checking, busy, onSearch, onRemove, onSetTarget }) {
  return (
    <li className={`${styles.card} ${status?.alert ? styles.cardAlert : ""}`}>
      <div
        className={styles.cover}
        style={
          favorite.image
            ? { backgroundImage: `url("${favorite.image}")` }
            : undefined
        }
        aria-hidden="true"
      />

      <div className={styles.text}>
        <strong>{favorite.name}</strong>

        <small>{savedLine(favorite)}</small>

        <TodayLine status={status} checking={checking} />
      </div>

      <AlertBadge alert={status?.alert} favorite={favorite} />

      <TargetForm favorite={favorite} onSetTarget={onSetTarget} />

      <div className={styles.actions}>
        <button
          type="button"
          className={styles.primary}
          onClick={() => onSearch(favorite)}
        >
          Ver todas las tiendas
        </button>

        <button
          type="button"
          className={styles.remove}
          disabled={busy}
          aria-label={`Quitar ${favorite.name} de favoritos`}
          onClick={() => onRemove(favorite)}
        >
          Quitar de favoritos
        </button>
      </div>
    </li>
  );
}

/** Los juegos que el usuario guardó, con su precio de hoy y sus alertas. */
export default function FavoritesPanel({
  favorites,
  alerts,
  error,
  busy,
  onSearch,
  onRemove,
  onSetTarget,
}) {
  return (
    <section className={styles.panel} aria-label="Favoritos">
      <h2>Favoritos ({favorites.length})</h2>

      <p className={styles.description}>
        Al entrar a DRIFT revisamos el precio de hoy de tus favoritos en las
        tiendas de PC y te avisamos aquí si llegaron a tu precio o bajaron. No
        enviamos correos.
      </p>

      {alerts?.checkedAt && (
        <p className={styles.checked}>
          Cada precio se consulta como máximo una vez por hora. Última
          revisión:{" "}
          {alerts.checkedAt.toLocaleTimeString("es-CO", {
            hour: "numeric",
            minute: "2-digit",
          })}
        </p>
      )}

      {error && (
        <p className={styles.warning} role="alert">
          {error}
        </p>
      )}

      {favorites.length === 0 && !error ? (
        <p className={styles.empty}>
          Todavía no tienes favoritos. Busca un juego, ábrelo y usa «Guardar
          en favoritos».
        </p>
      ) : (
        <ul className={styles.list}>
          {favorites.map((favorite) => (
            <FavoriteCard
              key={favorite.gameId}
              favorite={favorite}
              status={alerts?.byGame[favorite.gameId]}
              checking={!alerts}
              busy={busy}
              onSearch={onSearch}
              onRemove={onRemove}
              onSetTarget={onSetTarget}
            />
          ))}
        </ul>
      )}
    </section>
  );
}
