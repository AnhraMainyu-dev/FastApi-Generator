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
    bucket: str = Field(..., description="Minio bucket")
    timeout: int = Field(..., description="Minio timeout")
    reading_timeout: int = Field(..., description="Minio reading timeout")
    max_connections: int = Field(..., description="Minio max connections")


class UnsplashSettings(BaseModel):
    api_key: SecretStr = Field(..., description="Unsplash API")
    max_connections: int = 5
    timeout: int = 20


class GotenbergSettings(BaseModel):
    base_url: str = Field(..., description="Gotenberg API")
    screenshot_width: int = Field(..., description="Gotenberg screenshot width")
    screenshot_format: str = Field(..., description="Gotenberg screenshot format")
    wait_delay: int = Field(..., description="Gotenberg wait delay")
    max_connections: int = Field(..., description="Gotenberg max connections")
    timeout: int = Field(..., description="Gotenberg timeout")
    animation_timeout: int = Field(..., description="Gotenberg animation timeout")


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
    gotenberg: GotenbergSettings
