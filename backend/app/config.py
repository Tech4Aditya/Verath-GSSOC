from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",       # silently ignore unknown env vars
        protected_namespaces=("settings_",),
    )

    # ── Ollama ────────────────────────────────────────────────────────────────
    ollama_url: str = "http://localhost:11434"
    model_name: str = "mistral"
    embed_model: str = "nomic-embed-text"

    # ── Whisper ───────────────────────────────────────────────────────────────
    whisper_model: str = "base"
    whisper_device: str = "cpu"  # default to cpu for stability on Windows
    whisper_compute_type: str = "int8" # space-efficient


    # ── Server ────────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8002
    default_record_seconds: int = 10
    allow_cors: str = "*"

    # ── Storage ───────────────────────────────────────────────────────────────
    vector_db_path: str = "data/chroma_db"
    voice_db_path: str = "data/voices.pkl"

    # ── MongoDB (required) ────────────────────────────────────────────────────
    mongo_uri: str = Field(..., description="MongoDB connection string — required")
    database_name: str = "secondbrain"

    # ── Security (required) ───────────────────────────────────────────────────
    secret_key: str = Field(..., description="JWT secret key — required")

    # ── Validators ────────────────────────────────────────────────────────────
    @field_validator("secret_key")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if v in ("your-super-secret-key", "changeme", "secret"):
            raise ValueError("SECRET_KEY is set to a known insecure default — please change it.")
        return v

    @field_validator("port")
    @classmethod
    def port_must_be_valid(cls, v: int) -> int:
        if not (1024 <= v <= 65535):
            raise ValueError("PORT must be between 1024 and 65535")
        return v

    @field_validator("mongo_uri")
    @classmethod
    def mongo_uri_must_look_valid(cls, v: str) -> str:
        if not (v.startswith("mongodb://") or v.startswith("mongodb+srv://")):
            raise ValueError(
                "MONGO_URI must start with 'mongodb://' or 'mongodb+srv://'"
            )
        return v


# Single import point used everywhere in the app
settings = Settings()
