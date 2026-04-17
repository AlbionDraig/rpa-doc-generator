import os
from dataclasses import dataclass
from pathlib import Path


def _env_bool(name, default):
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name, default):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return int(default)


def _env_csv(name, default):
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


@dataclass(frozen=True)
class AppSettings:
    app_title: str
    app_version: str
    app_description: str
    app_host: str
    app_port: int
    app_log_level: str
    app_access_log: bool
    output_dir: Path
    tmp_dir: Path
    static_dir: Path
    cors_origins: list[str]
    public_base_url: str
    upload_chunk_size: int
    max_file_size: int
    max_extraction_size: int
    ai_quality_enabled: bool
    ai_timeout_seconds: int
    groq_api_key: str
    groq_model: str
    groq_base_url: str
    openai_api_key: str
    openai_model: str
    openai_base_url: str
    api_rate_limit_enabled: bool
    api_rate_limit_max_requests: int
    api_rate_limit_window_seconds: int
    max_concurrent_generations: int
    generation_acquire_timeout_seconds: int

    @classmethod
    def from_env(cls):
        app_port = _env_int("APP_PORT", "8000")
        return cls(
            app_title=os.getenv("APP_TITLE", "RPA Doc Generator"),
            app_version=os.getenv("APP_VERSION", "1.0.0"),
            app_description=os.getenv(
                "APP_DESCRIPTION",
                "Generador automatico de documentacion SDD para bots de Automation Anywhere",
            ),
            app_host=os.getenv("APP_HOST", "0.0.0.0"),
            app_port=app_port,
            app_log_level=os.getenv("APP_LOG_LEVEL", "info").lower(),
            app_access_log=_env_bool("APP_ACCESS_LOG", "true"),
            output_dir=Path(os.getenv("OUTPUT_DIR", "./output")),
            tmp_dir=Path(os.getenv("TMP_DIR", "./tmp")),
            static_dir=Path(os.getenv("STATIC_DIR", "./app/static")),
            cors_origins=_env_csv(
                "CORS_ORIGINS",
                "http://localhost,http://localhost:3000,http://localhost:8000,http://127.0.0.1,http://127.0.0.1:3000",
            ),
            public_base_url=os.getenv("PUBLIC_BASE_URL", f"http://localhost:{app_port}").rstrip("/"),
            upload_chunk_size=_env_int("UPLOAD_CHUNK_SIZE", str(1024 * 1024)),
            max_file_size=_env_int("MAX_FILE_SIZE", str(500 * 1024 * 1024)),
            max_extraction_size=_env_int("MAX_EXTRACTION_SIZE", str(1024 * 1024 * 1024)),
            ai_quality_enabled=_env_bool("AI_QUALITY_ENABLED", "false"),
            ai_timeout_seconds=_env_int("AI_TIMEOUT_SECONDS", "25"),
            groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
            groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip() or "llama-3.3-70b-versatile",
            groq_base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/"),
            openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini",
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
            api_rate_limit_enabled=_env_bool("API_RATE_LIMIT_ENABLED", "true"),
            api_rate_limit_max_requests=_env_int("API_RATE_LIMIT_MAX_REQUESTS", "30"),
            api_rate_limit_window_seconds=_env_int("API_RATE_LIMIT_WINDOW_SECONDS", "60"),
            max_concurrent_generations=_env_int("MAX_CONCURRENT_GENERATIONS", "2"),
            generation_acquire_timeout_seconds=_env_int("GENERATION_ACQUIRE_TIMEOUT_SECONDS", "10"),
        )
