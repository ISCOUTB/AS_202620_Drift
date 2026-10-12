import { cpuGroups } from "../../domain/model/CpuCatalog";
import { gpuGroups } from "../../domain/model/GpuCatalog";

/**
 * Opciones de un buscador de «Mi PC»: primero las genéricas («no sé cuál
 * tengo») y luego los modelos, uniendo el catálogo con benchmark y la lista
 * incluida en la aplicación (que cubre modelos antiguos). Si el catálogo no
 * responde o está vacío, queda solo la lista incluida.
 */
async function listHardwareOptions(catalogRepository, groups) {
  const [genericGroup, ...modelGroups] = groups;
  const builtIn = modelGroups.flatMap((group) => group.options);

  let fromCatalogue = [];

  try {
    fromCatalogue = await catalogRepository.list();
  } catch {
    // Sin catálogo se sigue con la lista incluida.
  }

  const byName = new Map();

  // El catálogo va después para que prevalezca sobre la lista incluida.
  for (const option of [...builtIn, ...fromCatalogue]) {
    byName.set(option.name.toLocaleLowerCase("es"), option);
  }

  const models = [...byName.values()].sort((first, second) =>
    first.name.localeCompare(second.name, "es", { numeric: true }),
  );

  return [...genericGroup.options, ...models];
}

export function listGraphicsCards(gpuCatalogRepository) {
  return listHardwareOptions(gpuCatalogRepository, gpuGroups);
}

export function listProcessors(cpuCatalogRepository) {
  return listHardwareOptions(cpuCatalogRepository, cpuGroups);
}
