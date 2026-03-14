from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings( BaseSettings ):
    """برای تنظیمات فایل پیکربندی برنامه استفاده می‌شود."""

    model_config = SettingsConfigDict( env_file=".env", env_file_encoding="utf-8", case_sensitive=False )

    # ==================== API Keys ====================
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # ==================== Document Corpus ====================
    DOCUMENTS_DIR: str = "corpus"

    # ==================== PostgreSQL ====================
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "meta_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_ECHO: bool = False

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
    EMBEDDING_MODEL: str = "Alibaba-NLP/gte-multilingual-base"
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    EMBEDDING_DEVICE: Literal[ "cpu", "cuda" ] = "cpu"
    EMBEDDING_BATCH_SIZE: int = 32
    EMBEDDING_MODEL_TOKEN: str = ""
    EMBEDDING_MODEL_PATH: str = ""
    RERANKER_MODEL_PATH: str = ""          # ‫مسیر local مدل reranker
    EMBEDDING_VECTOR_DIM: int = 768
    EMBEDDING_CPU_THREADS: int = 16          #تعداد ترد های CPU برای پردازش embedding

    # ==================== Chunking ====================
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 128

    # ==================== Retrieval ====================
    BM25_TOP_K: int = 20
    VECTOR_TOP_K: int = 20
    RERANKER_TOP_K: int = 5          # ‫تعداد نتایج نهایی بعد از reranker
    RRF_TOP_K: int = 20          # ‫تعداد نتایج بعد از RRF قبل از reranker
    BM25_CACHE_DIR: str = "backend/data/storage/bm25_cache"
    # ==================== FastAPI ====================
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    API_RELOAD: bool = False

    # ====================LLM Settings====================
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_MODEL: str = "gemini-2.5-flash"

    LLM_PRIMARY: str = "groq"
    LLM_FALLBACK: str = "gemini"

    TEMPERATURE: float = 0.3          #میزان خلاقیت پاسخ‌ها از 0 تا 2
    MAX_TOKENS: int = 2048          # ‫حداکثر توکن پاسخ LLM
    LLM_TIMEOUT: int = 30

    #==================== Intent Detection ====================
    DOMAIN_TOPIC: str = "انقلاب اسلامی ایران"
    DOMAIN_DESCRIPTION: str = ( "سوالات مرتبط با تاریخ، وقایع، شخصیت‌ها و "
                                "مفاهیم انقلاب اسلامی ایران" )
    OUT_OF_SCOPE_MESSAGE: str = ( "متأسفانه این سوال در حوزه تخصصی من نیست. "
                                  "من فقط می‌توانم سوالات مرتبط با "
                                  "انقلاب اسلامی ایران را پاسخ دهم." )
    CONVERSATIONAL_MESSAGE: str = ( "سلام! چطور می‌تونم کمکتون کنم؟ "
                                    "هر سوالی در مورد انقلاب اسلامی ایران دارید بپرسید." )

    #===================== Prompt Settings ====================
    MAX_CONTEXT_TOKENS: int = 3000          # ‫حداکثر توکن context در پرامپت
    DEFAULT_SYSTEM_PROMPT: str = """تو یک دستیار هوشمند متخصص در زمینه انقلاب اسلامی ایران هستی.

    وظایف:
    1. پاسخ دقیق بر اساس context.
    2. زبان فارسی رسمی و روان.
    3. ذکر منابع در صورت امکان.
    4. اگر جواب در context نیست، صادقانه بگو.

    محدودیت‌ها:
    - حداکثر 3-4 پاراگراف.
    - صرفاً زبان فارسی.
    """


settings = Settings()
