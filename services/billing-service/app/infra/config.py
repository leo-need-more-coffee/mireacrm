from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BILLING_", env_file=".env", extra="ignore")

    service_name: str = "billing-service"
    postgres_dsn: str = "postgresql+asyncpg://billing_user:billing_pass@localhost:5432/billing_db"
    http_port: int = 8006
    grpc_port: int = 9006
    amqp_url: str = "amqp://guest:guest@localhost:5672/"
    booking_addr: str = "localhost:9003"
    client_addr: str = "localhost:9005"
    debug: bool = False
    # Пустой адрес выключает экспорт трасс: нужен для тестов
    # и запуска без инфраструктуры.
    otlp_endpoint: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
