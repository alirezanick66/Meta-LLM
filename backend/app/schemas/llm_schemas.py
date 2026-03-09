from typing import Optional, List
from dataclasses import dataclass, field

from backend.app.schemas.base_schemas import FinishReason, LLMProvider, QueryIntent
# ==================== Layer 1: Prompt ====================


@dataclass( slots=True, frozen=True )
class LLMUsage:
    """‫اطلاعات مصرف توکن — لایه داخلی"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass( slots=True, frozen=True )
class SourceInfo:
    """‫اطلاعات منبع استفاده شده — نسخه داخلی"""
    index: int
    chunk_id: Optional[ str ]
    source: str
    hierarchy: str
    content: str


@dataclass( slots=True, frozen=True )
class PromptResult:
    """‫نتیجه ساخت پرامپت توسط PromptBuilder"""
    system_prompt: str
    user_prompt: str
    sources_used: List[ SourceInfo ]
    total_tokens: int
    intent: QueryIntent


# ==================== Layer 2: Provider Raw Response ====================


@dataclass( slots=True, frozen=True )
class ProviderLLMResponse:
    """‫پاسخ خام از Provider (Gemini/Groq)"""
    success: bool
    content: Optional[ str ]
    model: str
    usage: LLMUsage
    error: Optional[ str ] = None
    finish_reason: Optional[ FinishReason ] = None

    @classmethod
    def create_error(
        cls,
        msg: str,
        model: str,
        finish_reason: FinishReason = FinishReason.ERROR,
    ) -> "ProviderLLMResponse":
        """‫factory method برای ساخت error response"""
        return cls(
            success=False,
            content=None,
            model=model,
            usage=LLMUsage(),
            error=msg,
            finish_reason=finish_reason,
        )


# ==================== Layer 3: Application Response ====================


@dataclass( slots=True, frozen=True )
class LLMResponse:
    """‫پاسخ نهایی application به consumer"""
    success: bool
    answer: Optional[ str ] = None
    provider: Optional[ LLMProvider ] = None
    model: Optional[ str ] = None
    usage: LLMUsage = field( default_factory=LLMUsage )
    sources: List[ SourceInfo ] = field( default_factory=list )
    prompt_tokens: int = 0
    intent: QueryIntent = QueryIntent.RAG
    error: Optional[ str ] = None
    finish_reason: Optional[ FinishReason ] = None

    @classmethod
    def from_provider_response(
        cls,
        response: ProviderLLMResponse,
        prompt_result: PromptResult,
        provider_name: LLMProvider,
    ) -> "LLMResponse":
        """‫تبدیل Provider response به Application response"""
        if not response.success:
            return cls(
                success=False,
                error=response.error,
                provider=provider_name,
                model=response.model,
                prompt_tokens=prompt_result.total_tokens,
                intent=prompt_result.intent,
            )

        sources = [
            SourceInfo(
                index=s.index,
                chunk_id=s.chunk_id,
                source=s.source,
                hierarchy=s.hierarchy,
                content=s.content,
            ) for s in prompt_result.sources_used
        ]

        return cls(
            success=True,
            answer=response.content,
            provider=provider_name,
            model=response.model,
            usage=response.usage,
            sources=sources,
            prompt_tokens=prompt_result.total_tokens,
            intent=prompt_result.intent,
            finish_reason=response.finish_reason,
        )
