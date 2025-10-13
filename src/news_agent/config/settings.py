from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App info
    APP_NAME: str = Field("Trend-News-Notifier", env="APP_NAME")
    DEBUG: bool = Field(False, env="DEBUG")

    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # AWS credentials & region
    AWS_ACCESS_KEY_ID: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(None, env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: Optional[str] = Field("us-east-1", env="AWS_REGION")

    # S3
    S3_BUCKET_NAME: Optional[str] = Field(None, env="S3_BUCKET_NAME")

    # Presigned URL expiration (in seconds)
    PRESIGNED_URL_EXPIRATION: int = Field(
        3600, description="Expiration time for presigned URLs in seconds"
    )

    # Optional notification settings
    NOTIFY_EMAIL_FROM: Optional[str] = Field(None, env="NOTIFY_EMAIL_FROM")
    SMTP_SERVER: Optional[str] = Field(None, env="SMTP_SERVER")
    SMTP_USER: Optional[str] = Field(None, env="SMTP_USER")
    SMTP_PASS: Optional[str] = Field(None, env="SMTP_PASS")
    SMTP_PORT: int = Field(587, env="SMTP_PORT")
    RECIPIENT_EMAILS: Optional[str] = Field(None, env="RECIPIENT_EMAILS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# instantiate singleton
settings = Settings()
