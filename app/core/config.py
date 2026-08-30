from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    PROJECT_NAME: str = "UAV Telemetry & Analytics System"
    API_V1_STR: str = "/api/v1"

    MYSQL_SERVER: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DB: str = "uav_telemetry_db"

    @property
    def ASYNC_DATABASE_URI(self) -> str:
        """
        SQLAlchemy URL.create ile sıfır hatalı asenkron URI üretici.
        """
        return URL.create(
            drivername="mysql+aiomysql",
            username=self.MYSQL_USER,
            password=self.MYSQL_PASSWORD if self.MYSQL_PASSWORD else None,
            host=self.MYSQL_SERVER,
            port=self.MYSQL_PORT,
            database=self.MYSQL_DB
        ).render_as_string(hide_password=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()