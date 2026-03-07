from typing import Optional, Dict, List, Any
from google import genai
from google.genai import types
from backend.app.core.config import settings
from backend.app.utils.logging_config import log_message, LG, LogLevel
from backend.app.schemas.llm_schemas import LLMUsage, ProviderLLMResponse
from backend.app.schemas.base_schemas import FinishReason


class GeminiClient:
    """
    ‫استفاده از api gemini
    """

    def __init__( self ):
        if not settings.GEMINI_API_KEY:
            raise ValueError( "❌ GEMINI_API_KEY یافت نشد!" )

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options={ "timeout": settings.LLM_TIMEOUT },
        )
        self.model_name = settings.GEMINI_MODEL
        self.default_temp = settings.TEMPERATURE
        self.default_max_tokens = settings.MAX_TOKENS

        # ‫تنظیمات Safety
        self.safety_settings = [
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            ),
        ]

        log_message( LG.LLM, f"GeminiClient (New SDK) آماده شد - Model: {self.model_name}", LogLevel.INFO )

    def _extract_usage( self, response: Any ) -> LLMUsage:
        try:
            metadata = response.usage_metadata
            return LLMUsage(
                prompt_tokens=metadata.prompt_token_count,
                completion_tokens=metadata.candidates_token_count,
                total_tokens=metadata.total_token_count,
            )
        except AttributeError:
            return LLMUsage()

    def _parse_finish_reason( self, raw: str ) -> FinishReason:
        """‫تبدیل ایمن string به FinishReason Enum"""
        try:
            return FinishReason( raw.upper() )
        except ValueError:
            return FinishReason.UNKNOWN

    def _check_safety_and_content( self, response: Any ) -> ProviderLLMResponse:
        """
        ‫بررسی وضعیت فیلترهای ایمنی و استخراج محتوا
        """
        if not response.candidates:
            block_reason = getattr( response, "prompt_feedback", None )
            reason_str = block_reason.block_reason.name if block_reason else "UNKNOWN"
            return ProviderLLMResponse.create_error( f"ورودی یا پاسخ مسدود شد. دلیل: {reason_str}", self.model_name,
                                                     FinishReason.SAFETY )

        candidate = response.candidates[ 0 ]

        finish_reason_enum = candidate.finish_reason
        finish_reason_str = finish_reason_enum.name if finish_reason_enum else "UNKNOWN"
        finish_reason = self._parse_finish_reason( finish_reason_str )

        if finish_reason == FinishReason.SAFETY:
            return ProviderLLMResponse.create_error(
                "پاسخ توسط فیلترهای ایمنی مسدود شد.",
                self.model_name,
                FinishReason.SAFETY,
            )

        if finish_reason == FinishReason.MAX_TOKENS:
            log_message( LG.LLM, "⚠️ پاسخ ناقص ماند (Max Tokens).", LogLevel.WARNING )

        try:
            content = candidate.content.parts[ 0 ].text
            return ProviderLLMResponse(
                success=True,
                content=content,
                model=self.model_name,
                usage=self._extract_usage( response ),
                error=None,
                finish_reason=finish_reason,
            )
        except ( IndexError, AttributeError ):
            return ProviderLLMResponse.create_error(
                "ساختار پاسخ نامعتبر است.",
                self.model_name,
                FinishReason.INVALID_STRUCTURE,
            )

    def generate(
        self,
        prompt: str,
        temperature: Optional[ float ] = None,
        max_tokens: Optional[ int ] = None,
    ) -> ProviderLLMResponse:
        """
        ‫تولید پاسخ برای یک پرامپت تکی
        """
        try:
            config = types.GenerateContentConfig(
                temperature=temperature if temperature is not None else self.default_temp,
                max_output_tokens=max_tokens if max_tokens is not None else self.default_max_tokens,
                safety_settings=self.safety_settings,
            )
            response = self.client.models.generate_content( model=self.model_name, contents=prompt, config=config )
            return self._check_safety_and_content( response )

        except Exception as e:
            error_msg = f"Gemini Generation Error: {str(e)}"
            log_message( LG.LLM, f"❌ {error_msg}", LogLevel.ERROR )
            return ProviderLLMResponse.create_error( error_msg, self.model_name )

    def chat(
        self,
        messages: List[ Dict[ str, str ] ],
        temperature: Optional[ float ] = None,
        max_tokens: Optional[ int ] = None,
    ) -> ProviderLLMResponse:
        """
        ‫چت چند نوبتی با پشتیبانی از system_instruction
        """
        try:
            if not messages:
                return ProviderLLMResponse.create_error( "لیست پیام‌ها خالی است.", self.model_name )

            # ‫جداسازی system prompt و ارسال به عنوان system_instruction
            system_text = next( ( m.get( "content", "" ) for m in messages if m.get( "role" ) == "system" ), None )

            # ‫فقط پیام‌های user/model — بدون system
            history_contents = [ {
                "role": msg[ "role" ],
                "parts": [ types.Part( text=msg.get( "content", "" ) ) ],
            } for msg in messages if msg.get( "role" ) != "system" ]

            config = types.GenerateContentConfig(
                temperature=temperature if temperature is not None else self.default_temp,
                max_output_tokens=max_tokens if max_tokens is not None else self.default_max_tokens,
                safety_settings=self.safety_settings,
                system_instruction=system_text,
            )

            response = self.client.models.generate_content( model=self.model_name, contents=history_contents, config=config )
            return self._check_safety_and_content( response )

        except Exception as e:
            error_msg = f"Gemini Chat Error: {str(e)}"
            log_message( LG.LLM, f"❌ {error_msg}", LogLevel.ERROR )
            return ProviderLLMResponse.create_error( error_msg, self.model_name )


def get_gemini_model_list() -> None:
    """
    ‫دریافت اطلاعات مدل Gemini (مثل نام، ورژن، تنظیمات)
    """
    try:
        client = genai.Client( api_key=settings.GEMINI_API_KEY )
        models = client.models.list()
        gemini_models = [ model for model in models if "gemini" in model.name.lower() ]          # type: ignore
        for model in gemini_models:
            log_message( LG.LLM, model.name, LogLevel.INFO )
    except Exception as e:
        log_message( LG.LLM, f"❌ خطا در دریافت لیست مدل‌های Gemini: {str(e)}", LogLevel.ERROR )


def create_gemini_client() -> GeminiClient:
    return GeminiClient()
