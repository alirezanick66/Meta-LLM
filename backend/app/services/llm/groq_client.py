from typing import Optional, Dict, Any, List
from groq import Groq
from groq.types.chat import ChatCompletionMessageParam
from backend.app.core.config import settings
from backend.app.utils.logging_config import log_message, LG, LogLevel


class GroqClient:
    """
    کلاینت Groq API برای تولید پاسخ با LLM
    
    مدل‌های پشتیبانی شده:
    - llama-3.3-70b-versatile (پیشنهادی)
    - llama-3.1-70b-versatile
    - mixtral-8x7b-32768
    """

    def __init__(
        self,
        api_key: Optional[ str ] = None,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ):
        """
        Args:
            api_key: Groq API key (اگه None باشه از settings میگیره)
            model: نام مدل
            temperature: خلاقیت (0-1، کمتر = دقیق‌تر)
            max_tokens: حداکثر طول پاسخ
        """
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        if not self.api_key:
            raise ValueError( "GROQ_API_KEY یافت نشد!" )

        # ایجاد client
        self.client = Groq( api_key=self.api_key )

        log_message(
            LG.LLM,
            f"GroqClient آماده شد - Model: {model}, Temp: {temperature}",
            LogLevel.INFO,
        )

    def generate(
        self,
        prompt: str,
        temperature: Optional[ float ] = None,
        max_tokens: Optional[ int ] = None,
    ) -> Dict[ str, Any ]:
        """
        تولید پاسخ با Groq
        
        Args:
            prompt: پرامپت کامل
            temperature: override temperature (اختیاری)
            max_tokens: override max_tokens (اختیاری)
            
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
            temp = temperature if temperature is not None else self.temperature
            max_tok = max_tokens if max_tokens is not None else self.max_tokens

            log_message(
                LG.LLM,
                f"🤖 ارسال درخواست به Groq (model: {self.model})...",
                LogLevel.INFO,
            )

            # فراخوانی API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[ {
                    "role": "user",
                    "content": prompt
                } ],
                temperature=temp,
                max_tokens=max_tok,
            )

            # استخراج پاسخ
            content = response.choices[ 0 ].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }

            log_message(
                LG.LLM,
                f"✅ پاسخ دریافت شد - Tokens: {usage['total_tokens']}",
                LogLevel.INFO,
            )

            return {
                "success": True,
                "content": content,
                "model": self.model,
                "usage": usage,
            }

        except Exception as e:
            log_message( LG.LLM, f"❌ خطا در Groq API: {str(e)}", LogLevel.ERROR )
            return { "success": False, "error": str( e ) }

    def chat(
        self,
        messages: List[ ChatCompletionMessageParam ],
        temperature: Optional[ float ] = None,
        max_tokens: Optional[ int ] = None,
    ) -> Dict[ str, Any ]:
        """
        چت با history (برای گفتگوهای چند نوبتی)
        
        Args:
            messages: لیست پیام‌ها [{"role": "user/assistant", "content": "..."}]
            temperature: override temperature
            max_tokens: override max_tokens
            
        Returns:
            همان فرمت generate()
        """
        try:
            temp = temperature if temperature is not None else self.temperature
            max_tok = max_tokens if max_tokens is not None else self.max_tokens

            log_message(
                LG.LLM,
                f"💬 ارسال chat با {len(messages)} پیام به Groq...",
                LogLevel.INFO,
            )

            response = self.client.chat.completions.create( model=self.model,
                                                            messages=messages,
                                                            temperature=temp,
                                                            max_tokens=max_tok )

            content = response.choices[ 0 ].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }

            log_message(
                LG.LLM,
                f"✅ پاسخ chat دریافت شد - Tokens: {usage['total_tokens']}",
                LogLevel.INFO,
            )

            return {
                "success": True,
                "content": content,
                "model": self.model,
                "usage": usage,
            }

        except Exception as e:
            log_message( LG.LLM, f"❌ خطا در Groq chat: {str(e)}", LogLevel.ERROR )
            return { "success": False, "error": str( e ) }


def create_groq_client( model: str = "llama-3.3-70b-versatile", temperature: float = 0.3 ) -> GroqClient:
    """
    ساخت instance از GroqClient
    
    Args:
        model: نام مدل
        temperature: دمای تولید
        
    Returns:
        GroqClient instance
    """
    return GroqClient( model=model, temperature=temperature )
