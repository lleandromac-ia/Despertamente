import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from app.config import settings
from app.services.pexels import download_media_assets
from app.services.tts import generate_narration
from app.services.video_compose import FFmpegNotFoundError, render_video_pipeline


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    id: str
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    message: str = "Aguardando..."
    error: Optional[str] = None
    output_path: Optional[Path] = None
    meta_path: Optional[Path] = None


_jobs: dict[str, Job] = {}


def create_job() -> Job:
    job_id = str(uuid.uuid4())
    job = Job(id=job_id)
    _jobs[job_id] = job
    return job


def get_job(job_id: str) -> Optional[Job]:
    return _jobs.get(job_id)


async def _set(job: Job, progress: int, message: str) -> None:
    job.progress = progress
    job.message = message
    await asyncio.sleep(0)


async def run_video_job(
    job: Job,
    text: str,
    summary_line1: str,
    summary_line2: str,
    search_terms: list[str],
    aspect_ratio: str | None = None,
) -> None:
    job.status = JobStatus.RUNNING
    width = settings.video_width
    height = settings.video_height
    if aspect_ratio == "16:9":
        width, height = 1920, 1080

    base = settings.storage_path / "jobs" / job.id
    base.mkdir(parents=True, exist_ok=True)

    audio_path = base / "narration.mp3"
    srt_path = base / "subs.srt"
    ass_path = base / "subs.ass"
    assets_dir = base / "assets"
    output_path = base / "output.mp4"
    meta_path = base / "summary.txt"

    try:
        await _set(job, 10, "Gerando narração...")
        await generate_narration(text, settings.tts_voice, audio_path, srt_path)

        await _set(job, 35, "Buscando mídia temática...")
        assets = await download_media_assets(search_terms, assets_dir)

        await _set(job, 60, "Montando vídeo...")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: render_video_pipeline(
                text=text,
                assets=assets,
                audio_path=audio_path,
                srt_path=srt_path,
                ass_path=ass_path,
                work_dir=base / "work",
                output_path=output_path,
                summary_line1=summary_line1,
                summary_line2=summary_line2,
                width=width,
                height=height,
            ),
        )

        meta_path.write_text(
            f"{summary_line1}\n{summary_line2}\n",
            encoding="utf-8",
        )
        job.output_path = output_path
        job.meta_path = meta_path
        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.message = "Concluído"
    except FFmpegNotFoundError as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
        job.message = "Falha"
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
        job.message = "Falha"
