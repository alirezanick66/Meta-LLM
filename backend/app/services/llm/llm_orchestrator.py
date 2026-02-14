from typing import Dict, Any, List, Optional
from backend.app.services.llm.prompt_builder import PromptBuilder
from backend.app.utils.logging_config import log_message, LG, LogLevel
from backend.app.services.llm.groq_client import create_groq_client, GroqClient
from backend.app.services.llm.gemini_client import GeminiClient, create_gemini_client


class LLMOrchestrator:
    """
    مدیریت LLM با Groq (اصلی) و Gemini (fallback)
    
    فرآیند:
    1. تلاش با Groq
    2. در صورت خطا، fallback به Gemini
    3. بازگشت پاسخ نهایی
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

        log_message(
            LG.LLM,
            f"LLMOrchestrator آماده شد (fallback: {use_fallback})",
            LogLevel.INFO,
        )

    def generate_answer(
        self,
        query: str,
        chunks: List[ Dict[ str, Any ] ],
        temperature: Optional[ float ] = None,
    ) -> Dict[ str, Any ]:
        """
        تولید پاسخ با context
        
        Args:
            query: سوال کاربر
            chunks: retrieved chunks
            temperature: override temperature
            
        Returns:
            {
                'success': bool,
                'answer': str,
                'provider': str ('groq' یا 'gemini'),
                'model': str,
                'usage': dict,
                'chunks_used': int,
                'error': str (در صورت خطا)
            }
        """
        try:
            log_message( LG.LLM, "=" * 70, LogLevel.INFO )
            log_message( LG.LLM, f"🤖 تولید پاسخ برای: '{query[:50]}...'", LogLevel.INFO )
            log_message( LG.LLM, "=" * 70, LogLevel.INFO )

            # ساخت prompt
            prompt = self.prompt_builder.build_prompt( query, chunks )

            log_message(
                LG.LLM,
                f"📝 Prompt آماده شد با {len(chunks)} chunk",
                LogLevel.INFO,
            )

            # 1. تلاش با Groq
            log_message( LG.LLM, "🚀 مرحله 1: تلاش با Groq...", LogLevel.INFO )
            groq_result = self.groq.generate( prompt, temperature=temperature )

            if groq_result[ "success" ]:
                log_message( LG.LLM, "✅ پاسخ از Groq دریافت شد", LogLevel.INFO )

                return {
                    "success": True,
                    "answer": groq_result[ "content" ],
                    "provider": "groq",
                    "model": groq_result[ "model" ],
                    "usage": groq_result[ "usage" ],
                    "chunks_used": len( chunks ),
                }

            # 2. Fallback به Gemini
            if self.use_fallback:
                log_message(
                    LG.LLM,
                    f"⚠️ Groq خطا داد: {groq_result.get('error', 'نامشخص')}",
                    LogLevel.WARNING,
                )
                log_message( LG.LLM, "🔄 مرحله 2: Fallback به Gemini...", LogLevel.INFO )

                gemini_result = self.gemini.generate( prompt, temperature=temperature )

                if gemini_result[ "success" ]:
                    log_message( LG.LLM, "✅ پاسخ از Gemini دریافت شد", LogLevel.INFO )

                    return {
                        "success": True,
                        "answer": gemini_result[ "content" ],
                        "provider": "gemini",
                        "model": gemini_result[ "model" ],
                        "usage": gemini_result.get( "usage", {} ),
                        "chunks_used": len( chunks ),
                    }
                else:
                    log_message(
                        LG.LLM,
                        f"❌ Gemini هم خطا داد: {gemini_result.get('error')}",
                        LogLevel.ERROR,
                    )
                    return {
                        "success": False,
                        "error": f"Groq: {groq_result.get('error')}, Gemini: {gemini_result.get('error')}",
                    }
            else:
                # fallback غیرفعال
                return {
                    "success": False,
                    "error": f"Groq error: {groq_result.get('error')}",
                }

        except Exception as e:
            log_message( LG.LLM, f"❌ خطا در LLMOrchestrator: {str(e)}", LogLevel.ERROR )
            return { "success": False, "error": str( e ) }

    def generate_simple_answer( self, query: str, use_groq: bool = True ) -> Dict[ str, Any ]:
        """
        تولید پاسخ بدون context (برای تست)
        
        Args:
            query: سوال
            use_groq: استفاده از Groq (اگه False، Gemini)
            
        Returns:
            همان فرمت generate_answer()
        """
        try:
            prompt = self.prompt_builder.build_simple_prompt( query )

            if use_groq:
                result = self.groq.generate( prompt )
                provider = "groq"
            else:
                result = self.gemini.generate( prompt )
                provider = "gemini"

            if result[ "success" ]:
                return {
                    "success": True,
                    "answer": result[ "content" ],
                    "provider": provider,
                    "model": result[ "model" ],
                    "usage": result.get( "usage", {} ),
                    "chunks_used": 0,
                }
            else:
                return { "success": False, "error": result.get( "error" ) }

        except Exception as e:
            return { "success": False, "error": str( e ) }


def create_llm_orchestrator(
    groq_model: str = "llama-3.3-70b-versatile",
    gemini_model: str = "gemini-2.0-flash-exp",
    temperature: float = 0.3,
    max_context_length: int = 4000,
) -> LLMOrchestrator:
    """
    ساخت instance از LLMOrchestrator
    
    Args:
        groq_model: نام مدل Groq
        gemini_model: نام مدل Gemini
        temperature: دمای تولید
        max_context_length: حداکثر طول context
        
    Returns:
        LLMOrchestrator instance
    """

    groq_client = create_groq_client( model=groq_model, temperature=temperature )
    gemini_client = create_gemini_client( model=gemini_model, temperature=temperature )
    prompt_builder = PromptBuilder( max_context_length=max_context_length )

    return LLMOrchestrator(
        groq_client=groq_client,
        gemini_client=gemini_client,
        prompt_builder=prompt_builder,
        use_fallback=True,
    )
