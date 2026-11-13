"use client";

import { useMemo, useState } from "react";

import styles from "./PriceHistoryPanel.module.css";

const WIDTH = 640;
const HEIGHT = 210;
const MARGIN = { top: 14, right: 14, bottom: 26, left: 62 };
const PLOT_WIDTH = WIDTH - MARGIN.left - MARGIN.right;
const PLOT_HEIGHT = HEIGHT - MARGIN.top - MARGIN.bottom;

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

const monthLabel = new Intl.DateTimeFormat("es-CO", { month: "short" });

function formatAxisPrice(price) {
  return price >= 1000 ? `$${Math.round(price / 1000)} mil` : money.format(price);
}

/** Primer día de cada mes dentro del periodo, sin amontonar etiquetas. */
function monthTicks(start, end) {
  const ticks = [];
  const cursor = new Date(start.getFullYear(), start.getMonth() + 1, 1);

  while (cursor <= end) {
    ticks.push(new Date(cursor));
    cursor.setMonth(cursor.getMonth() + 1);
  }

  const step = Math.ceil(ticks.length / 6);

  return ticks.filter((_, index) => index % step === 0);
}

function buildChart(history, now) {
  const points = history.points;
  const start = history.since ?? points[0].date;
  const end = now;
  const span = Math.max(1, end - start);

  const prices = points.map((point) => point.price);
  const lowest = Math.min(...prices);
  const highest = Math.max(...prices);
  const padding = Math.max((highest - lowest) * 0.18, highest * 0.04);
  const minPrice = Math.max(0, lowest - padding);
  const maxPrice = highest + padding;

  const x = (date) =>
    MARGIN.left +
    (Math.min(Math.max(date - start, 0), span) / span) * PLOT_WIDTH;

  const y = (price) =>
    MARGIN.top +
    (1 - (price - minPrice) / (maxPrice - minPrice || 1)) * PLOT_HEIGHT;

  // Un precio se mantiene hasta el siguiente cambio: línea en escalones.
  let path = `M ${x(points[0].date)} ${y(points[0].price)}`;

  for (let index = 1; index < points.length; index += 1) {
    path += ` H ${x(points[index].date)} V ${y(points[index].price)}`;
  }

  path += ` H ${x(end)}`;

  const lowestIndex = prices.lastIndexOf(lowest);

  return {
    x,
    y,
    path,
    start,
    end,
    lowestIndex,
    gridPrices: [highest, (highest + lowest) / 2, lowest].filter(
      (price, index, all) => all.indexOf(price) === index,
    ),
    months: monthTicks(start, end),
  };
}

function Summary({ history }) {
  return (
    <dl className={styles.summary}>
      {history.current && (
        <div>
          <dt>Mejor precio hoy</dt>
          <dd>{money.format(history.current.price)}</dd>
          <small>{history.current.store}</small>
        </div>
      )}

      {history.lowest && (
        <div>
          <dt>Más bajo en 12 meses</dt>
          <dd>{money.format(history.lowest.price)}</dd>
          <small>
            {history.lowest.store} · {shortDate.format(history.lowest.date)}
          </small>
        </div>
      )}

      {history.steamBestDiscount && (
        <div>
          <dt>Mayor descuento en Steam</dt>
          <dd>-{history.steamBestDiscount.discount}%</dd>
          <small>{shortDate.format(history.steamBestDiscount.date)}</small>
        </div>
      )}
    </dl>
  );
}

function Chart({ history }) {
  const [now] = useState(() => new Date());
  const [hoverIndex, setHoverIndex] = useState(null);

  const chart = useMemo(() => buildChart(history, now), [history, now]);
  const points = history.points;

  const onMove = (event) => {
    const box = event.currentTarget.getBoundingClientRect();
    const svgX = ((event.clientX - box.left) / box.width) * WIDTH;

    // El punto vigente en esa fecha: el último que empieza antes del cursor.
    let index = 0;

    for (let current = 0; current < points.length; current += 1) {
      if (chart.x(points[current].date) <= svgX) {
        index = current;
      }
    }

    setHoverIndex(index);
  };

  const hovered = hoverIndex === null ? null : points[hoverIndex];
  const lowest = points[chart.lowestIndex];
  const lowestX = chart.x(lowest.date);

  return (
    <div className={styles.chartWrap}>
      <svg
        className={styles.chart}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label={`Mejor precio entre tiendas de PC en los últimos 12 meses. Hoy ${money.format(
          points[points.length - 1].price,
        )}; el más bajo fue ${money.format(lowest.price)}.`}
        onPointerMove={onMove}
        onPointerLeave={() => setHoverIndex(null)}
      >
        {chart.gridPrices.map((price) => (
          <g key={price}>
            <line
              className={styles.grid}
              x1={MARGIN.left}
              x2={WIDTH - MARGIN.right}
              y1={chart.y(price)}
              y2={chart.y(price)}
            />

            <text
              className={styles.axisLabel}
              x={MARGIN.left - 8}
              y={chart.y(price) + 4}
              textAnchor="end"
            >
              {formatAxisPrice(price)}
            </text>
          </g>
        ))}

        {chart.months.map((month) => (
          <text
            key={month.toISOString()}
            className={styles.axisLabel}
            x={chart.x(month)}
            y={HEIGHT - 8}
            textAnchor="middle"
          >
            {monthLabel.format(month).replace(".", "")}
          </text>
        ))}

        <path className={styles.line} d={chart.path} />

        {/* El más bajo del periodo: marcador con anillo del color del fondo. */}
        <circle
          className={styles.lowestDot}
          cx={lowestX}
          cy={chart.y(lowest.price)}
          r="5"
        />

        <text
          className={styles.pointLabel}
          x={Math.min(Math.max(lowestX, MARGIN.left + 28), WIDTH - 40)}
          y={chart.y(lowest.price) + 18}
          textAnchor="middle"
        >
          Más bajo
        </text>

        {hovered && (
          <g>
            <line
              className={styles.crosshair}
              x1={chart.x(hovered.date)}
              x2={chart.x(hovered.date)}
              y1={MARGIN.top}
              y2={HEIGHT - MARGIN.bottom}
            />

            <circle
              className={styles.hoverDot}
              cx={chart.x(hovered.date)}
              cy={chart.y(hovered.price)}
              r="5"
            />
          </g>
        )}
      </svg>

      {hovered && (
        <div
          className={styles.tooltip}
          style={{
            left: `${Math.min(
              Math.max((chart.x(hovered.date) / WIDTH) * 100, 18),
              82,
            )}%`,
          }}
        >
          <strong>{money.format(hovered.price)}</strong>

          <span>
            {hovered.store}
            {hovered.discount > 0 ? ` · -${hovered.discount}%` : ""}
          </span>

          <small>desde el {shortDate.format(hovered.date)}</small>
        </div>
      )}
    </div>
  );
}

function ChangesTable({ points }) {
  return (
    <details className={styles.tableToggle}>
      <summary>Ver los cambios en una tabla</summary>

      <div className={styles.tableScroll}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th scope="col">Desde</th>
              <th scope="col">Tienda</th>
              <th scope="col">Mejor precio</th>
              <th scope="col">Descuento</th>
            </tr>
          </thead>

          <tbody>
            {[...points].reverse().map((point) => (
              <tr key={`${point.date.toISOString()}-${point.store}`}>
                <td>{shortDate.format(point.date)}</td>
                <td>{point.store}</td>
                <td>{money.format(point.price)}</td>
                <td>{point.discount > 0 ? `-${point.discount}%` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}

/** Historial del mejor precio de un juego entre las tiendas de PC. */
export default function PriceHistoryPanel({ entry }) {
  // Sin llave de la fuente no hay historial que ofrecer: no se muestra nada.
  if (entry?.state === "done" && entry.data.reason === "not_configured") {
    return null;
  }

  return (
    <section className={styles.panel} aria-label="Historial de precios">
      <h3>Historial de precios</h3>

      {(!entry || entry.state === "loading") && (
        <p className={styles.note}>Consultando el historial…</p>
      )}

      {entry?.state === "error" && (
        <p className={styles.note}>
          No pudimos consultar el historial en este momento. Los precios de
          arriba siguen siendo los actuales.
        </p>
      )}

      {entry?.state === "done" && !entry.data.available && (
        <p className={styles.note}>
          No hay historial de precios registrado para este juego.
        </p>
      )}

      {entry?.state === "done" && entry.data.available && (
        <>
          <p className={styles.description}>
            Mejor precio entre las tiendas de PC que hoy venden el juego,
            incluida Steam, en los últimos 12 meses.
          </p>

          <Summary history={entry.data} />

          {entry.data.points.length > 0 ? (
            <>
              <Chart history={entry.data} />
              <ChangesTable points={entry.data.points} />
            </>
          ) : (
            <p className={styles.note}>
              Ninguna tienda de PC registró cambios de precio en los últimos
              12 meses.
            </p>
          )}

          {entry.data.cachedAt && (
            <p className={styles.warning}>
              La fuente no respondió: este historial se consultó el{" "}
              {shortDate.format(entry.data.cachedAt)}.
            </p>
          )}

          <p className={styles.footnote}>
            Fuente: IsThereAnyDeal. Los precios de Steam son los de Colombia:
            se calculan con su precio normal de hoy y el descuento que tuvo en
            cada fecha. Los de las demás tiendas son precios de Estados Unidos
            convertidos a pesos con la tasa de hoy. Los valores antiguos son
            aproximados.
          </p>
        </>
      )}
    </section>
  );
}
