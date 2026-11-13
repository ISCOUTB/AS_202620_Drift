import { createPriceHistory } from "../../domain/model/PriceHistory";

export async function getPriceHistory(gameId, priceHistoryRepository) {
  return createPriceHistory(await priceHistoryRepository.find(gameId));
}
