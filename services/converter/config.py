from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CONV_", env_file=BASE_DIR / ".env", extra="ignore")

    storage_dir: Path = BASE_DIR.parent.parent / "storage"
    max_file_size: int = 2 * 1024 * 1024 * 1024
    retention_seconds: int = 3600
    sweeper_interval_seconds: int = 300
    cors_origins: str = "http://localhost:3000"
    # Limite de débit par IP pour les endpoints de conversion (format slowapi/limits).
    # Exemples : "30/minute", "10/minute", "200/hour".
    rate_limit: str = "30/minute"

    def limit_for(self, plan: str | None = None) -> int:
        return self.max_file_size

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
settings.storage_dir.mkdir(parents=True, exist_ok=True)
