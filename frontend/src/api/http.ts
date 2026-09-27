export function formatApiError(detail: unknown, fallback: string): string {
  if (typeof detail === "string") {
    if (detail === "Not Found") {
      return "Rota da API não encontrada. Verifique VITE_API_URL e o backend.";
    }
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail.map((d) => (d as { msg?: string }).msg ?? String(d)).join("; ");
  }
  return fallback;
}

export async function readApiError(res: Response, fallback: string): Promise<string> {
  const text = await res.text();
  try {
    const err = JSON.parse(text) as { detail?: unknown };
    if (err.detail !== undefined) {
      return formatApiError(err.detail, fallback);
    }
  } catch {
    /* plain text */
  }
  if (text.trim()) return formatApiError(text.trim(), fallback);
  return `${fallback} (HTTP ${res.status})`;
}

export function authHeaders(): HeadersInit {
  const raw = localStorage.getItem("geravideos_auth");
  if (!raw) return {};
  try {
    const token = (JSON.parse(raw) as { accessToken?: string }).accessToken;
    if (token) return { Authorization: `Bearer ${token}` };
  } catch {
    /* ignore */
  }
  return {};
}
