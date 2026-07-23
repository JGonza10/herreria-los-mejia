import { useState } from "react";
import Hero from "../components/Hero.jsx";
import CordonSoldadura from "../components/CordonSoldadura.jsx";
import Catalogo from "../components/Catalogo.jsx";
import Cotizador from "../components/Cotizador.jsx";
import Footer from "../components/Footer.jsx";
import Chatbot from "../components/Chatbot.jsx";

export default function SitioPublico() {
  const [productoParaCotizar, setProductoParaCotizar] = useState(null);

  const irACotizar = (producto) => {
    setProductoParaCotizar(producto);
    document.getElementById("cotizador")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <>
      <Hero />
      <CordonSoldadura />
      <Catalogo onCotizarProducto={irACotizar} />
      <CordonSoldadura />
      <Cotizador productoPreseleccionado={productoParaCotizar} />
      <Footer />
      <Chatbot />
    </>
  );
}
