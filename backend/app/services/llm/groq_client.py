from typing import Optional, List
from groq import APIError, Groq
from groq.types.chat import ChatCompletionMessageParam
from backend.app.core.config import settings
from backend.app.schemas.base_schemas import FinishReason
from backend.app.utils.logging_config import log_message, LG, LogLevel
from backend.app.schemas.llm_schemas import LLMUsage, ProviderLLMResponse


class GroqClient:
    """
    ‫استفاده از api Groq
    """

    def __init__( self ):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.default_temperature = settings.TEMPERATURE
        self.default_max_tokens = settings.MAX_TOKENS

        if not self.api_key:
            raise ValueError( "GROQ_API_KEY یافت نشد!" )

        # ‫ایجاد client
        self.client = Groq( api_key=self.api_key, timeout=settings.LLM_TIMEOUT )

        log_message( LG.LLM, f"GroqClient آماده شد - Model: {self.model}, Temp: {self.default_temperature}", LogLevel.INFO )

    def _execute_request( self,
                          messages: List[ ChatCompletionMessageParam ],
                          temperature: Optional[ float ] = None,
                          max_tokens: Optional[ int ] = None ) -> ProviderLLMResponse:
        """
       ‫ هسته مرکزی برای مدیریت تمام درخواست‌ها و خطاها (Internal Only)
        """
        try:
            temp = temperature if temperature is not None else self.default_temperature
            max_tok = max_tokens if max_tokens is not None else self.default_max_tokens

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=max_tok,
            )

            # استخراج متمرکز داده‌ها
            usage_data = response.usage
            usage = LLMUsage(
                prompt_tokens=usage_data.prompt_tokens if usage_data else 0,
                completion_tokens=usage_data.completion_tokens if usage_data else 0,
                total_tokens=usage_data.total_tokens if usage_data else 0,
            )

            content = response.choices[ 0 ].message.content
            finish_reason = FinishReason(
                response.choices[ 0 ].finish_reason.upper() ) if response.choices[ 0 ].finish_reason else FinishReason.STOP
            return ProviderLLMResponse(
                success=True,
                content=content,
                model=self.model,
                usage=usage,
                error=None,
                finish_reason=finish_reason,
            )

        except APIError as e:          # ‫خطاهای اختصاصی Groq
            error_msg = f"Groq API Error: {e.message}"
            log_message( LG.LLM, f"❌ {error_msg}", LogLevel.ERROR )
            return ProviderLLMResponse.create_error( error_msg, self.model )

        except Exception as e:
            error_msg = f"Unexpected Error: {str(e)}"
            log_message( LG.LLM, f"❌ {error_msg}", LogLevel.ERROR )
            return ProviderLLMResponse.create_error( error_msg, self.model )

    def generate( self, prompt: str, **kwargs ) -> ProviderLLMResponse:
        """تولید پاسخ برای یک پرامپت تکی"""
        log_message( LG.LLM, f"🤖 ارسال Single Prompt به {self.model}...", LogLevel.INFO )
        messages: List[ ChatCompletionMessageParam ] = [ { "role": "user", "content": prompt } ]
        return self._execute_request( messages, **kwargs )

    def chat( self, messages: List[ ChatCompletionMessageParam ], **kwargs ) -> ProviderLLMResponse:
        """چت چند نوبتی با تاریخچه"""
        log_message( LG.LLM, f"💬 ارسال Chat Context ({len(messages)} پیام)...", LogLevel.INFO )
        return self._execute_request( messages, **kwargs )


def create_groq_client() -> GroqClient:
    return GroqClient()
