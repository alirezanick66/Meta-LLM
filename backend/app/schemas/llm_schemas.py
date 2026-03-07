from typing import Optional, Dict, List, Any, Literal
from dataclasses import dataclass, field

# ==================== Layer 1: Prompt ====================


@dataclass( slots=True, frozen=True )
class PromptResult:
    """‫نتیجه ساخت پرامپت توسط PromptBuilder"""
    system_prompt: str
    user_prompt: str
    sources_used: List[ Dict[ str, Any ] ]
    total_tokens: int
    is_system_question: bool


# ==================== Layer 2: Provider Raw Response ====================


@dataclass( slots=True, frozen=True )
class ProviderLLMResponse:
    """‫پاسخ خام از Provider (Gemini/Groq)"""
    success: bool
    content: Optional[ str ]
    model: str
    usage: Dict[ str, int ]
    error: Optional[ str ] = None
    finish_reason: Optional[ str ] = None


# ==================== Layer 3: Application Response ====================


@dataclass( slots=True, frozen=True )
class SourceInfo:
    """‫اطلاعات منبع استفاده شده — نسخه داخلی"""
    index: int
    chunk_id: Optional[ str ]
    source: str
    hierarchy: str
    content: str


@dataclass( slots=True, frozen=True )
class LLMResponse:
    """‫پاسخ نهایی application به consumer"""
    success: bool
    answer: Optional[ str ] = None
    provider: Optional[ Literal[ "groq", "gemini" ] ] = None
    model: Optional[ str ] = None
    usage: Dict[ str, int ] = field( default_factory=dict )
    sources: List[ SourceInfo ] = field( default_factory=list )
    prompt_tokens: int = 0
    is_system_question: bool = False
    error: Optional[ str ] = None
    finish_reason: Optional[ str ] = None

    @classmethod
    def from_provider_response(
        cls,
        response: ProviderLLMResponse,
        prompt_result: PromptResult,
        provider_name: Literal[ "groq", "gemini" ],
    ) -> "LLMResponse":
        """‫تبدیل Provider response به Application response"""
        if not response.success:
            return cls(
                success=False,
                error=response.error,
                provider=provider_name,
                model=response.model,
                prompt_tokens=prompt_result.total_tokens,
                is_system_question=prompt_result.is_system_question,
            )

        sources = [
            SourceInfo(
                index=s.get( "index", 0 ),
                chunk_id=s.get( "chunk_id" ),
                source=s.get( "source", "Unknown" ),
                hierarchy=s.get( "hierarchy", "" ),
                content=s.get( "content", "" ),
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
            is_system_question=prompt_result.is_system_question,
            finish_reason=response.finish_reason,
        )
