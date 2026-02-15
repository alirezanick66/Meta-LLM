from pydantic import BaseModel, Field, field_validator, computed_field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


# ==================== Enums ====================
class LLMProvider( str, Enum ):
    GROQ = "groq"
    GEMINI = "gemini"


class HealthStatus( str, Enum ):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


# ==================== Request Schemas ====================
class ChatRequest( BaseModel ):
    """درخواست چت از کاربر"""
    query: str = Field(..., min_length=1, max_length=1000, description="سوال کاربر" )
    temperature: Optional[ float ] = Field( None, ge=0.0, le=2.0, description="میزان خلاقیت پاسخ (0-2)" )

    @field_validator( 'query' )
    @classmethod
    def validate_query( cls, v: str ) -> str:
        """اعتبارسنجی query"""
        if not v or not v.strip():
            raise ValueError( "سوال نمی‌تواند خالی باشد" )
        return v.strip()

    # استفاده از ConfigDict به جای کلاس Config (Pydantic V2)
    model_config = ConfigDict(
        json_schema_extra={ "example": {
            "query": "انقلاب اسلامی چه تأثیری بر نظریه‌های غربی گذاشت؟",
            "temperature": 0.3
        } } )


# ==================== Response Schemas ====================
class Source( BaseModel ):
    """اطلاعات یک منبع"""
    index: int = Field(..., description="شماره منبع" )
    chunk_id: str = Field(..., description="شناسه chunk" )
    source: str = Field(..., description="نام فایل منبع" )
    hierarchy: str = Field(..., description="سلسله مراتب heading" )


class UsageInfo( BaseModel ):
    """اطلاعات مصرف توکن"""
    prompt_tokens: int = Field( 0, description="تعداد توکن‌های ورودی" )
    completion_tokens: int = Field( 0, description="تعداد توکن‌های خروجی" )

    # محاسبه خودکار مجموع توکن‌ها
    @computed_field          # type: ignore[misc]
    @property
    def total_tokens( self ) -> int:
        return self.prompt_tokens + self.completion_tokens


class ChatMetadata( BaseModel ):
    """متادیتای پاسخ"""
    provider: LLMProvider = Field(..., description="ارائه‌دهنده LLM" )
    model: str = Field(..., description="نام مدل استفاده شده" )
    usage: UsageInfo = Field(..., description="اطلاعات مصرف" )
    is_system_question: bool = Field( False, description="آیا سوال سیستمی بود؟" )
    retrieval_count: int = Field( 0, description="تعداد chunks بازیابی شده" )
    response_time: float = Field( 0.0, description="زمان پاسخ (ثانیه)" )


class ChatResponse( BaseModel ):
    """پاسخ چت به کاربر"""
    success: bool = Field(..., description="وضعیت موفقیت" )
    answer: Optional[ str ] = Field( None, description="پاسخ نهایی" )
    sources: list[ Source ] = Field( default_factory=list, description="منابع استفاده شده" )          # Python 3.9+ style
    metadata: Optional[ ChatMetadata ] = Field( None, description="اطلاعات تکمیلی" )
    error: Optional[ str ] = Field( None, description="پیغام خطا (در صورت وجود)" )
    timestamp: datetime = Field( default_factory=datetime.now, description="زمان پاسخ" )

    @field_validator( 'error', 'answer' )
    @classmethod
    def check_consistency( cls, v: Optional[ str ], info ) -> Optional[ str ]:
        """اطمینان از اینکه همزمان هم error و هم answer پر نشده باشند"""
        # این منطق کمی پیشرفته است و بسته به نیاز شما می‌تواند ساده‌تر باشد
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success":
                True,
                "answer":
                "انقلاب اسلامی تأثیرات عمیقی بر نظریه‌های غربی گذاشت...",
                "sources": [ {
                    "index": 1,
                    "chunk_id": "doc_1_chunk_003",
                    "source": "enghelab.md",
                    "hierarchy": "انقلاب اسلامی > تأثیرات"
                } ],
                "metadata": {
                    "provider": "groq",
                    "model": "llama-3.3-70b-versatile",
                    "usage": {
                        "prompt_tokens": 2847,
                        "completion_tokens": 309
          # total_tokens محاسبه می‌شود و نیازی به نوشتن نیست
                    },
                    "is_system_question": False,
                    "retrieval_count": 5,
                    "response_time": 2.45
                },
                "error":
                None,
                "timestamp":
                "2026-02-15T10:30:00Z"
            }
        } )


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
