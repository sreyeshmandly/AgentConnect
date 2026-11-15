from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AgentConnect"
    APP_VERSION: str = "1.0.0"

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "agentconnect"
    DB_USER: str = "postgres"
    DB_PASSWORD: str

    GEMINI_API_KEY: str | None = None

    EMBEDDING_MODEL: str = "gemini-embedding-2"
    EMBEDDING_DIMENSIONS: int = 768

    GEMINI_GENERATION_MODEL: str = "gemini-3.8-flash"

    RELEVANCE_THRESHOLD: float = Field(
        default=0.75,
        ge=0,
        le=1
    )

    ROUTING_CANDIDATE_LIMIT: int = 30
    MAX_ROUTED_AGENTS: int = 5

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    FRONTEND_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()