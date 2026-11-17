import { createRecommendation } from "../../domain/model/Recommendation";

/** La opción de compra más conveniente de un juego para estos dispositivos. */
export async function getRecommendation(game, devices, recommendationRepository) {
  return createRecommendation(
    await recommendationRepository.recommend(
      game.id,
      game.prices,
      game.discounts,
      devices,
    ),
  );
}
