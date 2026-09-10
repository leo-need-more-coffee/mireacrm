from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CATALOG_", env_file=".env", extra="ignore")

    service_name: str = "catalog-service"
    postgres_dsn: str = "postgresql+asyncpg://catalog_user:catalog_pass@localhost:5432/catalog_db"
    http_port: int = 8002
    grpc_port: int = 9002
    amqp_url: str = "amqp://guest:guest@localhost:5672/"
    debug: bool = False
    # Пустой адрес выключает экспорт трасс: нужен для тестов
    # и запуска без инфраструктуры.
    otlp_endpoint: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
