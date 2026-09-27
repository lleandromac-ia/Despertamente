import { useEffect, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { changePassword, updateProfile } from "../api/auth";
import { useAuth } from "../auth/AuthContext";
import type { User } from "../auth/types";
import "./Profile.css";

export function Profile() {
  const { user, token, refreshUser, setSession } = useAuth();
  const [params] = useSearchParams();
  const [profile, setProfile] = useState<Partial<User>>({});
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (user) {
      setProfile({
        fullName: user.fullName,
        email: user.email,
        phone: user.phone,
        socialInstagram: user.socialInstagram,
        socialTiktok: user.socialTiktok,
        socialYoutube: user.socialYoutube,
        socialWebsite: user.socialWebsite,
      });
    }
  }, [user]);

  if (!user || !token) return null;

  const mustChange = user.mustChangePassword || params.get("senha") === "1";

  const onSaveProfile = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setBusy(true);
    try {
      const res = await updateProfile(token, profile);
      setSession({ accessToken: token, user: res.user });
      setMessage("Perfil atualizado.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar");
    } finally {
      setBusy(false);
    }
  };

  const onChangePassword = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    if (newPassword !== confirmPassword) {
      setError("A confirmação da senha não confere.");
      return;
    }
    setBusy(true);
    try {
      const res = await changePassword(token, currentPassword, newPassword);
      setSession({ accessToken: token, user: res.user });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setMessage("Senha alterada com sucesso.");
      await refreshUser();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao alterar senha");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="profile-page">
      <h1>Meu perfil</h1>
      <p className="meta">
        Usuário: <strong>{user.username}</strong> · Papel: {user.role === "admin" ? "Administrador" : "Usuário"}
      </p>

      {mustChange && (
        <p className="warn-banner">
          Você precisa alterar a senha provisória definida pelo administrador.
        </p>
      )}

      <section className="panel">
        <h2>Dados pessoais</h2>
        <form onSubmit={onSaveProfile} className="profile-form">
          <label>
            Nome completo
            <input
              value={profile.fullName ?? ""}
              onChange={(e) => setProfile({ ...profile, fullName: e.target.value })}
            />
          </label>
          <label>
            E-mail
            <input
              type="email"
              value={profile.email ?? ""}
              onChange={(e) => setProfile({ ...profile, email: e.target.value })}
            />
          </label>
          <label>
            Celular
            <input
              value={profile.phone ?? ""}
              onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
            />
          </label>
          <label>
            Instagram (URL)
            <input
              value={profile.socialInstagram ?? ""}
              onChange={(e) => setProfile({ ...profile, socialInstagram: e.target.value })}
            />
          </label>
          <label>
            TikTok (URL)
            <input
              value={profile.socialTiktok ?? ""}
              onChange={(e) => setProfile({ ...profile, socialTiktok: e.target.value })}
            />
          </label>
          <label>
            YouTube (URL)
            <input
              value={profile.socialYoutube ?? ""}
              onChange={(e) => setProfile({ ...profile, socialYoutube: e.target.value })}
            />
          </label>
          <label>
            Site / outra rede (URL)
            <input
              value={profile.socialWebsite ?? ""}
              onChange={(e) => setProfile({ ...profile, socialWebsite: e.target.value })}
            />
          </label>
          <button type="submit" disabled={busy}>
            Salvar perfil
          </button>
        </form>
      </section>

      <section className="panel">
        <h2>Alterar senha</h2>
        <form onSubmit={onChangePassword} className="profile-form">
          <label>
            Senha atual
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
          </label>
          <label>
            Nova senha (mín. 8 caracteres)
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              minLength={8}
              required
            />
          </label>
          <label>
            Confirmar nova senha
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              minLength={8}
              required
            />
          </label>
          <button type="submit" className="primary" disabled={busy}>
            Atualizar senha
          </button>
        </form>
      </section>

      {message && <p className="success">{message}</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
