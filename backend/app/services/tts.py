import re
from pathlib import Path

from edge_tts import Communicate, SubMaker


def _format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def srt_to_ass_bottom(srt_path: Path, ass_path: Path, width: int, height: int) -> None:
    """Convert SRT to ASS with subtitles at bottom ~10% margin."""
    content = srt_path.read_text(encoding="utf-8")
    blocks = content.strip().split("\n\n")
    events = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        time_line = lines[1]
        text = "\\N".join(lines[2:])
        start_s, end_s = time_line.split(" --> ")

        def parse(t: str) -> float:
            h, m, rest = t.strip().split(":")
            s, ms = rest.split(",")
            return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

        start = parse(start_s)
        end = parse(end_s)
        sh = int(start // 3600)
        sm = int((start % 3600) // 60)
        ss = start % 60
        eh = int(end // 3600)
        em = int((end % 3600) // 60)
        es = end % 60
        start_ass = f"{sh}:{sm:02d}:{ss:05.2f}"
        end_ass = f"{eh}:{em:02d}:{es:05.2f}"
        events.append(f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{text}")

    margin_v = int(height * 0.10)
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ass_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")


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
) -> float:
    communicate = Communicate(text, voice)
    sub_maker = SubMaker()
    audio_path.parent.mkdir(parents=True, exist_ok=True)

    with open(audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                sub_maker.feed(chunk)

    srt_content = sub_maker.get_srt().strip()
    if not srt_content:
        duration = max(len(text.split()) * 0.45, 5.0)
        srt_content = _fallback_srt(text, duration)
    srt_path.write_text(srt_content, encoding="utf-8")

    duration = _srt_duration_seconds(srt_content)
    if duration <= 0:
        duration = max(len(text.split()) * 0.45, 5.0)
    return duration
