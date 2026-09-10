from functools import lru_cache

from mireacrm_common.config import ServiceSettings
from pydantic_settings import SettingsConfigDict


class Settings(ServiceSettings):
    model_config = SettingsConfigDict(env_prefix="CLIENT_", env_file=".env", extra="ignore")

    service_name: str = "client-service"
    postgres_dsn: str = "postgresql+asyncpg://client_user:client_pass@localhost:5432/client_db"
    http_port: int = 8005
    grpc_port: int = 9005

    booking_addr: str = "localhost:9003"


@lru_cache
def get_settings() -> Settings:
    return Settings()
