import { useEffect, useState, type FormEvent } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { API_BASE, apiDisplayLabel, isApiConfigured } from "../api/config";
import { fetchHealth } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import "./Login.css";

export function Login() {
  const { user, loading, login } = useAuth();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [apiReachable, setApiReachable] = useState<boolean | null>(null);

  useEffect(() => {
    if (import.meta.env.DEV || !API_BASE) return;
    let cancelled = false;
    fetchHealth()
      .then(() => {
        if (!cancelled) setApiReachable(true);
      })
      .catch(() => {
        if (!cancelled) setApiReachable(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

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
        {!isApiConfigured && (
          <p className="config-warn">
            Backend não configurado neste build. Na Vercel, defina{" "}
            <code>VITE_API_URL</code> (URL do FastAPI) e redeploy. Localmente, suba o
            backend na porta 8000.
          </p>
        )}
        <p className="api-hint">
          API: <code>{apiDisplayLabel()}</code>
        </p>
        {apiReachable === false && (
          <p className="config-warn">
            A API ainda não está no ar. Crie o serviço no{" "}
            <a href="https://dashboard.render.com" target="_blank" rel="noreferrer">
              Render
            </a>{" "}
            (Blueprint do repo) e confira{" "}
            <a href={`${API_BASE}/api/health`} target="_blank" rel="noreferrer">
              /api/health
            </a>
            .
          </p>
        )}
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
