from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime

from backend.app.schemas.api_schemas import UsageInfo
from backend.app.schemas.base_schemas import LLMProvider


# ==================== Request  ====================
class ChatRequest( BaseModel ):
    """درخواست چت از کاربر"""
    query: str = Field(..., min_length=1, max_length=1000, description="سوال کاربر" )
    temperature: Optional[ float ] = Field( None, ge=0.0, le=2.0, description="میزان خلاقیت پاسخ (0-2)" )

    @field_validator( 'query' )
    @classmethod
    def validate_query( cls, v: str ) -> str:
        """ ‫اعتبارسنجی query"""
        if not v or not v.strip():
            raise ValueError( "سوال نمی‌تواند خالی باشد" )
        return v.strip()

    model_config = ConfigDict(
        json_schema_extra={ "example": {
            "query": "انقلاب اسلامی چه تأثیری بر نظریه‌های غربی گذاشت؟",
            "temperature": 0.3
        } } )


# ==================== Response ====================
class Source( BaseModel ):
    """اطلاعات یک منبع"""
    index: int = Field(..., description="شماره منبع" )
    chunk_id: str = Field(..., description="شناسه chunk" )
    source: str = Field(..., description="نام فایل منبع" )
    hierarchy: str = Field(..., description="سلسله مراتب heading" )
    content: Optional[ str ] = Field( None, description="متن chunk" )


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
    sources: list[ Source ] = Field( default_factory=list, description="منابع استفاده شده" )
    metadata: Optional[ ChatMetadata ] = Field( None, description="اطلاعات تکمیلی" )
    error: Optional[ str ] = Field( None, description="پیغام خطا (در صورت وجود)" )
    timestamp: datetime = Field( default_factory=datetime.now, description="زمان پاسخ" )

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
