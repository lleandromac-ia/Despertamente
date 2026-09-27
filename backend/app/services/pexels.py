from pathlib import Path

import httpx

from app.config import settings

PEXELS_VIDEO = "https://api.pexels.com/videos/search"
PEXELS_PHOTO = "https://api.pexels.com/v1/search"


async def _fetch_videos(client: httpx.AsyncClient, query: str, per_page: int = 5) -> list[dict]:
    if not settings.pexels_api_key:
        return []
    headers = {"Authorization": settings.pexels_api_key}
    resp = await client.get(
        PEXELS_VIDEO, headers=headers, params={"query": query, "per_page": per_page}
    )
    if resp.status_code != 200:
        return []
    items = []
    for v in resp.json().get("videos", []):
        files = v.get("video_files", [])
        best = None
        for f in files:
            if f.get("width", 0) >= 720:
                if best is None or f.get("width", 0) < best.get("width", 9999):
                    best = f
        if best is None and files:
            best = files[0]
        if best and best.get("link"):
            items.append({"type": "video", "url": best["link"], "duration": v.get("duration", 5)})
    return items


async def _fetch_photos(client: httpx.AsyncClient, query: str, per_page: int = 5) -> list[dict]:
    if not settings.pexels_api_key:
        return []
    headers = {"Authorization": settings.pexels_api_key}
    resp = await client.get(
        PEXELS_PHOTO, headers=headers, params={"query": query, "per_page": per_page}
    )
    if resp.status_code != 200:
        return []
    items = []
    for p in resp.json().get("photos", []):
        src = p.get("src", {}).get("large2x") or p.get("src", {}).get("large")
        if src:
            items.append({"type": "photo", "url": src})
    return items


async def download_media_assets(
    search_terms: list[str],
    dest_dir: Path,
    min_clips: int = 4,
) -> list[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    assets: list[dict] = []
    queries = search_terms if search_terms else ["nature", "abstract"]

    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        for q in queries:
            videos = await _fetch_videos(client, q, 3)
            assets.extend(videos)
            if len(assets) >= min_clips:
                break
        if len(assets) < min_clips:
            for q in queries:
                photos = await _fetch_photos(client, q, 3)
                assets.extend(photos)
                if len(assets) >= min_clips:
                    break

        if not assets and settings.pexels_api_key:
            for fallback in ["nature", "city", "people"]:
                assets.extend(await _fetch_videos(client, fallback, 2))
                if assets:
                    break

    paths: list[Path] = []
    for i, asset in enumerate(assets[:8]):
        ext = ".mp4" if asset["type"] == "video" else ".jpg"
        out = dest_dir / f"asset_{i}{ext}"
        if out.exists():
            paths.append(out)
            continue
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            r = await client.get(asset["url"])
            r.raise_for_status()
            out.write_bytes(r.content)
        paths.append(out)
    return paths
