import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";

vi.mock("../application/usecases/searchGames", () => ({
  searchGames: vi.fn(),
}));

vi.mock("../application/usecases/estimateCompatibility", () => ({
  estimateCompatibility: vi.fn(),
}));

import { searchGames } from "../application/usecases/searchGames";
import { estimateCompatibility } from "../application/usecases/estimateCompatibility";
import DriftHome from "../ui/components/DriftHome";

const game = {
  id: "620",
  name: "Portal 2",
  prices: {
    Steam: 2600,
    PlayStation: 2000,
  },
  unavailable_sources: [],
};

beforeEach(() => {
  vi.clearAllMocks();

  searchGames.mockResolvedValue([game]);
  estimateCompatibility.mockResolvedValue({
    status: "Compatible",
    minimum_ram_gb: 4,
    recommended_ram_gb: 8,
    minimum_gpu_score: 1,
    recommended_gpu_score: 2,
  });
});

test("busca un juego, muestra sus precios y calcula compatibilidad", async () => {
  render(<DriftHome />);

  fireEvent.change(
    screen.getByLabelText("Buscar videojuego"),
    { target: { value: "Portal 2" } },
  );

  fireEvent.click(
    screen.getByRole("button", { name: "Buscar" }),
  );

  const gameHeading = await screen.findByRole(
    "heading",
    { name: "Portal 2" },
  );

  fireEvent.click(gameHeading.closest("article"));

  expect(
    await screen.findByText(
      "El precio más bajo está resaltado. Puedes elegir la plataforma que prefieras.",
    ),
  ).toBeInTheDocument();

  expect(
    screen.getAllByText("PlayStation").length,
  ).toBeGreaterThan(0);

  fireEvent.change(
    screen.getByLabelText("RAM disponible (GB)"),
    { target: { value: "8" } },
  );

  fireEvent.change(
    screen.getByLabelText("Nivel de GPU"),
    { target: { value: "2" } },
  );

  fireEvent.click(
    screen.getByRole("button", {
      name: "Comprobar compatibilidad",
    }),
  );

  expect(
    await screen.findByText("Resultado: Compatible"),
  ).toBeInTheDocument();

  expect(searchGames).toHaveBeenCalledWith(
    "Portal 2",
    expect.anything(),
  );

  expect(estimateCompatibility).toHaveBeenCalledWith(
    "620",
    { ramGb: "8", gpuScore: "2" },
    expect.anything(),
  );
});
