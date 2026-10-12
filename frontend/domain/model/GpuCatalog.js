/**
 * Tarjetas gráficas que el usuario puede elegir, con su nivel aproximado
 * (1 = integrada … 5 = muy alta). El backend vuelve a clasificar el nombre
 * con sus propias reglas; este nivel solo se usa si no lo reconoce.
 */
export const gpuLevelNames = {
  1: "integrada o muy básica",
  2: "básica",
  3: "media",
  4: "alta",
  5: "muy alta",
};

export const gpuGroups = [
  {
    label: "No sé cuál tengo",
    options: [
      { name: "Gráficos integrados (sin tarjeta dedicada)", score: 1 },
      { name: "Tarjeta dedicada básica", score: 2 },
      { name: "Tarjeta dedicada media", score: 3 },
      { name: "Tarjeta dedicada alta", score: 4 },
    ],
  },
  {
    label: "NVIDIA GeForce",
    options: [
      { name: "NVIDIA GeForce GT 710 / GT 730", score: 1 },
      { name: "NVIDIA GeForce GT 1030", score: 2 },
      { name: "NVIDIA GeForce GTX 750 Ti", score: 2 },
      { name: "NVIDIA GeForce GTX 950 / GTX 960", score: 2 },
      { name: "NVIDIA GeForce GTX 1050", score: 2 },
      { name: "NVIDIA GeForce GTX 1050 Ti", score: 3 },
      { name: "NVIDIA GeForce GTX 970", score: 3 },
      { name: "NVIDIA GeForce GTX 1060", score: 3 },
      { name: "NVIDIA GeForce GTX 1650", score: 3 },
      { name: "NVIDIA GeForce GTX 1660", score: 4 },
      { name: "NVIDIA GeForce GTX 1070", score: 4 },
      { name: "NVIDIA GeForce GTX 1080", score: 4 },
      { name: "NVIDIA GeForce RTX 2060", score: 4 },
      { name: "NVIDIA GeForce RTX 3050", score: 4 },
      { name: "NVIDIA GeForce RTX 3060", score: 4 },
      { name: "NVIDIA GeForce RTX 4060", score: 4 },
      { name: "NVIDIA GeForce RTX 2070 / RTX 2080", score: 5 },
      { name: "NVIDIA GeForce RTX 3070 / RTX 3080", score: 5 },
      { name: "NVIDIA GeForce RTX 4070 / RTX 4080 / RTX 4090", score: 5 },
    ],
  },
  {
    label: "AMD Radeon",
    options: [
      { name: "AMD Radeon RX 550 / RX 560", score: 2 },
      { name: "AMD Radeon RX 570 / RX 580", score: 3 },
      { name: "AMD Radeon RX 6400 / RX 6500", score: 3 },
      { name: "AMD Radeon RX 5600 / RX 5700", score: 4 },
      { name: "AMD Radeon RX 6600", score: 4 },
      { name: "AMD Radeon RX 7600", score: 4 },
      { name: "AMD Radeon RX 6700 / RX 6800", score: 5 },
      { name: "AMD Radeon RX 7700 / RX 7800", score: 5 },
    ],
  },
  {
    label: "Intel",
    options: [
      { name: "Intel HD / UHD Graphics", score: 1 },
      { name: "Intel Iris Xe", score: 1 },
      { name: "Intel Arc A380", score: 3 },
      { name: "Intel Arc A580 / A750 / A770", score: 4 },
    ],
  },
];

export function findGpuScore(name) {
  for (const group of gpuGroups) {
    const option = group.options.find((item) => item.name === name);

    if (option) {
      return option.score;
    }
  }

  return null;
}
