from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import re
from backend.app.utils.logging_config import log_message, LG, LogLevel


# ==================== Data Classes ====================
@dataclass( slots=True, frozen=True )
class PromptResult:
    """نتیجه نهایی ساخت پرامپت"""
    system_prompt: str
    user_prompt: str
    sources_used: List[ Dict[ str, Any ] ]
    total_tokens: int
    is_system_question: bool


# ==================== Prompt Builder ====================
class PromptBuilder:
    """
    سازنده پرامپت بهینه شده با تمرکز بر سرعت و مدیریت توکن
    """

    # --- Constants ---
    DEFAULT_SYSTEM_PROMPT = """تو یک دستیار هوشمند متخصص در زمینه انقلاب اسلامی ایران هستی.

وظایف:
1. پاسخ دقیق بر اساس context.
2. زبان فارسی رسمی و روان.
3. ذکر منابع در صورت امکان.
4. اگر جواب در context نیست، صادقانه بگو.

محدودیت‌ها:
- حداکثر 3-4 پاراگراف.
- صرفاً زبان فارسی.
"""

    RAG_TEMPLATE = """اطلاعات موجود:

{context}

---

سوال کاربر: {question}

پاسخ:"""

    SYSTEM_TEMPLATE = "{question}"

    # ترکیب تمام الگوهای سیستم در یک Regex برای پرفورمنس بالا
    # گروه‌های غیرگیرنده (?: ...) برای جلوگیری از مصرف حافظه اضافی
    SYS_PATTERN_REGEX = re.compile(
        r"^(?:سلام|علیک)?\s*"          # پیشوند اختیاری سلام
        r"(?:تو (?:کی|چی) هستی|اسم[ ت] (?:چیه|چیست)|نام[ ت] (?:چیه|چیست)|خودت (?:رو )?معرفی کن|"
        r"چه (?:کاری|کمکی) (?:میشه|می‌تونی)|چیکار (?:میشه|می‌کنی))|"          # گروه اول: ابتدای جمله
        r"\b(?:تو (?:کی|چی) هستی|اسم[ ت] (?:چیه|چیست))\b",          # گروه دوم: هر جایی در متن
        re.IGNORECASE )

    def __init__( self,
                  tokenizer_service,
                  system_prompt: Optional[ str ] = None,
                  include_sources: bool = True,
                  max_context_tokens: int = 3000 ):
        self.tokenizer = tokenizer_service
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self.include_sources = include_sources
        self.max_context_tokens = max_context_tokens

        # محاسبه سربار تملیت فقط یکبار
        self.template_overhead = self.tokenizer.count_tokens( self.RAG_TEMPLATE.format( context="", question="" ) )

        log_message( LG.LLM, "PromptBuilder initialized.", LogLevel.INFO )

    def count_tokens( self, text: str ) -> int:
        return self.tokenizer.count_tokens( text, tokenizer_name="persian" )

    def is_system_question( self, query: str ) -> bool:
        """بررسی سریع با Regex ترکیبی"""
        return bool( self.SYS_PATTERN_REGEX.search( query.strip() ) )

    def build_prompt( self, query: str, chunks: List[ Dict[ str, Any ] ], include_metadata: bool = True ) -> PromptResult:
        try:
            is_sys = self.is_system_question( query )

            if is_sys:
                log_message( LG.LLM, "System question detected (No RAG).", LogLevel.INFO )
                user_prompt = self.SYSTEM_TEMPLATE.format( question=query )
                sources = []
                tokens = self.count_tokens( user_prompt )
            else:
                user_prompt, sources, tokens = self._build_rag_prompt( query, chunks, include_metadata )

            log_message( LG.LLM, f"Prompt built: {tokens} tokens, {len(sources)} sources.", LogLevel.INFO )

            return PromptResult(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                sources_used=sources,
                total_tokens=tokens,
                is_system_question=is_sys,
            )
        except Exception as e:
            log_message( LG.LLM, f"Prompt building failed: {e}", LogLevel.ERROR )
            raise

    def _build_rag_prompt( self, query: str, chunks: List[ Dict[ str, Any ] ],
                           include_metadata: bool ) -> Tuple[ str, List[ Dict ], int ]:
        """
        ساخت پرامپت RAG با مدیریت هوشمند توکن
        Returns: (user_prompt_string, sources_list, total_token_count)
        """
        context_parts = []
        sources = []
        current_tokens = 0

        # توکن‌های رزرو شده برای Query و خودِ قالب
        query_tokens = self.count_tokens( query )
        reserved = self.template_overhead + query_tokens
        available_limit = self.max_context_tokens - reserved

        # تخمین سربار هر منبع (مانند: [منبع 1 - ...]\n)
        # فرض ثابت بودن برای پرفورمنس (می‌توان دقیق‌تر هم محاسبه کرد)
        CHUNK_OVERHEAD_ESTIMATE = 20

        log_message( LG.LLM, f"Token budget for chunks: {available_limit}", LogLevel.DEBUG )

        for idx, chunk in enumerate( chunks, 1 ):
            content = chunk.get( "content", "" )
            chunk_tokens = self.count_tokens( content ) + CHUNK_OVERHEAD_ESTIMATE

            if current_tokens + chunk_tokens > available_limit:
                log_message( LG.LLM, f"Context truncated at chunk {idx-1}", LogLevel.WARNING )
                break

            metadata = chunk.get( "metadata", {} )
            sources.append( {
                "index": idx,
                "chunk_id": chunk.get( "chunk_id" ),
                "source": metadata.get( "source", "Unknown" ),
                "hierarchy": metadata.get( "hierarchy", "" ),
                "content": content,          # ← اضافه کن
            } )

            # فرمت‌دهی متن چانک
            if self.include_sources and include_metadata:
                hierarchy = metadata.get( "hierarchy", "Unknown" )
                part = f"[منبع {idx} - {hierarchy}]\n{content}"
            else:
                part = f"[مستند {idx}]\n{content}"

            context_parts.append( part )
            current_tokens += chunk_tokens

        final_context = "\n\n".join( context_parts )
        user_prompt = self.RAG_TEMPLATE.format( context=final_context, question=query )

        # محاسبه نهایی (شامل قالب و کانتکست)
        total_tokens = self.count_tokens( user_prompt )

        return user_prompt, sources, total_tokens

    def build_simple_prompt( self, query: str ) -> PromptResult:
        return PromptResult(
            system_prompt="تو یک دستیار هوشمند فارسی‌زبان هستی.",
            user_prompt=query,
            sources_used=[],
            total_tokens=self.count_tokens( query ),
            is_system_question=False,
        )


def create_prompt_builder( tokenizer_service, include_sources: bool = True, max_context_tokens: int = 3000 ) -> PromptBuilder:
    return PromptBuilder(
        tokenizer_service=tokenizer_service,
        include_sources=include_sources,
        max_context_tokens=max_context_tokens,
    )
