import GamePage from "../../../ui/components/GamePage";

function firstValue(value) {
  return Array.isArray(value) ? value[0] : value;
}

export async function generateMetadata({ searchParams }) {
  const name = firstValue((await searchParams).nombre)?.trim();

  return {
    title: name ? `${name} | DRIFT` : "Juego | DRIFT",
    description: "Tráilers, precios en todas las tiendas, historial y compatibilidad con tu PC.",
  };
}

export default async function GameRoute({ params, searchParams }) {
  const { id } = await params;
  const name = firstValue((await searchParams).nombre)?.trim() ?? "";

  return <GamePage key={id} gameId={id} initialName={name.slice(0, 160)} />;
}
