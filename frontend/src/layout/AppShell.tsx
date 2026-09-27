import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import "./AppShell.css";

export function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const onLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="app-shell">
      <header className="top-nav">
        <Link to="/" className="brand">
          GeraVideos
        </Link>
        <nav>
          <NavLink to="/" end>
            Criar vídeo
          </NavLink>
          <NavLink to="/perfil">Perfil</NavLink>
          {user?.role === "admin" && <NavLink to="/admin/usuarios">Usuários</NavLink>}
        </nav>
        <div className="nav-user">
          <span>{user?.fullName || user?.username}</span>
          <button type="button" onClick={onLogout}>
            Sair
          </button>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
