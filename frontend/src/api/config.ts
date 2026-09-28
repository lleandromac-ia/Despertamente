/** URL do backend FastAPI. Obrigatória em produção (Vercel). Vazio = usa proxy local do Vite em dev. */
export const API_BASE = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

export const isApiConfigured = Boolean(API_BASE || import.meta.env.DEV);
