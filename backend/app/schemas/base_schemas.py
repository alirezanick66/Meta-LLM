from enum import Enum, StrEnum


# ==================== Enums ====================
class LLMProvider( str, Enum ):
    GROQ = "groq"
    GEMINI = "gemini"


class HealthStatus( str, Enum ):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class FinishReason( str, Enum ):
    STOP = "STOP"
    ERROR = "ERROR"
    SAFETY = "SAFETY"
    MAX_TOKENS = "MAX_TOKENS"
    INVALID_STRUCTURE = "INVALID_STRUCTURE"
    UNKNOWN = "UNKNOWN"


class QueryIntent( StrEnum ):
    """‫نوع intent تشخیص داده‌شده برای هر query"""
    RAG = "rag"          # ‫جستجو در اسناد
    OUT_OF_SCOPE = "out_of_scope"          # ‫خارج از حوزه — رد کن
    CONVERSATIONAL = "conversational"          # ‫احوال‌پرسی — پیام ثابت
