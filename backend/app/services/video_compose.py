import json
import shutil
import subprocess
import tempfile
from pathlib import Path


class FFmpegNotFoundError(RuntimeError):
    pass


def _ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise FFmpegNotFoundError(
            "FFmpeg não encontrado no PATH. Instale FFmpeg e reinicie o terminal."
        )
    return exe


def _ffprobe_duration(path: Path) -> float:
    ffprobe = shutil.which("ffprobe")
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


def _escape_filter_path(path: Path) -> str:
    p = str(path.resolve()).replace("\\", "/").replace(":", "\\:")
    return p.replace("'", "\\'")


def _segment_from_image(
    ffmpeg: str,
    image: Path,
    out: Path,
    duration: float,
    width: int,
    height: int,
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
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},format=yuv420p",
        "-r",
        "30",
        "-pix_fmt",
        "yuv420p",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def _segment_from_video(
    ffmpeg: str,
    video: Path,
    out: Path,
    duration: float,
    width: int,
    height: int,
) -> None:
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video),
        "-t",
        str(duration),
        "-vf",
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},format=yuv420p",
        "-r",
        "30",
        "-an",
        "-pix_fmt",
        "yuv420p",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


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
    subprocess.run(cmd, check=True, capture_output=True)


def build_visual_timeline(
    assets: list[Path],
    total_duration: float,
    work_dir: Path,
    width: int,
    height: int,
) -> Path:
    ffmpeg = _ffmpeg()
    work_dir.mkdir(parents=True, exist_ok=True)
    if total_duration <= 0:
        total_duration = 10.0

    if not assets:
        out = work_dir / "visual.mp4"
        _solid_segment(ffmpeg, out, total_duration, width, height)
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
                _segment_from_image(ffmpeg, asset, seg_out, seg_duration, width, height)
            else:
                _segment_from_video(ffmpeg, asset, seg_out, seg_duration, width, height)
            segments.append(seg_out)
        except subprocess.CalledProcessError:
            _solid_segment(ffmpeg, seg_out, seg_duration, width, height)
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
    subprocess.run(cmd, check=True, capture_output=True)
    return visual


def compose_final_video(
    visual_path: Path,
    audio_path: Path,
    ass_path: Path,
    output_path: Path,
    summary_line1: str,
    summary_line2: str,
    width: int,
    height: int,
) -> Path:
    ffmpeg = _ffmpeg()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    audio_duration = _ffprobe_duration(audio_path)
    if audio_duration <= 0:
        audio_duration = _ffprobe_duration(visual_path) or 10.0

    line1 = summary_line1.replace("'", "").replace(":", " ")
    line2 = summary_line2.replace("'", "").replace(":", " ")
    summary_filter = (
        f"drawbox=x=40:y=80:w={width - 80}:h=160:color=black@0.55:t=fill,"
        f"drawtext=text='{line1}':fontsize=42:fontcolor=white:x=(w-text_w)/2:y=100,"
        f"drawtext=text='{line2}':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=160:"
        f"enable='between(t,0,3)'"
    )
    ass_esc = _escape_filter_path(ass_path)
    vf = (
        f"{summary_filter},ass='{ass_esc}'"
    )

    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(visual_path),
        "-i",
        str(audio_path),
        "-vf",
        vf,
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
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def render_video_pipeline(
    text: str,
    assets: list[Path],
    audio_path: Path,
    srt_path: Path,
    ass_path: Path,
    work_dir: Path,
    output_path: Path,
    summary_line1: str,
    summary_line2: str,
    width: int,
    height: int,
) -> Path:
    from app.services.tts import srt_to_ass_bottom

    srt_to_ass_bottom(srt_path, ass_path, width, height)
    audio_duration = _ffprobe_duration(audio_path)
    if audio_duration <= 0:
        audio_duration = max(len(text.split()) * 0.45, 5.0)

    visual = build_visual_timeline(assets, audio_duration, work_dir / "segments", width, height)
    return compose_final_video(
        visual,
        audio_path,
        ass_path,
        output_path,
        summary_line1,
        summary_line2,
        width,
        height,
    )
