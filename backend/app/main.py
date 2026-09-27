import asyncio
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.jobs.manager import JobStatus, create_job, get_job, run_video_job
from app.services.enrich import enrich_text_to_minimum
from app.services.summarize import suggest_summary_and_keywords
from app.services.transcribe import transcribe_audio
from app.validation import MIN_CHARS, MAX_CHARS, validate_script_length

app = FastAPI(title="GeraVideos API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def ensure_storage() -> None:
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    (settings.storage_path / "uploads").mkdir(parents=True, exist_ok=True)


class SuggestSummaryRequest(BaseModel):
    text: str
    shortPhrase: bool = False


class CreateVideoRequest(BaseModel):
    text: str
    summaryLine1: str = Field(..., max_length=80)
    summaryLine2: str = Field(..., max_length=80)
    searchTerms: list[str] = Field(default_factory=list)
    aspectRatio: str | None = None
    shortPhrase: bool = False


class EnrichTextRequest(BaseModel):
    text: str


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "textLimits": {"min": MIN_CHARS, "max": MAX_CHARS},
        "hasOpenAI": bool(settings.openai_api_key),
        "hasPexels": bool(settings.pexels_api_key),
    }


@app.post("/api/transcribe")
async def transcribe(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".ogg"):
        raise HTTPException(400, "Envie um arquivo .ogg")

    upload_dir = settings.storage_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / file.filename
    content = await file.read()
    dest.write_bytes(content)

    try:
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, transcribe_audio, dest)
    except Exception as e:
        raise HTTPException(500, f"Erro na transcrição: {e}") from e

    return {"text": text}


@app.post("/api/enrich-text")
async def enrich_text(body: EnrichTextRequest):
    try:
        normalized, length = validate_script_length(body.text, allow_short=True)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    if length >= MIN_CHARS:
        raise HTTPException(
            400,
            f"O texto já atinge o mínimo de {MIN_CHARS} caracteres. Edite ou gere o vídeo.",
        )
    try:
        result = await enrich_text_to_minimum(normalized)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return result


@app.post("/api/suggest-summary")
async def suggest_summary(body: SuggestSummaryRequest):
    try:
        text, _ = validate_script_length(body.text, allow_short=body.shortPhrase)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    result = await suggest_summary_and_keywords(text)
    if not settings.openai_api_key:
        result["usedFallback"] = True
    else:
        result["usedFallback"] = False
    return result


@app.post("/api/videos")
async def create_video(body: CreateVideoRequest, background_tasks: BackgroundTasks):
    try:
        text, _ = validate_script_length(body.text, allow_short=body.shortPhrase)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    if not body.summaryLine1.strip() or not body.summaryLine2.strip():
        raise HTTPException(400, "Preencha as duas linhas do resumo.")

    job = create_job()
    terms = body.searchTerms or []

    async def _run():
        await run_video_job(
            job,
            text,
            body.summaryLine1.strip(),
            body.summaryLine2.strip(),
            terms,
            body.aspectRatio,
        )

    background_tasks.add_task(_run)
    return {"jobId": job.id}


@app.get("/api/videos/{job_id}")
def video_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job não encontrado")

    download_url = None
    if job.status == JobStatus.COMPLETED and job.output_path:
        download_url = f"/api/videos/{job_id}/file"

    return {
        "status": job.status.value,
        "progress": job.progress,
        "message": job.message,
        "error": job.error,
        "downloadUrl": download_url,
    }


@app.get("/api/videos/{job_id}/file")
def video_file(job_id: str):
    job = get_job(job_id)
    if not job or job.status != JobStatus.COMPLETED or not job.output_path:
        raise HTTPException(404, "Vídeo não disponível")
    path = Path(job.output_path)
    if not path.is_file():
        raise HTTPException(404, "Arquivo não encontrado")
    return FileResponse(path, media_type="video/mp4", filename=f"geravideos-{job_id[:8]}.mp4")


@app.get("/api/videos/{job_id}/summary")
def video_summary_meta(job_id: str):
    job = get_job(job_id)
    if not job or not job.meta_path or not job.meta_path.is_file():
        raise HTTPException(404, "Metadados não disponíveis")
    return FileResponse(job.meta_path, media_type="text/plain")
