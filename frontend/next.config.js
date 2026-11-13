/** @type {import('next').NextConfig} */
const nextConfig = {
  // El servidor autocontenido solo se genera para la imagen Docker, que lo
  // pide con NEXT_OUTPUT=standalone. Con `next build` a secas no hace falta.
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : undefined,
};

module.exports = nextConfig;
