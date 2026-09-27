import json
import shutil
import subprocess
from pathlib import Path

from app.config import settings
from app.services.ffmpeg_paths import resolve_ffmpeg_bin
from app.services.video_options import get_visual_style


class FFmpegNotFoundError(RuntimeError):
    pass


def _ffmpeg() -> str:
    exe = resolve_ffmpeg_bin("ffmpeg", settings.ffmpeg_path)
    if not exe:
        raise FFmpegNotFoundError(
            "FFmpeg não encontrado. Instale (winget install Gyan.FFmpeg) ou defina "
            "FFMPEG_PATH no .env apontando para a pasta bin do FFmpeg, e reinicie o backend."
        )
    return exe


def _ffprobe() -> str | None:
    return resolve_ffmpeg_bin("ffprobe", settings.ffmpeg_path)


def _ffprobe_duration(path: Path) -> float:
    ffprobe = _ffprobe()
    if not ffprobe:
        return 0.0
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return 0.0
    try:
        return float(json.loads(result.stdout)["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return 0.0


def _run_ffmpeg(cmd: list[str], *, cwd: Path | None = None) -> None:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        if len(detail) > 800:
            detail = detail[-800:]
        raise RuntimeError(detail or f"FFmpeg exit code {result.returncode}")


def _vf_chain(width: int, height: int, style_filter: str) -> str:
    base = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height}"
    )
    if style_filter.strip():
        return f"{base},{style_filter},format=yuv420p"
    return f"{base},format=yuv420p"


def _segment_from_image(
    ffmpeg: str,
    image: Path,
    out: Path,
    duration: float,
    width: int,
    height: int,
    style_filter: str = "",
) -> None:
    cmd = [
        ffmpeg,
        "-y",
        "-loop",
        "1",
        "-i",
        str(image),
        "-t",
        str(duration),
        "-vf",
        _vf_chain(width, height, style_filter),
        "-r",
        "30",
        "-pix_fmt",
        "yuv420p",
        str(out),
    ]
    _run_ffmpeg(cmd)


def _segment_from_video(
    ffmpeg: str,
    video: Path,
    out: Path,
    duration: float,
    width: int,
    height: int,
    style_filter: str = "",
) -> None:
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video),
        "-t",
        str(duration),
        "-vf",
        _vf_chain(width, height, style_filter),
        "-r",
        "30",
        "-an",
        "-pix_fmt",
        "yuv420p",
        str(out),
    ]
    _run_ffmpeg(cmd)


def _solid_segment(
    ffmpeg: str,
    out: Path,
    duration: float,
    width: int,
    height: int,
    color: str = "0x1a1a2e",
) -> None:
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c={color}:s={width}x{height}:d={duration}:r=30",
        "-pix_fmt",
        "yuv420p",
        str(out),
    ]
    _run_ffmpeg(cmd)


def build_visual_timeline(
    assets: list[Path],
    total_duration: float,
    work_dir: Path,
    width: int,
    height: int,
    visual_style_id: str = "realistic",
) -> Path:
    ffmpeg = _ffmpeg()
    style = get_visual_style(visual_style_id)
    work_dir.mkdir(parents=True, exist_ok=True)
    if total_duration <= 0:
        total_duration = 10.0

    if not assets:
        out = work_dir / "visual.mp4"
        _solid_segment(ffmpeg, out, total_duration, width, height, style.solid_color)
        return out

    seg_count = min(len(assets), 8)
    seg_duration = total_duration / seg_count
    segments: list[Path] = []

    for i in range(seg_count):
        asset = assets[i % len(assets)]
        seg_out = work_dir / f"seg_{i}.mp4"
        suffix = asset.suffix.lower()
        try:
            if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
                _segment_from_image(
                    ffmpeg, asset, seg_out, seg_duration, width, height, style.ffmpeg_filter
                )
            else:
                _segment_from_video(
                    ffmpeg, asset, seg_out, seg_duration, width, height, style.ffmpeg_filter
                )
            segments.append(seg_out)
        except RuntimeError:
            _solid_segment(ffmpeg, seg_out, seg_duration, width, height, style.solid_color)
            segments.append(seg_out)

    list_file = work_dir / "concat.txt"
    list_file.write_text(
        "\n".join(f"file '{s.resolve().as_posix()}'" for s in segments),
        encoding="utf-8",
    )
    visual = work_dir / "visual.mp4"
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-c",
        "copy",
        str(visual),
    ]
    _run_ffmpeg(cmd)
    return visual


def compose_final_video(
    visual_path: Path,
    audio_path: Path,
    ass_path: Path,
    output_path: Path,
    width: int,
    height: int,
) -> Path:
    ffmpeg = _ffmpeg()
    job_dir = ass_path.parent
    job_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    audio_duration = _ffprobe_duration(audio_path)
    if audio_duration <= 0:
        audio_duration = _ffprobe_duration(visual_path) or 10.0

    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(visual_path.resolve()),
        "-i",
        str(audio_path.resolve()),
        "-vf",
        f"ass={ass_path.name}",
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-t",
        str(audio_duration),
        str(output_path.resolve()),
    ]
    _run_ffmpeg(cmd, cwd=job_dir)
    return output_path


def render_video_pipeline(
    text: str,
    assets: list[Path],
    audio_path: Path,
    srt_path: Path,
    ass_path: Path,
    words_path: Path | None,
    work_dir: Path,
    output_path: Path,
    summary_line1: str,
    summary_line2: str,
    width: int,
    height: int,
    visual_style_id: str = "realistic",
    subtitle_style: str = "classic",
) -> Path:
    from app.services.ass_subtitles import build_ass_file

    build_ass_file(
        ass_path,
        width,
        height,
        subtitle_style=subtitle_style,
        srt_path=srt_path,
        words_path=words_path,
        summary_line1=summary_line1,
        summary_line2=summary_line2,
    )
    audio_duration = _ffprobe_duration(audio_path)
    if audio_duration <= 0:
        audio_duration = max(len(text.split()) * 0.45, 5.0)

    visual = build_visual_timeline(
        assets,
        audio_duration,
        work_dir / "segments",
        width,
        height,
        visual_style_id,
    )
    return compose_final_video(
        visual,
        audio_path,
        ass_path,
        output_path,
        width,
        height,
    )
