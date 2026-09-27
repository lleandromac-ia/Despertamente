import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";

export function ProtectedRoute() {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <p style={{ padding: "2rem", textAlign: "center" }}>Carregando...</p>;
  }

  if (!user) {
    return <Navigate to={`/login?redirect=${encodeURIComponent(location.pathname)}`} replace />;
  }

  if (user.mustChangePassword && !location.pathname.startsWith("/perfil")) {
    return <Navigate to="/perfil?senha=1" replace />;
  }

  return <Outlet />;
}
