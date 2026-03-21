from typing import Optional, List, Dict

from backend.app.schemas.base_schemas import FinishReason, LLMProvider, QueryIntent
from backend.app.services.llm.groq_client import GroqClient, create_groq_client
from backend.app.services.llm.gemini_client import GeminiClient, create_gemini_client
from backend.app.services.llm.prompt_builder import PromptBuilder, create_prompt_builder
from backend.app.schemas.llm_schemas import LLMResponse, PromptResult, ProviderLLMResponse
from backend.app.services.llm.intent_detector import IntentDetector, create_intent_detector
from backend.app.utils.logging_config import log_message, LG, LogLevel


class LLMOrchestrator:
    """
        ‫مدیریت هوشمند LLM با Intent Detection و Fallback خودکار

        ‫جریان کار:
        ‫1. IntentDetector تشخیص میده query از چه نوعیه
        ‫2. بر اساس intent، routing انجام میشه:
        ‫   - RAG: chunks به PromptBuilder داده میشه
        ‫   - غیر RAG: PromptBuilder بدون chunks کار میکنه
        ‫3. LLM call با Groq (primary) و Gemini (fallback)
        """

    def __init__( self,
                  groq_client: GroqClient,
                  gemini_client: GeminiClient,
                  prompt_builder: PromptBuilder,
                  intent_detector: IntentDetector,
                  use_fallback: bool = True ):
        self.clients = { "groq": groq_client, "gemini": gemini_client }
        self.prompt_builder = prompt_builder
        self.intent_detector = intent_detector
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
        intent: QueryIntent,
        temperature: Optional[ float ] = None,
        include_metadata: bool = True,
    ) -> LLMResponse:
        """
        ‫مدیریت کامل فرآیند تولید پاسخ

        Args:
            query: سوال کاربر
            chunks: ‫نتایج retrieval (برای RAG — میتونه خالی باشه)
            temperature: ‫میزان خلاقیت پاسخ
            include_metadata: ‫نمایش hierarchy در پرامپت
            intent: ‫نوع سوال

        Returns:
            LLMResponse با intent مشخص
        """

        log_message( LG.LLM, f"🤖 Request: {query[:50]}...", LogLevel.INFO )

        # ‫مرحله ۱: تشخیص intent
        # intent = self.intent_detector.detect( query )
        # ‫مرحله ۲: ساخت پرامپت بر اساس intent
        # ‫برای RAG — chunks پاس داده میشه
        # ‫برای غیر RAG — chunks خالیه (PromptBuilder نادیده میگیره)

        prompt = self.prompt_builder.build_prompt(
            query=query,
            chunks=chunks if intent == QueryIntent.RAG else [],
            intent=intent,
            include_metadata=include_metadata,
        )

        # ‫مرحله ۳: LLM call — Groq اول، Gemini fallback
        res = self._execute_chat( "groq", prompt, temperature )
        current_provider: LLMProvider = LLMProvider.GROQ

        if not res.success and self.use_fallback:
            log_message( LG.LLM, f"⚠️ Groq failed ({res.error}), trying Gemini...", LogLevel.WARNING )
            res = self._execute_chat( "gemini", prompt, temperature )
            current_provider = LLMProvider.GEMINI

            if not res.success:
                log_message( LG.LLM, f"❌ Gemini also failed: {res.error}", LogLevel.ERROR )

        return LLMResponse.from_provider_response( res, prompt, current_provider )


# ==================== Factory Function ====================
def create_llm_orchestrator(
    tokenizer_service,
    use_fallback: bool = True,
) -> LLMOrchestrator:
    """‫factory function برای ساخت LLMOrchestrator با همه dependencies"""
    return LLMOrchestrator(
        groq_client=create_groq_client(),
        gemini_client=create_gemini_client(),
        prompt_builder=create_prompt_builder(
            tokenizer_service=tokenizer_service,
            include_sources=True,
        ),
        intent_detector=create_intent_detector(),
        use_fallback=use_fallback,
    )
