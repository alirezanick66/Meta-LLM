from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from backend.app.services.llm.groq_client import GroqClient, create_groq_client
from backend.app.services.llm.gemini_client import GeminiClient, create_gemini_client
from backend.app.services.llm.prompt_builder import PromptBuilder, create_prompt_builder, PromptResult
from backend.app.utils.logging_config import log_message, LG, LogLevel


@dataclass( slots=True, frozen=True )
class LLMResponse:
    success: bool
    answer: Optional[ str ] = None
    provider: Optional[ str ] = None
    model: Optional[ str ] = None
    usage: Dict[ str, int ] = field( default_factory=dict )
    sources: List[ Dict[ str, Any ] ] = field( default_factory=list )
    prompt_tokens: int = 0
    is_system_question: bool = False
    error: Optional[ str ] = None


class LLMOrchestrator:
    """ ‫مدیریت هوشمند LLM با قابلیت Fallback خودکار"""

    def __init__( self,
                  groq_client: GroqClient,
                  gemini_client: GeminiClient,
                  prompt_builder: PromptBuilder,
                  use_fallback: bool = True ):
        self.clients = { "groq": groq_client, "gemini": gemini_client }
        self.prompt_builder = prompt_builder
        self.use_fallback = use_fallback

    def _execute_chat( self, provider: str, prompt: PromptResult, temp: Optional[ float ] ) -> Dict[ str, Any ]:
        """ ‫اجرای تماس با API به صورت متمرکز"""
        messages = [ { "role": "system", "content": prompt.system_prompt }, { "role": "user", "content": prompt.user_prompt } ]
        try:
            return self.clients[ provider ].chat( messages=messages, temperature=temp )
        except Exception as e:
            return { "success": False, "error": str( e ) }

    def generate_answer( self,
                         query: str,
                         chunks: List[ Dict ],
                         temperature: Optional[ float ] = None,
                         include_metadata: bool = True ) -> LLMResponse:

        log_message( LG.LLM, f"🤖 Request: {query[:50]}...", LogLevel.INFO )

        prompt = self.prompt_builder.build_prompt( query, chunks, include_metadata )

        # ‫1. تلاش اول: Groq
        res = self._execute_chat( "groq", prompt, temperature )
        current_provider = "groq"

        # ‫2. تلاش دوم (Fallback): Gemini
        if not res[ "success" ] and self.use_fallback:
            log_message( LG.LLM, f"⚠️ Groq failed ({res.get('error')}), trying Gemini...", LogLevel.WARNING )

            # ‫تلاش با Gemini
            res = self._execute_chat( "gemini", prompt, temperature )
            current_provider = "gemini"

            #‫ اگر Gemini هم خطا داد
            if not res[ "success" ]:
                log_message( LG.LLM, f"❌ Gemini also failed: {res.get('error')}", LogLevel.ERROR )

        # ‫ساخت پاسخ نهایی (بدون تغییر دادن دیکشنری res)
        return self._wrap_response( res, current_provider, prompt )

    def _wrap_response( self, res: Dict, provider_name: str, prompt: PromptResult ) -> LLMResponse:
        """ ‫تبدیل دیکشنری خروجی به شیء استاندارد LLMResponse."""
        if not res.get( "success" ):
            return LLMResponse( success=False,
                                error=res.get( "error" ),
                                prompt_tokens=prompt.total_tokens,
                                is_system_question=prompt.is_system_question )

        return LLMResponse(
            success=True,
            answer=res.get( "content" ),
            provider=provider_name,          # استفاده از پارامتر ورودی
            model=res.get( "model" ),
            usage=res.get( "usage", {} ),
            sources=prompt.sources_used,
            prompt_tokens=prompt.total_tokens,
            is_system_question=prompt.is_system_question )


# ==================== Factory Function ====================
def create_llm_orchestrator( max_context_tokens: int = 3000, use_fallback: bool = True ) -> LLMOrchestrator:
    return LLMOrchestrator(
        groq_client=create_groq_client(),
        gemini_client=create_gemini_client(),
        prompt_builder=create_prompt_builder( include_sources=True, max_context_tokens=max_context_tokens ),
        use_fallback=use_fallback,
    )
