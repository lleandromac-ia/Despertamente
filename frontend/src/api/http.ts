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
  if (res.status === 405) {
    return (
      "HTTP 405: a requisição foi para o site estático (Vercel), não para a API. " +
      "Configure VITE_API_URL na Vercel com a URL do backend e faça redeploy."
    );
  }
  if (res.status === 404 && fallback.toLowerCase().includes("login")) {
    return "API de login não encontrada. Verifique VITE_API_URL e se o backend está no ar.";
  }
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
