import { useTema } from "../context/ThemeContext.jsx";

export default function ThemeToggle() {
  const { tema, alternarTema } = useTema();
  return (
    <button
      onClick={alternarTema}
      aria-label={tema === "dark" ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}
      title={tema === "dark" ? "Tema claro" : "Tema oscuro"}
      style={{
        width: 38,
        height: 38,
        borderRadius: "50%",
        border: "1px solid var(--borde)",
        background: "transparent",
        color: "var(--texto)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: "1.05rem",
      }}
    >
      {tema === "dark" ? "☀" : "🌙"}
    </button>
  );
}
