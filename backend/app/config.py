from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

_app_dir = Path(__file__).resolve().parent
_backend_root = _app_dir.parent
# Monorepo (backend/app/...): raiz do repo. Docker (só /app/app): raiz = /app.
if (_backend_root.parent / "frontend").is_dir():
    ROOT_DIR = _backend_root.parent
else:
    ROOT_DIR = _backend_root
load_dotenv(ROOT_DIR / ".env", override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    pexels_api_key: str = ""
    whisper_model: str = "small"
    tts_voice: str = "pt-BR-FranciscaNeural"
    video_width: int = 1080
    video_height: int = 1920
    storage_dir: str = "storage"
    ffmpeg_path: str = ""
    jwt_secret: str = "dev-change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 72
    admin_username: str = "lleandromachado"
    admin_initial_password: str = "Admin@123"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def storage_path(self) -> Path:
        p = Path(self.storage_dir)
        if not p.is_absolute():
            p = ROOT_DIR / p
        return p


def _strip_secret(value: str) -> str:
    return value.strip().strip('"').strip("'")


settings = Settings()
settings.openai_api_key = _strip_secret(settings.openai_api_key)
settings.pexels_api_key = _strip_secret(settings.pexels_api_key)
settings.jwt_secret = _strip_secret(settings.jwt_secret)
