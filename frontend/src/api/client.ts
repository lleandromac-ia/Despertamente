const API_BASE = import.meta.env.VITE_API_URL ?? "";

function formatApiError(detail: unknown, fallback: string): string {
  if (typeof detail === "string") {
    if (detail === "Not Found") {
      return "Rota da API não encontrada. Reinicie o backend (uvicorn --reload).";
    }
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail.map((d) => (d as { msg?: string }).msg ?? String(d)).join("; ");
  }
  return fallback;
}

async function readApiError(res: Response, fallback: string): Promise<string> {
  const text = await res.text();
  try {
    const err = JSON.parse(text) as { detail?: unknown };
    if (err.detail !== undefined) {
      return formatApiError(err.detail, fallback);
    }
  } catch {
    /* plain text body */
  }
  if (text.trim()) return formatApiError(text.trim(), fallback);
  return `${fallback} (HTTP ${res.status})`;
}

export type HealthResponse = {
  ok: boolean;
  textLimits: { min: number; max: number };
  hasOpenAI: boolean;
  hasPexels: boolean;
  hasFFmpeg?: boolean;
  ffmpegPath?: string | null;
};

export type SuggestSummaryResponse = {
  line1: string;
  line2: string;
  searchTerms: string[];
  usedFallback?: boolean;
};

export type VideoOptionsResponse = {
  voices: { id: string; label: string; gender: string }[];
  visualStyles: { id: string; label: string; description: string }[];
  subtitleStyles: { id: string; label: string; description: string }[];
  sceneMediaModes: { id: string; label: string }[];
  defaultVoice: string;
};

export type JobStatusResponse = {
  status: string;
  progress: number;
  message: string;
  error?: string | null;
  downloadUrl?: string | null;
};

export async function fetchVideoOptions(): Promise<VideoOptionsResponse> {
  const res = await fetch(`${API_BASE}/api/video-options`);
  if (!res.ok) throw new Error("Não foi possível carregar opções de vídeo");
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
    headers: { "Content-Type": "application/json" },
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
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, shortPhrase: options?.shortPhrase ?? false }),
  });
  if (!res.ok) throw new Error(await readApiError(res, "Falha ao sugerir legenda"));
  return res.json();
}

export async function createVideo(payload: {
  text: string;
  summaryLine1: string;
  summaryLine2: string;
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
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await readApiError(res, "Falha ao iniciar geração"));
  return res.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const res = await fetch(`${API_BASE}/api/videos/${jobId}`);
  if (!res.ok) throw new Error("Job não encontrado");
  return res.json();
}

export function downloadUrl(path: string): string {
  return `${API_BASE}${path}`;
}
