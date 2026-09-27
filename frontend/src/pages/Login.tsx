import { useState, type FormEvent } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import "./Login.css";

export function Login() {
  const { user, loading, login } = useAuth();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!loading && user) {
    const dest = user.mustChangePassword ? "/perfil?senha=1" : "/";
    return <Navigate to={dest} replace />;
  }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const logged = await login(username.trim(), password);
      const params = new URLSearchParams(location.search);
      const redirect = params.get("redirect");
      if (logged.mustChangePassword) {
        window.location.href = "/perfil?senha=1";
        return;
      }
      window.location.href = redirect && redirect.startsWith("/") ? redirect : "/";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro no login");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={onSubmit}>
        <h1>GeraVideos</h1>
        <p>Acesse com login e senha</p>
        <label>
          Usuário
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />
        </label>
        <label>
          Senha
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        <button type="submit" className="primary" disabled={busy}>
          {busy ? "Entrando..." : "Entrar"}
        </button>
        {error && <p className="error">{error}</p>}
      </form>
    </div>
  );
}
