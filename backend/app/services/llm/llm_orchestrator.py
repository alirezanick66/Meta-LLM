from typing import Optional, List, Dict, Literal

from backend.app.schemas.base_schemas import FinishReason, LLMProvider
from backend.app.services.llm.groq_client import GroqClient, create_groq_client
from backend.app.services.llm.gemini_client import GeminiClient, create_gemini_client
from backend.app.services.llm.prompt_builder import PromptBuilder, create_prompt_builder
from backend.app.schemas.llm_schemas import LLMResponse, PromptResult, ProviderLLMResponse
from backend.app.utils.logging_config import log_message, LG, LogLevel


class LLMOrchestrator:
    """‫ مدیریت هوشمند LLM با قابلیت Fallback خودکار"""

    def __init__( self,
                  groq_client: GroqClient,
                  gemini_client: GeminiClient,
                  prompt_builder: PromptBuilder,
                  use_fallback: bool = True ):
        self.clients = { "groq": groq_client, "gemini": gemini_client }
        self.prompt_builder = prompt_builder
        self.use_fallback = use_fallback

    def _execute_chat( self, provider: str, prompt: PromptResult, temp: Optional[ float ] ) -> ProviderLLMResponse:
        """‫ اجرای تماس با API به صورت متمرکز"""
        messages = [ { "role": "system", "content": prompt.system_prompt }, { "role": "user", "content": prompt.user_prompt } ]
        try:
            return self.clients[ provider ].chat( messages=messages, temperature=temp )
        except Exception as e:
            return ProviderLLMResponse.create_error( str( e ), provider, FinishReason.ERROR )

    def generate_answer(
        self,
        query: str,
        chunks: List[ Dict ],
        temperature: Optional[ float ] = None,
        include_metadata: bool = True,
    ) -> LLMResponse:
        """‫مدیریت کامل فرآیند تولید پاسخ با fallback خودکار"""
        log_message( LG.LLM, f"🤖 Request: {query[:50]}...", LogLevel.INFO )

        prompt = self.prompt_builder.build_prompt( query, chunks, include_metadata )

        # ‫1. تلاش اول: Groq
        res = self._execute_chat( "groq", prompt, temperature )
        current_provider: LLMProvider = LLMProvider.GROQ

        # ‫2. تلاش دوم (Fallback): Gemini
        if not res.success and self.use_fallback:
            log_message( LG.LLM, f"⚠️ Groq failed ({res.error}), trying Gemini...", LogLevel.WARNING )
            res = self._execute_chat( "gemini", prompt, temperature )
            current_provider = LLMProvider.GEMINI

            if not res.success:
                log_message( LG.LLM, f"❌ Gemini also failed: {res.error}", LogLevel.ERROR )

        return LLMResponse.from_provider_response( res, prompt, current_provider )


# ==================== Factory Function ====================
def create_llm_orchestrator( tokenizer_service, use_fallback: bool = True ) -> LLMOrchestrator:
    return LLMOrchestrator(
        groq_client=create_groq_client(),
        gemini_client=create_gemini_client(),
        prompt_builder=create_prompt_builder(
            tokenizer_service=tokenizer_service,
            include_sources=True,
        ),
        use_fallback=use_fallback,
    )
