from pathlib import Path

from app.config import settings

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        _model = WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")
    return _model


def transcribe_audio(audio_path: Path) -> str:
    model = _get_model()
    segments, _info = model.transcribe(str(audio_path), language="pt")
    parts = [seg.text.strip() for seg in segments if seg.text.strip()]
    return " ".join(parts)
