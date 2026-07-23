import { Routes, Route } from "react-router-dom";
import { ThemeProvider } from "./context/ThemeContext.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";
import RutaProtegida from "./components/RutaProtegida.jsx";
import Header from "./components/Header.jsx";

import SitioPublico from "./pages/SitioPublico.jsx";
import Login from "./pages/Login.jsx";
import Registro from "./pages/Registro.jsx";
import AdminPanel from "./pages/admin/AdminPanel.jsx";
import TrabajadorPanel from "./pages/TrabajadorPanel.jsx";
import ClientePanel from "./pages/ClientePanel.jsx";

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Rutas />
      </AuthProvider>
    </ThemeProvider>
  );
}

function Rutas() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <>
            <Header />
            <SitioPublico />
          </>
        }
      />
      <Route
        path="/login"
        element={
          <>
            <Header />
            <Login />
          </>
        }
      />
      <Route
        path="/registro"
        element={
          <>
            <Header />
            <Registro />
          </>
        }
      />
      <Route
        path="/admin/*"
        element={
          <RutaProtegida rolesPermitidos={["administrador"]}>
            <AdminPanel />
          </RutaProtegida>
        }
      />
      <Route
        path="/trabajador"
        element={
          <RutaProtegida rolesPermitidos={["trabajador"]}>
            <TrabajadorPanel />
          </RutaProtegida>
        }
      />
      <Route
        path="/cliente"
        element={
          <RutaProtegida rolesPermitidos={["cliente"]}>
            <ClientePanel />
          </RutaProtegida>
        }
      />
    </Routes>
  );
}
