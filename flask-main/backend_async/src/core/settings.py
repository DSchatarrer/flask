"""Settings cacheables; jamás cachear Session, conexiones o datos de usuario."""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", env_ignore_empty=True)

    FLASK_SECRET_KEY: str = Field(min_length=16)
    JWT_SECRET_KEY: str = Field(min_length=16)
    ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    TOKEN_SECONDS_EXP: int = Field(default=3600, gt=0)
    API_KEY: str = Field(min_length=1)
    COOKIE_SECURE: bool = True
    FLASK_DEBUG: bool = False
    FLASK_RUN_HOST: str = "127.0.0.1"
    FLASK_RUN_PORT: int = 5000
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    DATABASE_URL: str | None = None
    DATASOURCE_DB: str | None = None
    DATASOURCE_PORT: int = 5432
    DATASOURCE_FQDN: str | None = None
    DATASOURCE_USR: str | None = None
    DATASOURCE_PWD: str | None = None
    BACKEND_CORS_ORIGINS: list[str] = Field(default_factory=list)

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.DATABASE_URL:
            url = make_url(self.DATABASE_URL)
            if url.drivername in {"sqlite", "sqlite+pysqlite"}:
                url = url.set(drivername="sqlite+aiosqlite")
            elif url.drivername in {"postgresql", "postgresql+psycopg2", "postgresql+psycopg"}:
                url = url.set(drivername="postgresql+asyncpg")
            elif url.drivername not in {"sqlite+aiosqlite", "postgresql+asyncpg"}:
                raise ValueError(f"Driver asíncrono no soportado: {url.drivername}")
            return url.render_as_string(hide_password=False)
        if not all((self.DATASOURCE_DB, self.DATASOURCE_FQDN, self.DATASOURCE_USR, self.DATASOURCE_PWD)):
            raise ValueError("Configura DATABASE_URL o DATASOURCE_DB/FQDN/USR/PWD")
        return URL.create(
            "postgresql+asyncpg", username=self.DATASOURCE_USR, password=self.DATASOURCE_PWD,
            host=self.DATASOURCE_FQDN, port=self.DATASOURCE_PORT, database=self.DATASOURCE_DB,
        ).render_as_string(hide_password=False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
