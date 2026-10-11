/** @type {import('next').NextConfig} */
const nextConfig = {
  // Genera un servidor autocontenido para la imagen Docker; Vercel lo ignora.
  output: "standalone",
};

module.exports = nextConfig;
