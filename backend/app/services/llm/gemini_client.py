from typing import Optional, Dict, List, TypedDict, Any
from google import genai
from google.genai import types
from backend.app.core.config import settings
from backend.app.utils.logging_config import log_message, LG, LogLevel


class LLMResponse( TypedDict ):
    success: bool
    content: Optional[ str ]
    model: str
    usage: Dict[ str, int ]
    error: Optional[ str ]
    finish_reason: Optional[ str ]


class GeminiClient:
    """
    ‫استفاده از api gemini
    """

    def __init__( self ):
        if not settings.GEMINI_API_KEY:
            raise ValueError( "❌ GEMINI_API_KEY یافت نشد!" )

        self.client = genai.Client( api_key=settings.GEMINI_API_KEY, http_options={ 'timeout': settings.LLM_TIMEOUT } )
        self.model_name = settings.GEMINI_MODEL

        # ذخیره تنظیمات پیش‌فرض برای استفاده متدها
        self.default_temp = settings.TEMPERATURE
        self.default_max_tokens = settings.MAX_TOKENS

        # تنظیمات Safety (برای پاسخ دادن دستی در درخواست‌ها)
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

    def _extract_usage( self, response: Any ) -> Dict[ str, int ]:
        try:
            metadata = response.usage_metadata
            return {
                "prompt_tokens": metadata.prompt_token_count,
                "completion_tokens": metadata.candidates_token_count,
                "total_tokens": metadata.total_token_count
            }
        except AttributeError:
            return { "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0 }

    def _create_error_result( self, error_msg: str, finish_reason: str = "ERROR" ) -> LLMResponse:
        return LLMResponse( success=False,
                            content=None,
                            model=self.model_name,
                            usage={
                                "prompt_tokens": 0,
                                "completion_tokens": 0,
                                "total_tokens": 0
                            },
                            error=error_msg,
                            finish_reason=finish_reason )

    def _check_safety_and_content( self, response: Any ) -> LLMResponse:
        """
بررسی وضعیت فیلترهای ایمنی و استخراج محتوا  
"""

        if not response.candidates:
            # بررسی اینکه آیا دلیل blocked بودن در feedback هست
            block_reason = getattr( response, 'prompt_feedback', None )
            reason_str = block_reason.block_reason.name if block_reason else "UNKNOWN"
            return self._create_error_result( f"ورودی یا پاسخ مسدود شد. دلیل: {reason_str}", finish_reason="SAFETY" )

        candidate = response.candidates[ 0 ]

        # بررسی Finish Reason
        finish_reason_enum = candidate.finish_reason
        finish_reason = finish_reason_enum.name if finish_reason_enum else "UNKNOWN"

        if finish_reason == "SAFETY":
            return self._create_error_result( "پاسخ توسط فیلترهای ایمنی مسدود شد.", finish_reason="SAFETY" )

        if finish_reason == "MAX_TOKENS":
            log_message( LG.LLM, "⚠️ پاسخ ناقص ماند (Max Tokens).", LogLevel.WARNING )

        # استخراج متن
        try:
            content = candidate.content.parts[ 0 ].text
            return LLMResponse( success=True,
                                content=content,
                                model=self.model_name,
                                usage=self._extract_usage( response ),
                                error=None,
                                finish_reason=finish_reason )
        except ( IndexError, AttributeError ) as e:
            return self._create_error_result( "ساختار پاسخ نامعتبر است.", finish_reason="INVALID_STRUCTURE" )

    def generate(
        self,
        prompt: str,
        temperature: Optional[ float ] = None,
        max_tokens: Optional[ int ] = None,
    ) -> LLMResponse:
        """
تولید پاسخ برای یک پرامپت تکی
"""
        try:
            config = types.GenerateContentConfig(
                temperature=temperature if temperature is not None else self.default_temp,
                max_output_tokens=max_tokens if max_tokens is not None else self.default_max_tokens,
                safety_settings=self.safety_settings )

            # ارسال درخواست
            response = self.client.models.generate_content( model=self.model_name, contents=prompt, config=config )

            return self._check_safety_and_content( response )

        except Exception as e:
            error_msg = f"Gemini Generation Error: {str(e)}"
            log_message( LG.LLM, f"❌ {error_msg}", LogLevel.ERROR )
            return self._create_error_result( error_msg )

    def chat( self,
              messages: List[ Dict[ str, str ] ],
              temperature: Optional[ float ] = None,
              max_tokens: Optional[ int ] = None ) -> LLMResponse:
        """
       ‫ چت چند نوبتی.
       ‫ در SDK جدید، به جای start_chat، معمولاً کل تاریخچه (history) را به صورت 
       ‫ لیستی از Contents به متد generate_content پاس می‌دهیم.
        """
        try:
            if not messages:
                return self._create_error_result( "لیست پیام‌ها خالی است." )

            # ‫تبدیل پیام‌ها به فرمت استاندارد Contents
            # فرمت جدید: [{'role': 'user', 'parts': ['text']}, ...]
            history_contents = []
            for msg in messages:
                role = msg.get( "role", "user" )
                #‫ نقش‌ها باید دقیقا user یا model باشند
                if role == "system":
                    #‫ معمولا سیستم پیام جداگانه‌ای دارد، اما اینجا به user تبدیل می‌کنیم برای سادگی
                    #‫ یا می‌توان از system_instruction در config استفاده کرد
                    role = "user"
                elif role not in [ "user", "model" ]:
                    role = "user"

                history_contents.append( { "role": role, "parts": [ types.Part( text=msg.get( "content", "" ) ) ] } )

            config = types.GenerateContentConfig(
                temperature=temperature if temperature is not None else self.default_temp,
                max_output_tokens=max_tokens if max_tokens is not None else self.default_max_tokens,
                safety_settings=self.safety_settings )

            # ارسال کل تاریخچه به مدل
            response = self.client.models.generate_content( model=self.model_name, contents=history_contents, config=config )

            return self._check_safety_and_content( response )

        except Exception as e:
            error_msg = f"Gemini Chat Error: {str(e)}"
            log_message( LG.LLM, f"❌ {error_msg}", LogLevel.ERROR )
            return self._create_error_result( error_msg )


def get_gemini_model_list():
    """
   ‫ دریافت اطلاعات مدل Gemini (مثل نام، ورژن، تنظیمات)
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
