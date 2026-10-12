/**
 * Procesadores que el usuario puede elegir aunque el catálogo de benchmarks
 * no los tenga, con su nivel aproximado (1 = muy básico … 5 = muy alto).
 * El backend vuelve a clasificar el nombre con sus propias reglas; este
 * nivel solo se usa si no lo reconoce.
 */
export const cpuGroups = [
  {
    label: "No sé cuál tengo",
    options: [
      { name: "Procesador básico o antiguo (2 núcleos)", score: 1 },
      { name: "Procesador de gama media (4 a 6 núcleos)", score: 3 },
      { name: "Procesador de gama alta (8 núcleos o más)", score: 4 },
    ],
  },
  {
    label: "Intel",
    options: [
      { name: "Intel Core i3-6100", score: 1 },
      { name: "Intel Core i5-4460", score: 2 },
      { name: "Intel Core i5-6500", score: 2 },
      { name: "Intel Core i7-4770", score: 3 },
      { name: "Intel Core i7-6700", score: 3 },
      { name: "Intel Core i3-8100", score: 2 },
      { name: "Intel Core i5-8400", score: 3 },
      { name: "Intel Core i5-9400F", score: 3 },
      { name: "Intel Core i7-8700", score: 4 },
      { name: "Intel Core i7-9700K", score: 4 },
      { name: "Intel Core i3-10100", score: 3 },
      { name: "Intel Core i5-10400F", score: 4 },
      { name: "Intel Core i7-10700", score: 4 },
      { name: "Intel Core i5-11400F", score: 4 },
    ],
  },
  {
    label: "AMD",
    options: [
      { name: "AMD FX-6300", score: 2 },
      { name: "AMD FX-8350", score: 2 },
      { name: "AMD Ryzen 3 1200", score: 2 },
      { name: "AMD Ryzen 5 1600", score: 3 },
      { name: "AMD Ryzen 5 2600", score: 3 },
      { name: "AMD Ryzen 7 2700X", score: 3 },
      { name: "AMD Ryzen 3 3100", score: 3 },
      { name: "AMD Ryzen 5 3600", score: 4 },
      { name: "AMD Ryzen 7 3700X", score: 4 },
    ],
  },
];
