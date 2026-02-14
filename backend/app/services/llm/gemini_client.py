import google.generativeai as genai
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.utils.logging_config import log_message, LG, LogLevel


class GeminiClient:
    """
    کلاینت Gemini API برای fallback
    
    مدل‌های پشتیبانی شده:
    - gemini-2.0-flash-exp (پیشنهادی - سریع)
    - gemini-1.5-pro
    """

    def __init__(
        self,
        api_key: Optional[ str ] = None,
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ):
        """
        Args:
            api_key: Gemini API key
            model: نام مدل
            temperature: خلاقیت
            max_tokens: حداکثر طول پاسخ
        """
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        if not self.api_key:
            raise ValueError( "GEMINI_API_KEY یافت نشد!" )

        # تنظیم API key
        genai.configure( api_key=self.api_key )

        # ایجاد model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
            },
        )

        log_message(
            LG.LLM,
            f"GeminiClient آماده شد - Model: {model}, Temp: {temperature}",
            LogLevel.INFO,
        )

    def generate(
        self,
        prompt: str,
        temperature: Optional[ float ] = None,
        max_tokens: Optional[ int ] = None,
    ) -> Dict[ str, Any ]:
        """
        تولید پاسخ با Gemini
        
        Args:
            prompt: پرامپت کامل
            temperature: override temperature
            max_tokens: override max_tokens
            
        Returns:
            {
                'success': bool,
                'content': str,
                'model': str,
                'usage': dict,
                'error': str (در صورت خطا)
            }
        """
        try:
            # اگه override شده، model جدید بساز
            if temperature is not None or max_tokens is not None:
                temp = temperature if temperature is not None else self.temperature
                max_tok = max_tokens if max_tokens is not None else self.max_tokens

                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config={
                        "temperature": temp,
                        "max_output_tokens": max_tok,
                    },
                )
            else:
                model = self.model

            log_message(
                LG.LLM,
                f"🤖 ارسال درخواست به Gemini (model: {self.model_name})...",
                LogLevel.INFO,
            )

            # فراخوانی API
            response = model.generate_content( prompt )

            # استخراج پاسخ
            content = response.text

            # Gemini usage info (اگه موجود باشه)
            usage = {}
            if hasattr( response, "usage_metadata" ):
                usage = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count,
                }

            log_message(
                LG.LLM,
                f"✅ پاسخ از Gemini دریافت شد - Tokens: {usage.get('total_tokens', 'N/A')}",
                LogLevel.INFO,
            )

            return {
                "success": True,
                "content": content,
                "model": self.model_name,
                "usage": usage,
            }

        except Exception as e:
            log_message( LG.LLM, f"❌ خطا در Gemini API: {str(e)}", LogLevel.ERROR )
            return { "success": False, "error": str( e ) }

    def chat(
        self,
        messages: List[ Dict[ str, str ] ],
        temperature: Optional[ float ] = None,
        max_tokens: Optional[ int ] = None,
    ) -> Dict[ str, Any ]:
        """
        چت با history
        
        Args:
            messages: لیست پیام‌ها
            temperature: override temperature
            max_tokens: override max_tokens
            
        Returns:
            همان فرمت generate()
        """
        try:
            # تبدیل messages به فرمت Gemini
            # Gemini فقط یک string میگیره، پس باید merge کنیم
            prompt_parts = []
            for msg in messages:
                role = "User" if msg[ "role" ] == "user" else "Assistant"
                prompt_parts.append( f"{role}: {msg['content']}" )

            full_prompt = "\n\n".join( prompt_parts )

            # استفاده از generate
            return self.generate( full_prompt, temperature, max_tokens )

        except Exception as e:
            log_message( LG.LLM, f"❌ خطا در Gemini chat: {str(e)}", LogLevel.ERROR )
            return { "success": False, "error": str( e ) }


def create_gemini_client( model: str = "gemini-2.0-flash-exp", temperature: float = 0.3 ) -> GeminiClient:
    """
    ساخت instance از GeminiClient
    
    Args:
        model: نام مدل
        temperature: دمای تولید
        
    Returns:
        GeminiClient instance
    """
    return GeminiClient( model=model, temperature=temperature )
