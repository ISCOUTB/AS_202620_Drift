import { notFound } from "next/navigation";

import { EXPLORE_GENRES, filtersFromParams, findGenre } from "../../../domain/model/Explore";
import ExploreGenre from "../../../ui/components/ExploreGenre";

export function generateStaticParams() {
  return EXPLORE_GENRES.map((genre) => ({ genero: genre.slug }));
}

export async function generateMetadata({ params }) {
  const { genero } = await params;
  const genre = findGenre(genero);

  return { title: genre ? `${genre.name} | Explorar | DRIFT` : "Explorar | DRIFT" };
}

export default async function GenrePage({ params, searchParams }) {
  const { genero } = await params;

  if (!findGenre(genero)) {
    notFound();
  }

  const filters = filtersFromParams(await searchParams);

  // `key`: al cambiar de género la página empieza de cero.
  return <ExploreGenre key={genero} genre={genero} initialFilters={filters} />;
}
