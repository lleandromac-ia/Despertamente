import json
import re
from pathlib import Path


def _ass_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("\n", "\\N")


def _seconds_to_ass_time(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _ticks_to_ass_time(ticks: int) -> str:
    return _seconds_to_ass_time(max(0, ticks) / 10_000_000)


def _parse_srt_time(t: str) -> float:
    h, m, rest = t.strip().split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def _group_words_for_karaoke(words: list[dict], max_chars: int = 48) -> list[list[dict]]:
    lines: list[list[dict]] = []
    current: list[dict] = []
    length = 0
    for w in words:
        text = str(w.get("text", "")).strip()
        if not text:
            continue
        add_len = len(text) + (1 if current else 0)
        if current and length + add_len > max_chars:
            lines.append(current)
            current = [w]
            length = len(text)
        else:
            current.append(w)
            length += add_len
    if current:
        lines.append(current)
    return lines


def _karaoke_line_text(line_words: list[dict]) -> str:
    parts: list[str] = []
    for w in line_words:
        text = str(w.get("text", "")).strip()
        if not text:
            continue
        duration = int(w.get("duration", 0))
        cs = max(1, duration // 100_000)
        parts.append(f"{{\\k{cs}}}{_ass_escape(text)}")
    return " ".join(parts)


def build_ass_file(
    ass_path: Path,
    width: int,
    height: int,
    *,
    subtitle_style: str,
    srt_path: Path | None = None,
    words_path: Path | None = None,
    summary_line1: str = "",
    summary_line2: str = "",
) -> None:
    events: list[str] = []
    margin_v = int(height * 0.10)

    use_karaoke = subtitle_style == "karaoke"
    if use_karaoke and words_path and words_path.is_file():
        words = json.loads(words_path.read_text(encoding="utf-8"))
        if words:
            for line_words in _group_words_for_karaoke(words):
                start = int(line_words[0]["offset"])
                end = int(line_words[-1]["offset"]) + int(line_words[-1]["duration"])
                events.append(
                    f"Dialogue: 0,{_ticks_to_ass_time(start)},{_ticks_to_ass_time(end)},"
                    f"Karaoke,,0,0,0,,{_karaoke_line_text(line_words)}"
                )
        else:
            use_karaoke = False

    if not use_karaoke and srt_path and srt_path.is_file():
        content = srt_path.read_text(encoding="utf-8")
        blocks = content.strip().split("\n\n")
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue
            time_line = lines[1]
            text = _ass_escape("\\N".join(lines[2:]))
            start_s, end_s = time_line.split(" --> ")
            start = _parse_srt_time(start_s)
            end = _parse_srt_time(end_s)
            events.append(
                f"Dialogue: 0,{_seconds_to_ass_time(start)},{_seconds_to_ass_time(end)},"
                f"Default,,0,0,0,,{text}"
            )

    # Legenda resumida (line1/line2) é só para cópia na UI — não entra no vídeo.

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,40,40,{margin_v},1
Style: Karaoke,Arial,52,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,40,40,{margin_v},1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ass_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
