from typing import List, Dict, Any, Tuple
import re
from backend.app.schemas.llm_schemas import PromptResult, SourceInfo
from backend.app.utils.logging_config import log_message, LG, LogLevel
from backend.app.core.config import settings
from backend.app.services.embedding.tokenizer_service import TokenizerService


# ==================== Prompt Builder ====================
class PromptBuilder:
    """
    ‫سازنده پرامپت بهینه با مدیریت هوشمند توکن
    ‫- تشخیص سوالات سیستمی با Regex
    ‫- محاسبه دقیق budget توکن (بدون system_prompt — جداگانه توسط API محاسبه میشه)
    ‫- overhead واقعی برای هر chunk
    """

    # ----------------- ثابت‌ها -----------------
    RAG_TEMPLATE = """اطلاعات موجود:

    {context}

    ---

    سوال کاربر: {question}

    پاسخ:"""

    SYSTEM_TEMPLATE = "{question}"

    SYS_PATTERN_REGEX = re.compile(
        r"\W*"
        r"(?:سلام|علیک)?\s*"
        r"(?:تو (?:کی|چی) هستی|اسم[ ت] (?:چیه|چیست)|نام[ ت] (?:چیه|چیست)"
        r"|خودت (?:رو )?معرفی کن"
        r"|چه (?:کاری|کمکی) (?:میشه|می‌تونی)"
        r"|چیکار (?:میشه|می‌کنی)"
        r"|(?:چه )?قابلیت‌?هایی داری"
        r"|(?:چه )?توانایی‌?هایی داری)"
        r"\W*", re.IGNORECASE )

    def __init__(
        self,
        tokenizer_service: TokenizerService,
        include_sources: bool = True,
    ):
        self.tokenizer = tokenizer_service
        self.system_prompt = settings.DEFAULT_SYSTEM_PROMPT
        self.include_sources = include_sources
        self.max_context_tokens = settings.MAX_CONTEXT_TOKENS

        # ‫محاسبه یکبار در __init__ — هر سه مقدار ثابت هستن
        template_tokens = self.tokenizer.count_tokens( self.RAG_TEMPLATE.format( context="", question="" ) )
        self.template_overhead = template_tokens
        self.system_tokens = self.tokenizer.count_tokens( self.system_prompt )

        log_message( LG.LLM, "PromptBuilder ساخته شد", LogLevel.INFO )

    def count_tokens( self, text: str ) -> int:
        return self.tokenizer.count_tokens( text )

    def is_system_question( self, query: str ) -> bool:
        """‫بررسی با fullmatch — جلوگیری از false positive در سوالات ترکیبی"""
        return bool( self.SYS_PATTERN_REGEX.fullmatch( query.strip() ) )

    def build_prompt( self, query: str, chunks: List[ Dict[ str, Any ] ], include_metadata: bool = True ) -> PromptResult:
        """
        ‫ساخت پرامپت نهایی برای LLM

        Args:
            query: سوال کاربر
            chunks: ‫لیست chunks بازیابی شده
            include_metadata: ‫آیا hierarchy در پرامپت نمایش داده شود

        Returns:
            PromptResult: ‫شامل system_prompt، user_prompt، sources و آمار توکن
        """
        try:
            is_sys = self.is_system_question( query )

            if is_sys:
                log_message( LG.LLM, "پرامپت سیستمی هستش.", LogLevel.INFO )
                user_prompt = self.SYSTEM_TEMPLATE.format( question=query )
                sources: List[ SourceInfo ] = []
                tokens = self.system_tokens + self.count_tokens( user_prompt )
            else:
                user_prompt, sources, tokens = self._build_rag_prompt( query, chunks, include_metadata )

            log_message( LG.LLM, f"پرامپت ساخته شد: {tokens} توکن, {len(sources)} منابع.", LogLevel.INFO )

            return PromptResult(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                sources_used=sources,
                total_tokens=tokens,
                is_system_question=is_sys,
            )
        except Exception as e:
            log_message( LG.LLM, f"خطا در ساخت پرامپت: {e}", LogLevel.ERROR )
            raise

    def _build_rag_prompt( self, query: str, chunks: List[ Dict[ str, Any ] ],
                           include_metadata: bool ) -> Tuple[ str, List[ SourceInfo ], int ]:
        """
        ‫ساخت پرامپت RAG با مدیریت هوشمند توکن

        Args:
            include_metadata: ‫نمایش hierarchy در header — فقط وقتی include_sources=True هم باشه فعاله

        Returns: (user_prompt_string, sources_list, total_token_count)
        ‫total_tokens شامل system_prompt + user_prompt است
        """
        context_parts = []
        sources = []
        current_tokens = 0

        query_tokens = self.tokenizer.count_tokens( query )
        available_limit = self.max_context_tokens - self.template_overhead - query_tokens

        if available_limit <= 0:
            raise ValueError( f"Query too long: {query_tokens} tokens exceeds available limit" )

        log_message( LG.LLM, f"Token budget for chunks: {available_limit}", LogLevel.DEBUG )

        for idx, chunk in enumerate( chunks, 1 ):
            content = chunk.get( "content", "" )
            metadata = chunk.get( "metadata" ) or {}
            hierarchy = metadata.get( "hierarchy", "Unknown" )

            # ‫‫include_sources کنترل نمایش hierarchy، include_metadata کنترل فعال‌سازی آن از بیرون
            header = ( f"[منبع {idx} - {hierarchy}]\n" if ( self.include_sources and include_metadata ) else f"[مستند {idx}]\n" )

            header_tokens = self.tokenizer.count_tokens( header )
            chunk_tokens = self.tokenizer.count_tokens( content ) + header_tokens

            if current_tokens + chunk_tokens > available_limit:
                log_message( LG.LLM, f"Context truncated at chunk {idx - 1}", LogLevel.WARNING )
                break

            sources.append(
                SourceInfo(
                    index=idx,
                    chunk_id=chunk.get( "chunk_id" ),
                    source=metadata.get( "source", "Unknown" ),
                    hierarchy=hierarchy,
                    content=content,
                ) )

            context_parts.append( f"{header}{content}" )
            current_tokens += chunk_tokens

        final_context = "\n\n".join( context_parts )
        safe_context = final_context.replace( "{", "{{" ).replace( "}", "}}" )
        safe_query = query.replace( "{", "{{" ).replace( "}", "}}" )
        user_prompt = self.RAG_TEMPLATE.format( context=safe_context, question=safe_query )

        # ‫total شامل system_prompt + user_prompt — system_tokens از cache در __init__
        total_tokens = self.system_tokens + self.count_tokens( user_prompt )

        return user_prompt, sources, total_tokens


def create_prompt_builder(
    tokenizer_service: TokenizerService,
    include_sources: bool = True,
) -> PromptBuilder:
    """
    ‫فکتوری برای ساخت PromptBuilder
    """
    return PromptBuilder(
        tokenizer_service=tokenizer_service,
        include_sources=include_sources,
    )
