from enum import Enum


# ==================== Enums ====================
class LLMProvider( str, Enum ):
    GROQ = "groq"
    GEMINI = "gemini"


class HealthStatus( str, Enum ):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
