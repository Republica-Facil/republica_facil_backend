from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    DATABASE_URL: str
    ALGORITHM: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    FROM_EMAIL: str
    EMAIL_PASSWORD: str
    SMTP_PORT: int
    SMTP_SERVER: str
    LOCALHOST_FRONTEND: str
    LOCALHOST_FRONTEND_ADDRESS: str
