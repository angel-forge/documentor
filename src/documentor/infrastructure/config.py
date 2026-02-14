from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    rewrite_model: str = ""
    cors_origins: list[str] = ["http://localhost:5173"]
