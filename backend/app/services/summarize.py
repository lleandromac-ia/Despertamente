import json
import re

import httpx

from app.config import settings


def _fallback_summary(text: str) -> dict:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s for s in sentences if s]
    line1 = sentences[0][:80] if sentences else text[:80]
    line2 = sentences[1][:80] if len(sentences) > 1 else text[80:160]
    if not line2.strip():
        line2 = text[-80:].strip()
    words = re.findall(r"\w{4,}", text.lower())
    seen: set[str] = set()
    terms: list[str] = []
    for w in words:
        if w not in seen:
            seen.add(w)
            terms.append(w)
        if len(terms) >= 5:
            break
    if not terms:
        terms = ["nature", "people", "city"]
    return {"line1": line1.strip(), "line2": line2.strip(), "searchTerms": terms}


async def suggest_summary_and_keywords(text: str) -> dict:
    if not settings.openai_api_key:
        return _fallback_summary(text)

    prompt = (
        "Analise o texto em português abaixo. Responda APENAS com JSON válido, sem markdown:\n"
        '{"line1": "primeira linha curta de legenda resumida", '
        '"line2": "segunda linha curta", '
        '"searchTerms": ["termo1", "termo2", "termo3"]}\n'
        "Regras: line1 e line2 com no máximo 60 caracteres cada; "
        "searchTerms com 3 a 5 termos em inglês para busca de stock video/foto.\n\n"
        f"Texto:\n{text}"
    )
    url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.openai_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            data = json.loads(content.strip())
            return {
                "line1": str(data.get("line1", ""))[:60],
                "line2": str(data.get("line2", ""))[:60],
                "searchTerms": list(data.get("searchTerms", []))[:5],
            }
    except Exception:
        return _fallback_summary(text)

