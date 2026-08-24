export const metadata = {
  title: "DRIFT",
  description: "Comparador de precios de Videojuegos"
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}