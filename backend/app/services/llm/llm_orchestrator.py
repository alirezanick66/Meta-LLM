from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from backend.app.services.llm.groq_client import GroqClient
from backend.app.services.llm.gemini_client import GeminiClient
from backend.app.services.llm.prompt_builder import PromptBuilder, PromptResult
from backend.app.utils.logging_config import log_message, LG, LogLevel
from backend.app.services.llm.groq_client import create_groq_client
from backend.app.services.llm.gemini_client import create_gemini_client
from backend.app.services.llm.prompt_builder import create_prompt_builder


# ==================== Data Classes ====================
@dataclass( slots=True, frozen=True )
class LLMResponse:
    """
    نتیجه نهایی تولید پاسخ
    
    Attributes:
        success: موفقیت عملیات
        answer: پاسخ نهایی (اگه موفق)
        provider: 'groq' یا 'gemini'
        model: نام مدل استفاده شده
        usage: اطلاعات مصرف توکن
        sources: منابع استفاده شده از retrieval
        prompt_tokens: توکن‌های prompt
        is_system_question: آیا سوال سیستمی بود؟
        error: پیام خطا (اگه ناموفق)
    """

    success: bool
    answer: Optional[ str ] = None
    provider: Optional[ str ] = None
    model: Optional[ str ] = None
    usage: Optional[ Dict[ str, int ] ] = None
    sources: Optional[ List[ Dict[ str, Any ] ] ] = None
    prompt_tokens: int = 0
    is_system_question: bool = False
    error: Optional[ str ] = None

    def __post_init__( self ):
        """تنظیم مقادیر پیش‌فرض"""
        if self.usage is None:
            object.__setattr__( self, "usage", {} )
        if self.sources is None:
            object.__setattr__( self, "sources", [] )


# ==================== LLM Orchestrator ====================
class LLMOrchestrator:
    """
    مدیریت LLM با Groq (اصلی) و Gemini (fallback)
    
    فرآیند:
    1. ساخت prompt با PromptBuilder
    2. تلاش با Groq
    3. در صورت خطا، fallback به Gemini
    4. بازگشت LLMResponse
    """

    def __init__(
        self,
        groq_client: GroqClient,
        gemini_client: GeminiClient,
        prompt_builder: PromptBuilder,
        use_fallback: bool = True,
    ):
        """
        Args:
            groq_client: instance از GroqClient
            gemini_client: instance از GeminiClient
            prompt_builder: instance از PromptBuilder
            use_fallback: استفاده از fallback در صورت خطا
        """
        self.groq = groq_client
        self.gemini = gemini_client
        self.prompt_builder = prompt_builder
        self.use_fallback = use_fallback

        log_message( LG.LLM, f"LLMOrchestrator آماده شد (fallback: {use_fallback})", LogLevel.INFO )

    def generate_answer(
        self,
        query: str,
        chunks: List[ Dict[ str, Any ] ],
        temperature: Optional[ float ] = None,
        include_metadata: bool = True,
    ) -> LLMResponse:
        """
        تولید پاسخ با context
        
        Args:
            query: سوال کاربر
            chunks: retrieved chunks
            temperature: override temperature
            include_metadata: شامل metadata در prompt
            
        Returns:
            LLMResponse
        """
        try:
            log_message( LG.LLM, "=" * 70, LogLevel.INFO )
            log_message( LG.LLM, f"🤖 تولید پاسخ برای: '{query[:50]}...'", LogLevel.INFO )
            log_message( LG.LLM, "=" * 70, LogLevel.INFO )

            # 🆕 ساخت prompt با PromptBuilder
            prompt_result: PromptResult = self.prompt_builder.build_prompt( query=query,
                                                                            chunks=chunks,
                                                                            include_metadata=include_metadata )

            log_message(
                LG.LLM, f"📝 Prompt: {prompt_result.total_tokens} tokens, "
                f"{len(prompt_result.sources_used)} sources, "
                f"system_q: {prompt_result.is_system_question}", LogLevel.INFO )

            # 1️⃣ تلاش با Groq
            log_message( LG.LLM, "🚀 مرحله 1: تلاش با Groq...", LogLevel.INFO )
            groq_result = self._call_groq( prompt_result, temperature )

            if groq_result[ "success" ]:
                log_message( LG.LLM, "✅ پاسخ از Groq دریافت شد", LogLevel.INFO )
                return self._build_response(
                    success=True,
                    answer=groq_result[ "content" ],
                    provider="groq",
                    model=groq_result[ "model" ],
                    usage=groq_result[ "usage" ],
                    prompt_result=prompt_result,
                )

            # 2️⃣ Fallback به Gemini
            if self.use_fallback:
                log_message( LG.LLM, f"⚠️ Groq خطا داد: {groq_result.get('error', 'نامشخص')}", LogLevel.WARNING )
                log_message( LG.LLM, "🔄 مرحله 2: Fallback به Gemini...", LogLevel.INFO )

                gemini_result = self._call_gemini( prompt_result, temperature )

                if gemini_result[ "success" ]:
                    log_message( LG.LLM, "✅ پاسخ از Gemini دریافت شد", LogLevel.INFO )
                    return self._build_response(
                        success=True,
                        answer=gemini_result[ "content" ],
                        provider="gemini",
                        model=gemini_result[ "model" ],
                        usage=gemini_result.get( "usage", {} ),
                        prompt_result=prompt_result,
                    )
                else:
                    # هر دو failed
                    log_message(
                        LG.LLM,
                        f"❌ Gemini هم خطا داد: {gemini_result.get('error')}",
                        LogLevel.ERROR,
                    )
                    return LLMResponse(
                        success=False,
                        error=f"Groq: {groq_result.get('error')}, Gemini: {gemini_result.get('error')}",
                        prompt_tokens=prompt_result.total_tokens,
                        is_system_question=prompt_result.is_system_question,
                    )
            else:
                # fallback غیرفعال
                return LLMResponse(
                    success=False,
                    error=f"Groq error: {groq_result.get('error')}",
                    prompt_tokens=prompt_result.total_tokens,
                    is_system_question=prompt_result.is_system_question,
                )

        except Exception as e:
            log_message( LG.LLM, f"❌ خطا در LLMOrchestrator: {str(e)}", LogLevel.ERROR )
            return LLMResponse( success=False, error=str( e ) )

    def _call_groq( self, prompt_result: PromptResult, temperature: Optional[ float ] ) -> Dict[ str, Any ]:
        """
        فراخوانی Groq با system/user prompts
        
        Args:
            prompt_result: نتیجه PromptBuilder
            temperature: دمای تولید
            
        Returns:
            dict با success, content, model, usage, error
        """
        try:
            # 🆕 استفاده از chat برای system + user
            messages = [
                {
                    "role": "system",
                    "content": prompt_result.system_prompt
                },
                {
                    "role": "user",
                    "content": prompt_result.user_prompt
                },
            ]

            return self.groq.chat( messages=messages, temperature=temperature )

        except Exception as e:
            return { "success": False, "error": str( e ) }

    def _call_gemini( self, prompt_result: PromptResult, temperature: Optional[ float ] ) -> Dict[ str, Any ]:
        """
        فراخوانی Gemini با system/user prompts
        
        Args:
            prompt_result: نتیجه PromptBuilder
            temperature: دمای تولید
            
        Returns:
            dict با success, content, model, usage, error
        """
        try:
            # 🆕 استفاده از chat برای system + user
            messages = [
                {
                    "role": "system",
                    "content": prompt_result.system_prompt
                },
                {
                    "role": "user",
                    "content": prompt_result.user_prompt
                },
            ]

            return self.gemini.chat( messages=messages, temperature=temperature )

        except Exception as e:
            return { "success": False, "error": str( e ) }

    def _build_response(
        self,
        success: bool,
        answer: str,
        provider: str,
        model: str,
        usage: Dict[ str, int ],
        prompt_result: PromptResult,
    ) -> LLMResponse:
        """
        ساخت LLMResponse نهایی
        
        Args:
            success: موفقیت
            answer: پاسخ LLM
            provider: 'groq' یا 'gemini'
            model: نام مدل
            usage: مصرف توکن
            prompt_result: نتیجه PromptBuilder
            
        Returns:
            LLMResponse
        """
        return LLMResponse(
            success=success,
            answer=answer,
            provider=provider,
            model=model,
            usage=usage,
            sources=prompt_result.sources_used,
            prompt_tokens=prompt_result.total_tokens,
            is_system_question=prompt_result.is_system_question,
        )

    def generate_simple_answer( self, query: str, use_groq: bool = True ) -> LLMResponse:
        """
        تولید پاسخ بدون context (برای تست)
        
        Args:
            query: سوال
            use_groq: استفاده از Groq (اگه False، Gemini)
            
        Returns:
            LLMResponse
        """
        try:
            prompt_result = self.prompt_builder.build_simple_prompt( query )

            if use_groq:
                result = self.groq.generate( prompt_result.user_prompt )
                provider = "groq"
            else:
                result = self.gemini.generate( prompt_result.user_prompt )
                provider = "gemini"

            if result[ "success" ]:
                return LLMResponse(
                    success=True,
                    answer=result[ "content" ],
                    provider=provider,
                    model=result[ "model" ],
                    usage=result.get( "usage", {} ),
                    sources=[],
                    prompt_tokens=prompt_result.total_tokens,
                    is_system_question=False,
                )
            else:
                return LLMResponse( success=False, error=result.get( "error" ) )

        except Exception as e:
            return LLMResponse( success=False, error=str( e ) )


    # ==================== Factory Function ====================
def create_llm_orchestrator(
    groq_model: Optional[ str ] = None,
    gemini_model: Optional[ str ] = None,
    temperature: float = 0.3,
    max_context_tokens: int = 3000,
    use_fallback: bool = True,
) -> LLMOrchestrator:
    """
    ساخت instance از LLMOrchestrator
    
    Args:
        groq_model: نام مدل Groq (اختیاری، از settings میگیره)
        gemini_model: نام مدل Gemini (اختیاری، از settings میگیره)
        temperature: دمای تولید
        max_context_tokens: حداکثر توکن context
        use_fallback: فعال کردن fallback به Gemini
        
    Returns:
        LLMOrchestrator instance
    """

    # ساخت clients
    groq_client = create_groq_client()
    gemini_client = create_gemini_client()          # از settings می‌گیره

    # ساخت prompt builder
    prompt_builder = create_prompt_builder( include_sources=True, max_context_tokens=max_context_tokens )

    return LLMOrchestrator(
        groq_client=groq_client,
        gemini_client=gemini_client,
        prompt_builder=prompt_builder,
        use_fallback=use_fallback,
    )
