import re
from typing import Optional
from groq import Groq, APIError
from google import genai
from google.genai import types

from backend.app.core.config import settings
from backend.app.schemas.base_schemas import QueryIntent
from backend.app.utils.logging_config import log_message, LG, LogLevel


class IntentDetector:
    """
    ‫تشخیص intent سوال کاربر — دو لایه:
    ‫لایه ۱: Conversational Regex (رایگان، فوری)
    ‫لایه ۲: LLM Classifier (دقیق، domain-agnostic)

    ‫برای استفاده در پروژه دیگه فقط در config.py:
    ‫DOMAIN_TOPIC و DOMAIN_DESCRIPTION رو عوض کن
    """

    # ‫pattern های احوال‌پرسی — مستقل از domain
    _CONVERSATIONAL_PATTERN = re.compile(
        r"^\W*"
        r"(?:سلام|درود|خوبی|خوب هستی|حالت چطوره|چطوری|"
        r"ممنون|مرسی|متشکرم|خداحافظ|بای|موفق باشی|"
        r"تشکر|عالی بود|دستت درد نکنه)"
        r"\W*$",
        re.IGNORECASE,
    )

    # ‫prompt classifier — فقط DOMAIN_TOPIC عوض میشه برای پروژه دیگه
    _CLASSIFIER_PROMPT = """تو یک سیستم طبقه‌بندی هستی.

    حوزه تخصصی: {domain_topic}
    توضیح: {domain_description}

    سوال کاربر: "{query}"

    آیا این سوال مستقیماً به حوزه تخصصی بالا مربوط است و نیاز به جستجو در اسناد دارد؟

    فقط یکی از این دو کلمه را بنویس:
    RAG
    OUT_OF_SCOPE"""

    def __init__( self ):
        self._groq_client: Optional[ Groq ] = None
        self._gemini_client = None
        self._init_clients()
        log_message( LG.LLM, "✅ IntentDetector آماده شد", LogLevel.INFO )

    def _init_clients( self ) -> None:
        """‫مقداردهی lazy clients — فقط اگه API key موجود باشه"""
        try:
            if settings.GROQ_API_KEY:
                self._groq_client = Groq(
                    api_key=settings.GROQ_API_KEY,
                    timeout=10,          # ‫timeout کوتاه برای classifier
                )
        except Exception as e:
            log_message( LG.LLM, f"⚠️ Groq client init failed: {e}", LogLevel.WARNING )

        try:
            if settings.GEMINI_API_KEY:
                self._gemini_client = genai.Client( api_key=settings.GEMINI_API_KEY )
        except Exception as e:
            log_message( LG.LLM, f"⚠️ Gemini client init failed: {e}", LogLevel.WARNING )

    def detect( self, query: str ) -> QueryIntent:
        """
        ‫تشخیص intent سوال

        Args:
            query: سوال کاربر

        Returns:
            QueryIntent: RAG | OUT_OF_SCOPE | CONVERSATIONAL
        """
        if not query or not query.strip():
            return QueryIntent.OUT_OF_SCOPE

        query = query.strip()

        # ‫لایه ۱: Conversational Regex
        intent = self._check_conversational( query )
        if intent is not None:
            log_message( LG.LLM, f"🎯 Intent (Regex): {intent} — '{query[:40]}'", LogLevel.INFO )
            return intent

        # ‫لایه ۲: LLM Classifier
        intent = self._classify_with_llm( query )
        log_message( LG.LLM, f"🎯 Intent (LLM): {intent} — '{query[:40]}'", LogLevel.INFO )
        return intent

    def _check_conversational( self, query: str ) -> Optional[ QueryIntent ]:
        """
        ‫لایه ۱: بررسی احوال‌پرسی با regex
        Returns None اگه match نشد
        """
        if self._CONVERSATIONAL_PATTERN.match( query ):
            return QueryIntent.CONVERSATIONAL
        return None

    def _classify_with_llm( self, query: str ) -> QueryIntent:
        """
        ‫لایه ۲: تشخیص با LLM
        ‫Groq اول، Gemini fallback، RAG به عنوان safe default
        """
        prompt = self._CLASSIFIER_PROMPT.format(
            domain_topic=settings.DOMAIN_TOPIC,
            domain_description=settings.DOMAIN_DESCRIPTION,
            query=query,
        )

        # ‫تلاش اول: Groq
        if self._groq_client:
            result = self._call_groq( prompt )
            if result is not None:
                return result

        # ‫تلاش دوم: Gemini
        if self._gemini_client:
            result = self._call_gemini( prompt )
            if result is not None:
                return result

        # ‫safe default — اگه هر دو fail کردن
        log_message( LG.LLM, "⚠️ هر دو classifier fail کردن — fallback به RAG", LogLevel.WARNING )
        return QueryIntent.RAG

    def _parse_intent( self, raw: str ) -> Optional[ QueryIntent ]:
        """
        ‫تبدیل ایمن خروجی LLM به QueryIntent
        ‫فقط RAG یا OUT_OF_SCOPE قبول میشه
        """
        cleaned = raw.strip().upper()

        if "OUT_OF_SCOPE" in cleaned:
            return QueryIntent.OUT_OF_SCOPE
        if "RAG" in cleaned:
            return QueryIntent.RAG

        # ‫خروجی نامعتبر — safe default
        log_message( LG.LLM, f"⚠️ خروجی نامعتبر LLM: '{raw}' — fallback به RAG", LogLevel.WARNING )
        return None

    def _call_groq( self, prompt: str ) -> Optional[ QueryIntent ]:
        """‫تماس با Groq برای classification"""
        try:
            response = self._groq_client.chat.completions.create(          # type: ignore
                model=settings.GROQ_MODEL,
                messages=[ {
                    "role": "user",
                    "content": prompt
                } ],
                max_tokens=10,          # ‫فقط RAG یا OUT_OF_SCOPE
                temperature=0.0,          # ‫قطعی‌ترین جواب
            )
            raw = response.choices[ 0 ].message.content or ""
            return self._parse_intent( raw )

        except APIError as e:
            log_message( LG.LLM, f"⚠️ Groq classifier error: {e.message}", LogLevel.WARNING )
            return None
        except Exception as e:
            log_message( LG.LLM, f"⚠️ Groq classifier unexpected error: {e}", LogLevel.WARNING )
            return None

    def _call_gemini( self, prompt: str ) -> Optional[ QueryIntent ]:
        """‫تماس با Gemini برای classification"""
        try:
            response = self._gemini_client.models.generate_content(          # type: ignore
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=10,
                    temperature=0.0,
                ),
            )
            raw = response.candidates[ 0 ].content.parts[ 0 ].text or ""          #type: ignore
            return self._parse_intent( raw )

        except Exception as e:
            log_message( LG.LLM, f"⚠️ Gemini classifier error: {e}", LogLevel.WARNING )
            return None


def create_intent_detector() -> IntentDetector:
    """‫factory function برای ساخت IntentDetector"""
    return IntentDetector()
