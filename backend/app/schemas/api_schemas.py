from pydantic import BaseModel, Field, computed_field, ConfigDict
from typing import Optional
from datetime import datetime

from backend.app.schemas.base_schemas import HealthStatus


# ==================== Usage Schema ====================
class UsageInfo( BaseModel ):
    """اطلاعات مصرف توکن"""
    prompt_tokens: int = Field( 0, description="تعداد توکن‌های ورودی" )
    completion_tokens: int = Field( 0, description="تعداد توکن‌های خروجی" )

    # محاسبه خودکار مجموع توکن‌ها
    @computed_field
    @property
    def total_tokens( self ) -> int:
        return self.prompt_tokens + self.completion_tokens


# ==================== Health Check Schema ====================
class HealthResponse( BaseModel ):
    """پاسخ health check"""
    status: HealthStatus = Field(..., description="وضعیت کلی" )
    service: str = Field( "Meta API", description="نام سرویس" )
    postgres: str = Field(..., description="وضعیت PostgreSQL" )
    qdrant: str = Field(..., description="وضعیت Qdrant" )
    qdrant_vectors: int = Field( 0, description="تعداد vectors در Qdrant" )
    redis: Optional[ str ] = Field( None, description="وضعیت Redis (فاز 7)" )
    timestamp: datetime = Field( default_factory=datetime.now, description="زمان بررسی" )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "service": "Meta API",
                "postgres": "connected",
                "qdrant": "connected",
                "qdrant_vectors": 68,
                "redis": None,
                "timestamp": "2026-02-15T10:30:00Z"
            }
        } )


# ==================== Stats Schema ====================
class SystemStats( BaseModel ):
    """آمار سیستم"""
    total_documents: int = Field( 0, description="تعداد اسناد" )
    total_chunks: int = Field( 0, description="تعداد chunks" )
    qdrant_vectors: int = Field( 0, description="تعداد vectors" )
    bm25_chunks: int = Field( 0, description="تعداد chunks در BM25" )
    embedding_model: str = Field(..., description="مدل embedding" )
    llm_primary: str = Field(..., description="مدل اصلی LLM" )
    timestamp: datetime = Field( default_factory=datetime.now )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_documents": 1,
                "total_chunks": 68,
                "qdrant_vectors": 68,
                "bm25_chunks": 68,
                "embedding_model": "BAAI/bge-m3",
                "llm_primary": "llama-3.3-70b-versatile",
                "timestamp": "2026-02-15T10:30:00Z"
            }
        } )
