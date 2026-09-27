import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createVideo,
  downloadUrl,
  fetchHealth,
  getJobStatus,
  enrichText,
  suggestSummary,
  transcribeOgg,
  type HealthResponse,
} from "../api/client";
import "./Editor.css";

type InputMode = "text" | "audio";

export function Editor() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [mode, setMode] = useState<InputMode>("text");
  const [text, setText] = useState("");
  const [line1, setLine1] = useState("");
  const [line2, setLine2] = useState("");
  const [searchTerms, setSearchTerms] = useState<string[]>([]);
  const [aspectRatio, setAspectRatio] = useState<"9:16" | "16:9">("9:16");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [jobMessage, setJobMessage] = useState("");
  const [download, setDownload] = useState<string | null>(null);

  const min = health?.textLimits.min ?? 350;
  const max = health?.textLimits.max ?? 500;
  const len = text.trim().length;
  const lengthOk = len >= min && len <= max;
  const belowMin = len > 0 && len < min;
  const overMax = len > max;

  const lengthClass = useMemo(() => {
    if (len === 0) return "";
    if (overMax) return "bad";
    if (belowMin) return "warn";
    return "ok";
  }, [len, belowMin, overMax]);

  const startVideoJob = useCallback(
    async (
      script: string,
      l1: string,
      l2: string,
      terms: string[],
      shortPhrase: boolean,
    ) => {
      setDownload(null);
      setJobId(null);
      setBusy("Iniciando geração do vídeo...");
      const { jobId: id } = await createVideo({
        text: script,
        summaryLine1: l1,
        summaryLine2: l2,
        searchTerms: terms,
        aspectRatio,
        shortPhrase,
      });
      setJobId(id);
      setProgress(0);
      setJobMessage("Na fila...");
    },
    [aspectRatio],
  );

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    if (!jobId) return;
    const interval = setInterval(async () => {
      try {
        const status = await getJobStatus(jobId);
        setProgress(status.progress);
        setJobMessage(status.message);
        if (status.status === "completed" && status.downloadUrl) {
          setDownload(downloadUrl(status.downloadUrl));
          setBusy(null);
          clearInterval(interval);
        } else if (status.status === "failed") {
          setError(status.error ?? "Falha na geração do vídeo");
          setBusy(null);
          clearInterval(interval);
        }
      } catch {
        setError("Erro ao consultar status do job");
        setBusy(null);
        clearInterval(interval);
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [jobId]);

  const onUpload = useCallback(
    async (file: File | null) => {
      if (!file) return;
      setError(null);
      setBusy("Transcrevendo áudio...");
      try {
        const result = await transcribeOgg(file);
        setText(result);
        setMode("text");
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro na transcrição");
      } finally {
        setBusy(null);
      }
    },
    [],
  );

  const onSuggest = useCallback(async () => {
    setError(null);
    if (!lengthOk) {
      setError(`O texto deve ter entre ${min} e ${max} caracteres.`);
      return;
    }
    setBusy("Sugerindo legenda resumida...");
    try {
      const res = await suggestSummary(text);
      setLine1(res.line1);
      setLine2(res.line2);
      setSearchTerms(res.searchTerms ?? []);
      if (res.usedFallback) {
        setError(
          "OPENAI_API_KEY não configurada: resumo gerado localmente. Você pode editar as linhas.",
        );
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao sugerir legenda");
    } finally {
      setBusy(null);
    }
  }, [text, lengthOk, min, max]);

  const onEnrich = useCallback(async () => {
    setError(null);
    if (!text.trim()) {
      setError("Informe um texto antes de enriquecer.");
      return;
    }
    if (!belowMin) {
      setError("Enriquecer só é necessário quando o texto está abaixo de 350 caracteres.");
      return;
    }
    if (overMax) {
      setError(`Reduza o texto para no máximo ${max} caracteres.`);
      return;
    }
    setBusy("Enriquecendo texto...");
    try {
      const res = await enrichText(text);
      setText(res.text);
      if (res.usedFallback) {
        setError(
          "OPENAI_API_KEY não configurada: texto ampliado com fallback local. Revise antes de gerar.",
        );
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao enriquecer texto");
    } finally {
      setBusy(null);
    }
  }, [text, belowMin, len, min, max, overMax]);

  const onShortPhrase = useCallback(async () => {
    setError(null);
    setDownload(null);
    if (!text.trim()) {
      setError("Informe um texto antes de continuar.");
      return;
    }
    if (overMax) {
      setError(`O texto deve ter no máximo ${max} caracteres.`);
      return;
    }
    setBusy("Sugerindo legenda e gerando vídeo (frase curta)...");
    try {
      const res = await suggestSummary(text, { shortPhrase: true });
      setLine1(res.line1);
      setLine2(res.line2);
      setSearchTerms(res.searchTerms ?? []);
      await startVideoJob(text, res.line1, res.line2, res.searchTerms ?? [], true);
      if (res.usedFallback) {
        setError(
          "Resumo gerado localmente (sem OpenAI). O vídeo está sendo produzido com o texto atual.",
        );
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro no fluxo de frase curta");
      setBusy(null);
    }
  }, [text, overMax, max, startVideoJob]);

  const onGenerate = useCallback(async () => {
    setError(null);
    setDownload(null);
    if (!lengthOk) {
      setError(`O texto deve ter entre ${min} e ${max} caracteres.`);
      return;
    }
    if (!line1.trim() || !line2.trim()) {
      setError("Preencha ou sugira as duas linhas do resumo antes de gerar.");
      return;
    }
    try {
      await startVideoJob(text, line1, line2, searchTerms, false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao gerar vídeo");
      setBusy(null);
    }
  }, [text, line1, line2, searchTerms, lengthOk, min, max, startVideoJob]);

  return (
    <div className="editor">
      <header className="editor-header">
        <h1>GeraVideos</h1>
        <p>Texto ou áudio .ogg → vídeo narrado com mídia temática e legendas</p>
        {health && (
          <div className="badges">
            <span className={health.hasOpenAI ? "on" : "off"}>
              IA resumo: {health.hasOpenAI ? "ativa" : "fallback local"}
            </span>
            <span className={health.hasPexels ? "on" : "off"}>
              Pexels: {health.hasPexels ? "ativa" : "fundo sólido"}
            </span>
          </div>
        )}
      </header>

      <div className="mode-tabs">
        <button
          type="button"
          className={mode === "text" ? "active" : ""}
          onClick={() => setMode("text")}
        >
          Texto direto
        </button>
        <button
          type="button"
          className={mode === "audio" ? "active" : ""}
          onClick={() => setMode("audio")}
        >
          Áudio .ogg
        </button>
      </div>

      {mode === "audio" && (
        <section className="panel">
          <label className="file-label">
            Enviar arquivo .ogg
            <input
              type="file"
              accept=".ogg,audio/ogg"
              onChange={(e) => onUpload(e.target.files?.[0] ?? null)}
            />
          </label>
          <p className="hint">Após transcrever, edite o texto abaixo se necessário.</p>
        </section>
      )}

      <section className="panel">
        <label htmlFor="script">Roteiro ({min}–{max} caracteres)</label>
        <textarea
          id="script"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={8}
          placeholder="Cole ou escreva o texto que será narrado no vídeo..."
        />
        <div className={`counter ${lengthClass}`}>
          {len} / {max}{" "}
          {lengthOk ? "✓" : overMax ? "(acima do máximo)" : `(mín. ${min})`}
        </div>
        {belowMin && (
          <div className="short-actions">
            <p className="hint">
              Texto abaixo do mínimo. Enriqueça para atingir {min} caracteres ou siga com frase
              curta.
            </p>
            <div className="short-actions-buttons">
              <button type="button" onClick={onEnrich} disabled={!!busy}>
                Enriquecer
              </button>
              <button
                type="button"
                className="primary"
                onClick={onShortPhrase}
                disabled={!!busy}
              >
                Frase curta
              </button>
            </div>
          </div>
        )}
      </section>

      <section className="panel">
        <div className="row">
          <h2>Legenda resumida (2 linhas)</h2>
          <button type="button" onClick={onSuggest} disabled={!!busy || !lengthOk}>
            Sugerir legenda
          </button>
        </div>
        <input
          type="text"
          value={line1}
          onChange={(e) => setLine1(e.target.value)}
          placeholder="Linha 1"
          maxLength={80}
        />
        <input
          type="text"
          value={line2}
          onChange={(e) => setLine2(e.target.value)}
          placeholder="Linha 2"
          maxLength={80}
        />
      </section>

      <section className="panel row">
        <label>
          Proporção
          <select
            value={aspectRatio}
            onChange={(e) => setAspectRatio(e.target.value as "9:16" | "16:9")}
          >
            <option value="9:16">Vertical 9:16</option>
            <option value="16:9">Horizontal 16:9</option>
          </select>
        </label>
        <button
          type="button"
          className="primary"
          onClick={onGenerate}
          disabled={!!busy || !lengthOk}
        >
          Gerar vídeo
        </button>
      </section>

      {busy && <p className="status">{busy}</p>}
      {jobId && !download && (
        <div className="progress-wrap">
          <div className="progress-bar" style={{ width: `${progress}%` }} />
          <span>
            {jobMessage} ({progress}%)
          </span>
        </div>
      )}
      {download && (
        <p className="success">
          <a href={download} download>
            Baixar vídeo MP4
          </a>
        </p>
      )}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
