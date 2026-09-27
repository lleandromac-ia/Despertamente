import re

MIN_CHARS = 350
MAX_CHARS = 500


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def validate_script_length(
    text: str, *, allow_short: bool = False
) -> tuple[str, int]:
    normalized = normalize_text(text)
    length = len(normalized)
    if not normalized:
        raise ValueError("Informe um texto para continuar.")
    if length > MAX_CHARS:
        raise ValueError(
            f"O texto deve ter no máximo {MAX_CHARS} caracteres (atual: {length})."
        )
    if not allow_short and length < MIN_CHARS:
        raise ValueError(
            f"O texto deve ter entre {MIN_CHARS} e {MAX_CHARS} caracteres "
            f"(atual: {length}). Use Enriquecer ou Frase curta."
        )
    return normalized, length
