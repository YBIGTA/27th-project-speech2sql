"""
Project settings and configuration management
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Database Configuration
    database_type: str = Field(default="postgresql", env="DATABASE_TYPE")
    postgresql_host: str = Field(default="localhost", env="POSTGRESQL_HOST")
    postgresql_port: int = Field(default=5432, env="POSTGRESQL_PORT")
    postgresql_user: str = Field(default="postgres", env="POSTGRESQL_USER")
    postgresql_password: str = Field(default="password", env="POSTGRESQL_PASSWORD")
    postgresql_database: str = Field(default="speech2sql", env="POSTGRESQL_DATABASE")
    postgresql_url: str = Field(default="postgresql://postgres:password@localhost:5432/speech2sql", env="POSTGRESQL_URL")
    
    # API Keys
    upstage_api_key: Optional[str] = Field(default=None, env="UPSTAGE_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    upstage_base_url: Optional[str] = Field(default="https://api.upstage.ai/v1", env="UPSTAGE_BASE_URL")
    
    # Elasticsearch Configuration
    elasticsearch_url: str = Field(default="http://localhost:9200", env="ELASTICSEARCH_URL")
    elasticsearch_username: Optional[str] = Field(default=None, env="ELASTICSEARCH_USERNAME")
    elasticsearch_password: Optional[str] = Field(default=None, env="ELASTICSEARCH_PASSWORD")
    
    # Model Configuration
    whisper_model: str = Field(default="base", env="WHISPER_MODEL")
    summarization_model: str = Field(default="pegasus-large", env="SUMMARIZATION_MODEL")
    text2sql_model: str = Field(default="text2sql-large", env="TEXT2SQL_MODEL")
    
    # Audio Processing
    audio_upload_path: str = Field(default="./data/raw", env="AUDIO_UPLOAD_PATH")
    processed_audio_path: str = Field(default="./data/processed", env="PROCESSED_AUDIO_PATH")
    max_audio_size: str = Field(default="100MB", env="MAX_AUDIO_SIZE")
    supported_formats: str = Field(default="wav,mp3,m4a", env="SUPPORTED_FORMATS")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # File Storage
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    temp_dir: str = Field(default="./temp", env="TEMP_DIR")
    model_cache_dir: str = Field(default="./data/models", env="MODEL_CACHE_DIR")
    
    # Security
    secret_key: str = Field(default="your_secret_key_here", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def supported_audio_formats(self) -> list[str]:
        """Get list of supported audio formats"""
        return [fmt.strip() for fmt in self.supported_formats.split(",")]
    
    @property
    def max_audio_size_bytes(self) -> int:
        """Convert max audio size string to bytes"""
        size_str = self.max_audio_size.upper()
        if size_str.endswith("MB"):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith("GB"):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings 