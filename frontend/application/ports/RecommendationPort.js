export function defineRecommendationPort(adapter) {
  if (!adapter || typeof adapter.recommend !== "function") {
    throw new Error(
      "El adaptador debe implementar recommend(gameId, prices, discounts, devices).",
    );
  }

  return adapter;
}
