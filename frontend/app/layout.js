import "../ui/components/DriftHome.module.css";

export const metadata = {
  title: "DRIFT | Encuentra tu próxima partida",
  description: "Compara precios y descubre videojuegos."
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
