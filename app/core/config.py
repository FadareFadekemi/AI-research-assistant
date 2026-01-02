from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    SERPER_API_KEY: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()

