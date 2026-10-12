/** @type {import('next').NextConfig} */
const nextConfig = {
  // El servidor autocontenido solo se genera para la imagen Docker, que lo
  // pide con NEXT_OUTPUT=standalone. En Vercel rompe su paso final de build.
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : undefined,
};

module.exports = nextConfig;
