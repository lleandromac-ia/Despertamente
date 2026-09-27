import { useEffect, useState, type FormEvent } from "react";
import { createUserAdmin, listUsers } from "../api/auth";
import { useAuth } from "../auth/AuthContext";
import type { User } from "../auth/types";
import "./AdminUsers.css";

export function AdminUsers() {
  const { token, user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    if (!token) return;
    const res = await listUsers(token);
    setUsers(res.users);
  };

  useEffect(() => {
    load().catch((e) => setError(e instanceof Error ? e.message : "Erro ao carregar"));
  }, [token]);

  if (!user || user.role !== "admin") {
    return <p className="error">Acesso restrito a administradores.</p>;
  }

  const onCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await createUserAdmin(token, {
        username,
        password,
        fullName,
        email,
        role: "user",
      });
      setMessage(`Usuário "${username}" criado. Ele deve alterar a senha no primeiro acesso.`);
      setUsername("");
      setPassword("");
      setFullName("");
      setEmail("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar usuário");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="admin-users">
      <h1>Usuários</h1>
      <p className="hint">Somente administradores podem cadastrar novos usuários.</p>

      <section className="panel">
        <h2>Novo usuário</h2>
        <form onSubmit={onCreate} className="admin-form">
          <label>
            Usuário (login)
            <input value={username} onChange={(e) => setUsername(e.target.value)} required minLength={3} />
          </label>
          <label>
            Senha inicial
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
          </label>
          <label>
            Nome
            <input value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </label>
          <label>
            E-mail
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <button type="submit" className="primary" disabled={busy}>
            Cadastrar usuário
          </button>
        </form>
      </section>

      <section className="panel">
        <h2>Usuários cadastrados</h2>
        <ul className="user-list">
          {users.map((u) => (
            <li key={u.id}>
              <strong>{u.username}</strong> — {u.fullName || "Sem nome"} ({u.role})
              {u.mustChangePassword && <span className="tag">Senha provisória</span>}
            </li>
          ))}
        </ul>
      </section>

      {message && <p className="success">{message}</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
