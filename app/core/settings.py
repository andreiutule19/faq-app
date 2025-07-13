import os
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    api_secret_key: str = os.getenv("API_SECRET_KEY", "your-secret-key-here")
    api_port: int = int(os.getenv("API_PORT", "8000"))

    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/semantic_faq")
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "password")
    postgres_db: str = os.getenv("POSTGRES_DB", "semantic_faq")
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "20"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    allowed_hosts: str = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
    
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.8"))
    openai_max_tokens: int = int(os.getenv("OPENAI_MAX_TOKENS", "150"))
    openai_temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    

    cache_ttl: int = int(os.getenv("CACHE_TTL", "3600"))
    max_query_length: int = int(os.getenv("MAX_QUERY_LENGTH", "1000"))
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"  
    )

settings = Settings()