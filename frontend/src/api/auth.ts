import type { AuthSession, User } from "../auth/types";
import { readApiError } from "./http";
import { API_BASE, apiUrl } from "./config";

const STORAGE_KEY = "geravideos_auth";

export function readStoredSession(): AuthSession | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthSession;
  } catch {
    return null;
  }
}

export function storeSession(session: AuthSession) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function logoutStorage() {
  localStorage.removeItem(STORAGE_KEY);
}

export function getAccessToken(): string | null {
  return readStoredSession()?.accessToken ?? null;
}

export async function login(username: string, password: string): Promise<AuthSession> {
  if (!import.meta.env.DEV && !API_BASE) {
    throw new Error(
      "VITE_API_URL não configurada. Na Vercel, aponte para a API (ex.: Render) e redeploy.",
    );
  }
  let res: Response;
  try {
    res = await fetch(apiUrl("/api/auth/login"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
  } catch {
    if (import.meta.env.DEV) {
      throw new Error(
        "Não foi possível conectar à API local. Suba o backend na porta 8000 " +
          "(cd backend && .venv\\Scripts\\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000).",
      );
    }
    throw new Error(
      `A API em ${API_BASE} não respondeu. Abra ${API_BASE}/api/health no navegador — ` +
        "se aparecer 'Not Found', o serviço despertamente-api ainda não foi criado no Render " +
        "(Dashboard → New → Blueprint → repo Despertamente). Depois do deploy Live, faça redeploy na Vercel.",
    );
  }
  if (!res.ok) throw new Error(await readApiError(res, "Falha no login"));
  return res.json();
}

export async function fetchMe(token: string): Promise<{ user: User }> {
  const res = await fetch(apiUrl("/api/auth/me"), {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(await readApiError(res, "Sessão inválida"));
  return res.json();
}

export async function updateProfile(
  token: string,
  body: Partial<User>,
): Promise<{ user: User }> {
  const res = await fetch(apiUrl("/api/auth/me/profile"), {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      fullName: body.fullName,
      email: body.email,
      phone: body.phone,
      socialInstagram: body.socialInstagram,
      socialTiktok: body.socialTiktok,
      socialYoutube: body.socialYoutube,
      socialWebsite: body.socialWebsite,
    }),
  });
  if (!res.ok) throw new Error(await readApiError(res, "Falha ao salvar perfil"));
  return res.json();
}

export async function changePassword(
  token: string,
  currentPassword: string,
  newPassword: string,
): Promise<{ user: User }> {
  const res = await fetch(apiUrl("/api/auth/me/password"), {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ currentPassword, newPassword }),
  });
  if (!res.ok) throw new Error(await readApiError(res, "Falha ao alterar senha"));
  return res.json();
}

export async function listUsers(token: string): Promise<{ users: User[] }> {
  const res = await fetch(apiUrl("/api/auth/users"), {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(await readApiError(res, "Falha ao listar usuários"));
  return res.json();
}

export async function createUserAdmin(
  token: string,
  body: {
    username: string;
    password: string;
    fullName?: string;
    email?: string;
    role?: string;
  },
): Promise<{ user: User }> {
  const res = await fetch(apiUrl("/api/auth/users"), {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await readApiError(res, "Falha ao criar usuário"));
  return res.json();
}
