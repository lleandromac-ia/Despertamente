import json
import re
from pathlib import Path

from edge_tts import Communicate, SubMaker


def _format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _srt_duration_seconds(srt: str) -> float:
    matches = re.findall(
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})",
        srt,
    )
    if not matches:
        return 0.0
    last = matches[-1]
    end = (
        int(last[4]) * 3600
        + int(last[5]) * 60
        + int(last[6])
        + int(last[7]) / 1000
    )
    return float(end)


def _fallback_srt(text: str, duration: float) -> str:
    return (
        f"1\n"
        f"{_format_srt_time(0)} --> {_format_srt_time(max(duration, 5))}\n"
        f"{text}\n"
    )


async def generate_narration(
    text: str,
    voice: str,
    audio_path: Path,
    srt_path: Path,
    words_path: Path | None = None,
) -> float:
    communicate = Communicate(text, voice)
    sub_maker = SubMaker()
    word_boundaries: list[dict] = []
    audio_path.parent.mkdir(parents=True, exist_ok=True)

    with open(audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_boundaries.append(
                    {
                        "text": chunk["text"],
                        "offset": chunk["offset"],
                        "duration": chunk["duration"],
                    }
                )
                sub_maker.feed(chunk)
            elif chunk["type"] == "SentenceBoundary":
                if not word_boundaries:
                    sub_maker.feed(chunk)

    if words_path is not None:
        words_path.write_text(
            json.dumps(word_boundaries, ensure_ascii=False),
            encoding="utf-8",
        )

    srt_content = sub_maker.get_srt().strip()
    if not srt_content:
        duration = max(len(text.split()) * 0.45, 5.0)
        srt_content = _fallback_srt(text, duration)
    srt_path.write_text(srt_content, encoding="utf-8")

    duration = _srt_duration_seconds(srt_content)
    if duration <= 0:
        duration = max(len(text.split()) * 0.45, 5.0)
    return duration
