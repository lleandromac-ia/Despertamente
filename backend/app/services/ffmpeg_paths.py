import os
import shutil
from pathlib import Path


def _winget_ffmpeg_bins() -> list[Path]:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        return []
    packages = Path(local) / "Microsoft" / "WinGet" / "Packages"
    if not packages.is_dir():
        return []
    bins: list[Path] = []
    for pkg in packages.glob("Gyan.FFmpeg*"):
        for exe in pkg.rglob("ffmpeg.exe"):
            bin_dir = exe.parent
            if bin_dir not in bins:
                bins.append(bin_dir)
    return bins


def resolve_ffmpeg_bin(name: str, configured_dir: str = "") -> str | None:
    if configured_dir:
        candidate = Path(configured_dir) / f"{name}.exe"
        if candidate.is_file():
            return str(candidate)
        candidate = Path(configured_dir) / name
        if candidate.is_file():
            return str(candidate)

    found = shutil.which(name)
    if found:
        return found

    for bin_dir in _winget_ffmpeg_bins():
        candidate = bin_dir / f"{name}.exe"
        if candidate.is_file():
            return str(candidate)

    return None
