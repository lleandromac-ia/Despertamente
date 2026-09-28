import { API_BASE } from "./config";
import { authHeaders, readApiError } from "./http";

export type HealthResponse = {
  ok: boolean;
  textLimits: { min: number; max: number };
  hasOpenAI: boolean;
  hasPexels: boolean;
  hasFFmpeg?: boolean;
  ffmpegPath?: string | null;
};

export type VideoOptionsResponse = {
  voices: { id: string; label: string; gender: string }[];
  visualStyles: { id: string; label: string; description: string }[];
  subtitleStyles: { id: string; label: string; description: string }[];
  sceneMediaModes: { id: string; label: string }[];
  defaultVoice: string;
};

export type SuggestSummaryResponse = {
  line1: string;
  line2: string;
  caption?: string;
  searchTerms: string[];
  usedFallback?: boolean;
};

export type JobStatusResponse = {
  status: string;
  progress: number;
  message: string;
  error?: string | null;
  downloadUrl?: string | null;
};

export async function fetchVideoOptions(): Promise<VideoOptionsResponse> {
  const res = await fetch(`${API_BASE}/api/video-options`, { headers: authHeaders() });
  if (!res.ok) throw new Error(await readApiError(res, "Não foi possível carregar opções de vídeo"));
  return res.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error("API indisponível");
  return res.json();
}

export async function transcribeOgg(file: File): Promise<string> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/api/transcribe`, {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  if (!res.ok) throw new Error(await readApiError(res, "Falha na transcrição"));
  const data = await res.json();
  return data.text as string;
}

export async function enrichText(text: string): Promise<{
  text: string;
  usedFallback?: boolean;
  fallbackReason?: string;
  message?: string;
}> {
  const res = await fetch(`${API_BASE}/api/enrich-text`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(await readApiError(res, "Falha ao enriquecer texto"));
  return res.json();
}

export async function suggestSummary(
  text: string,
  options?: { shortPhrase?: boolean },
): Promise<SuggestSummaryResponse> {
  const res = await fetch(`${API_BASE}/api/suggest-summary`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text, shortPhrase: options?.shortPhrase ?? false }),
  });
  if (!res.ok) throw new Error(await readApiError(res, "Falha ao sugerir legenda"));
  return res.json();
}

export async function createVideo(payload: {
  text: string;
  summaryLine1?: string;
  summaryLine2?: string;
  searchTerms: string[];
  aspectRatio?: string;
  shortPhrase?: boolean;
  narratorVoice?: string;
  visualStyle?: string;
  subtitleStyle?: string;
  sceneMedia?: string;
}): Promise<{ jobId: string }> {
  const res = await fetch(`${API_BASE}/api/videos`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await readApiError(res, "Falha ao iniciar geração"));
  return res.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const res = await fetch(`${API_BASE}/api/videos/${jobId}`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Job não encontrado");
  return res.json();
}

export function downloadUrl(path: string): string {
  const token = (() => {
    try {
      const raw = localStorage.getItem("geravideos_auth");
      if (!raw) return null;
      return (JSON.parse(raw) as { accessToken?: string }).accessToken ?? null;
    } catch {
      return null;
    }
  })();
  const base = `${API_BASE}${path}`;
  if (!token) return base;
  return `${base}?access_token=${encodeURIComponent(token)}`;
}
