import json
import re

import httpx

from app.config import settings

MAX_LINE_CHARS = 48


def extract_search_terms(text: str) -> list[str]:
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
    return terms


def _shorten_phrase(raw: str, limit: int = MAX_LINE_CHARS) -> str:
    s = re.sub(r"\s+", " ", raw.strip())
    if len(s) <= limit:
        return s
    cut = s[: limit - 1].rsplit(" ", 1)[0]
    return (cut or s[:limit]).strip() + "…"


def _fallback_summary(text: str) -> dict:
    """Resumo novo e curto (não copia o texto original inteiro)."""
    plain = re.sub(r"\s+", " ", text.strip())
    words = plain.split()
    if len(words) <= 4:
        line1 = _shorten_phrase(plain)
        line2 = ""
    else:
        mid = max(2, len(words) // 2)
        line1 = _shorten_phrase(" ".join(words[:mid]))
        line2 = _shorten_phrase(" ".join(words[mid:]))
    if not line2.strip():
        line2 = _shorten_phrase(plain[len(line1) :].strip() or plain)
    terms = extract_search_terms(text)
    return {
        "line1": line1.strip()[:MAX_LINE_CHARS],
        "line2": line2.strip()[:MAX_LINE_CHARS],
        "searchTerms": terms,
        "caption": f"{line1.strip()}\n{line2.strip()}".strip(),
    }


async def suggest_summary_and_keywords(text: str) -> dict:
    if not settings.openai_api_key:
        return _fallback_summary(text)

    prompt = (
        "Analise o texto em português abaixo. Crie uma NOVA legenda resumida para "
        "publicação (redes sociais / descrição), bem mais curta que o texto original — "
        "não copie frases longas do texto; reformule com outras palavras.\n"
        "Responda APENAS com JSON válido, sem markdown:\n"
        '{"line1": "primeira linha bem curta", '
        '"line2": "segunda linha bem curta", '
        '"searchTerms": ["termo1", "termo2", "termo3"]}\n'
        f"Regras: line1 e line2 com no máximo {MAX_LINE_CHARS} caracteres cada; "
        "juntas formam um gancho de duas linhas; "
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
        "temperature": 0.5,
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            data = json.loads(content.strip())
            line1 = str(data.get("line1", ""))[:MAX_LINE_CHARS].strip()
            line2 = str(data.get("line2", ""))[:MAX_LINE_CHARS].strip()
            return {
                "line1": line1,
                "line2": line2,
                "searchTerms": list(data.get("searchTerms", []))[:5],
                "caption": f"{line1}\n{line2}".strip() if line2 else line1,
            }
    except Exception:
        return _fallback_summary(text)
