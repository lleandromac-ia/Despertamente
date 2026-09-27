import json
import re

import httpx

from app.config import settings
from app.validation import MAX_CHARS, MIN_CHARS, normalize_text


def _fallback_enrich(text: str) -> str:
    base = normalize_text(text)
    if len(base) >= MIN_CHARS:
        return base[:MAX_CHARS]

    extras = [
        " Isso nos convida a olhar o assunto com mais profundidade e clareza.",
        " Compreender esse contexto ajuda a tomar decisões mais conscientes no dia a dia.",
        " Pequenos detalhes fazem diferença quando queremos comunicar com precisão.",
        " Por isso, vale a pena dedicar atenção à forma como expressamos essa ideia.",
        " Assim, a mensagem chega de maneira mais completa a quem nos escuta.",
    ]
    result = base
    i = 0
    while len(result) < MIN_CHARS and i < 30:
        result += extras[i % len(extras)]
        i += 1
    if len(result) > MAX_CHARS:
        trimmed = result[:MAX_CHARS]
        last_space = trimmed.rfind(" ")
        if last_space > MIN_CHARS:
            return trimmed[:last_space].strip()
        return trimmed.strip()
    return result.strip()


async def enrich_text_to_minimum(text: str) -> dict:
    normalized = normalize_text(text)
    if not normalized:
        raise ValueError("Informe um texto para enriquecer.")
    if len(normalized) >= MIN_CHARS:
        if len(normalized) > MAX_CHARS:
            raise ValueError(f"O texto já excede {MAX_CHARS} caracteres.")
        return {"text": normalized, "usedFallback": False}

    if not settings.openai_api_key:
        return {
            "text": _fallback_enrich(normalized),
            "usedFallback": True,
            "fallbackReason": "no_key",
            "message": "OPENAI_API_KEY não configurada no arquivo .env na raiz do projeto.",
        }

    prompt = (
        f"Reescreva e expanda o texto abaixo em português do Brasil, mantendo o mesmo sentido e tom, "
        f"de forma mais elaborada e natural. O resultado final deve ter entre {MIN_CHARS} e {MAX_CHARS} "
        f"caracteres (inclusive). Responda APENAS com o texto final, sem aspas, título ou explicação.\n\n"
        f"Texto original ({len(normalized)} caracteres):\n{normalized}"
    )
    url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.openai_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.6,
    }
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            content = re.sub(r"^[\"']|[\"']$", "", content)
            enriched = normalize_text(content)
            if len(enriched) < MIN_CHARS:
                enriched = _fallback_enrich(enriched)
            if len(enriched) > MAX_CHARS:
                enriched = enriched[:MAX_CHARS]
                last_space = enriched.rfind(" ")
                if last_space >= MIN_CHARS:
                    enriched = enriched[:last_space].strip()
            return {"text": enriched, "usedFallback": False}
    except httpx.HTTPStatusError as exc:
        detail = "Erro na API OpenAI."
        try:
            detail = exc.response.json().get("error", {}).get("message", detail)
        except Exception:
            pass
        return {
            "text": _fallback_enrich(normalized),
            "usedFallback": True,
            "fallbackReason": "api_error",
            "message": f"{detail} Texto ampliado localmente — revise antes de gerar.",
        }
    except Exception as exc:
        return {
            "text": _fallback_enrich(normalized),
            "usedFallback": True,
            "fallbackReason": "api_error",
            "message": f"Falha ao contactar OpenAI ({exc}). Texto ampliado localmente.",
        }
