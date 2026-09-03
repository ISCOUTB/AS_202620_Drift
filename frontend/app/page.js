"use client";

import { useState } from "react";

export default function Home() {
  const [query, setQuery] = useState("");
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const searchGames = async () => {
    if (!query.trim()) {
      setError("Escribe el nombre de un videojuego.");
      setGames([]);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `http://localhost:8000/games/search?q=${encodeURIComponent(query)}`
      );

      if (!response.ok) {
        throw new Error("No se pudo realizar la búsqueda");
      }

      const data = await response.json();
      setGames(data);

      if (data.length === 0) {
        setError("No se encontraron videojuegos.");
      }
    } catch (err) {
      setError("No se pudo conectar con el backend.");
      setGames([]);
    } finally {
      setLoading(false);
    }
  };

  const getBestPrice = (prices) => {
  const entries = Object.entries(prices);

  if (entries.length === 0) {
    return null;
  }

  return entries.reduce((best, current) => {
    return current[1] < best[1] ? current : best;
  });
};

  return (
    <main
      style={{
        maxWidth: "900px",
        margin: "0 auto",
        padding: "40px 20px",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <header style={{ marginBottom: "30px" }}>
        <h1 style={{ fontSize: "42px", marginBottom: "8px" }}>
          DRIFT
        </h1>

        <p style={{ fontSize: "18px", color: "#555" }}>
          Compara precios de videojuegos entre diferentes plataformas.
        </p>
      </header>

      <section
        style={{
          display: "flex",
          gap: "10px",
          marginBottom: "30px",
        }}
      >
        <input
          type="text"
          placeholder="Buscar videojuego..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              searchGames();
            }
          }}
          style={{
            flex: 1,
            padding: "12px",
            fontSize: "16px",
            border: "1px solid #ccc",
            borderRadius: "6px",
          }}
        />

        <button
          onClick={searchGames}
          disabled={loading}
          style={{
            padding: "12px 20px",
            fontSize: "16px",
            border: "none",
            borderRadius: "6px",
            cursor: loading ? "default" : "pointer",
          }}
        >
          {loading ? "Buscando..." : "Buscar"}
        </button>
      </section>

      {error && (
        <p
          style={{
            padding: "12px",
            borderRadius: "6px",
            marginBottom: "20px",
          }}
        >
          {error}
        </p>
      )}

      <section>
        {games.map((game) => {
  const bestPrice = getBestPrice(game.prices);

  return (
            <article
              key={game.id}
              style={{
                border: "1px solid #ddd",
                borderRadius: "10px",
                padding: "24px",
                marginBottom: "20px",
              }}
            >
              <h2 style={{ marginTop: 0 }}>{game.name}</h2>

              <p>
  <strong>Mejor precio:</strong>{" "}
  {bestPrice
    ? `${bestPrice[0]} — $${bestPrice[1].toFixed(2)}`
    : "Precio no disponible"}
</p>

              <hr />

              <h3>Precios disponibles</h3>

              {Object.entries(game.prices).map(
                ([platform, price]) => (
                  <p key={platform}>
                    <strong>{platform}:</strong> $
                    {price.toFixed(2)}
                  </p>
                )
              )}
            </article>
          );
        })}
      </section>
    </main>
  );
}