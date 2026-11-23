from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeepSeekSettings(BaseModel):
    api_key: SecretStr = Field(..., description="Deepseek API")
    max_connections: int = 5


class MinioSettings(BaseModel):
    endpoint: str = Field(..., description="Minio endpoint")
    access_key: SecretStr = Field(..., description="Minio access key")
    secret_key: SecretStr = Field(..., description="Minio secret key")
    region_name: str = Field(..., description="Minio region")


class UnsplashSettings(BaseModel):
    api_key: SecretStr = Field(..., description="Unsplash API")
    max_connections: int = 5
    timeout: int = 20


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )
    debug: bool = False
    deepseek: DeepSeekSettings
    unsplash: UnsplashSettings
    minio: MinioSettings
