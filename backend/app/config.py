from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


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

    @property
    def storage_path(self) -> Path:
        p = Path(self.storage_dir)
        if not p.is_absolute():
            p = ROOT_DIR / p
        return p


settings = Settings()
