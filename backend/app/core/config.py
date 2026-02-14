from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings( BaseSettings ):
    """برای تنظیمات فایل پیکربندی برنامه استفاده می‌شود."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    # ==================== API Keys ====================
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # ==================== PostgreSQL ====================
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "meta_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"

    @property
    def postgres_url( self ) -> str:
        """اتصال به پایگاه داده PostgreSQL"""
        return ( f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                 f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}" )

    # ==================== Qdrant ====================
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "meta_documents"

    # ==================== Redis ====================
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_CACHE_TTL: int = 3600

    # ==================== Embedding Models ====================
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    EMBEDDING_DEVICE: Literal[ "cpu", "cuda" ] = "cpu"
    EMBEDDING_BATCH_SIZE: int = 32
    EMBEDDING_MODEL_TOKEN: str = "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"
    EMBEDDING_MODEL_PATH: str = "E:/A-Golchin program/Ai/Models/BAAIbge-m3"
    EMBEDDING_VECTOR_DIM: int = 1024
    CPU_THREADS: int = 4          #تعداد ترد های CPU برای پردازش embedding

    # ==================== Chunking ====================
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 128

    # ==================== Retrieval ====================
    BM25_TOP_K: int = 20
    VECTOR_TOP_K: int = 20
    RERANKER_TOP_K: int = 5

    # ==================== FastAPI ====================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # ====================LLM Settings====================
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_MODEL: str = "gemini-2.5-flash"

    LLM_PRIMARY: str = "groq"
    LLM_FALLBACK: str = "gemini"

    TEMPERATURE: float = 0.3          #میزان خلاقیت پاسخ‌ها از 0 تا 2
    MAX_TOKENS: int = 2048
    LLM_TIMEOUT: int = 5
    LLM_MAX_RETRIES: int = 3


settings = Settings()
