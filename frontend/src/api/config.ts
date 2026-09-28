/** URL do backend FastAPI. Obrigatória em produção (Vercel). Vazio = requisições relativas (/api → proxy Vite em dev). */
const configuredBase = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

/** Em dev, ignora VITE_API_URL do sistema/.env para usar o proxy local (127.0.0.1:8000). */
export const API_BASE = import.meta.env.DEV ? "" : configuredBase;

export const isApiConfigured = Boolean(API_BASE || import.meta.env.DEV);

export function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${p}`;
}

export function apiDisplayLabel(): string {
  if (import.meta.env.DEV) return "local (proxy /api → 127.0.0.1:8000)";
  return API_BASE || "(não configurada)";
}
