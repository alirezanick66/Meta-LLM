"""
تست کامل RAG Pipeline (End-to-End)
شامل: Retrieval + LLM Generation
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent ) )

from backend.app.api.dependencies import get_hybrid_retriever, get_llm_orchestrator
from backend.app.services.llm.llm_orchestrator import LLMResponse
from backend.app.utils.logging_config import log_message, LG, LogLevel

# ==================== Constants ====================
ANSWER_PREVIEW_LEN = 300
CHUNK_PREVIEW_LEN = 80
TOP_CHUNKS_LOG = 3


def _log_chunks_summary( chunks: List[ Dict[ str, Any ] ] ):
    """لاگ کردن خلاصه chunk های بازیابی شده"""
    if not chunks:
        log_message( LG.LLM, "⚠️ هیچ chunk ای پیدا نشد", LogLevel.WARNING )
        return

    log_message( LG.LLM, f"✅ {len(chunks)} chunk بازیابی شد", LogLevel.INFO )
    log_message( LG.LLM, f"📚 Top-{TOP_CHUNKS_LOG} Retrieved Chunks:", LogLevel.INFO )

    for rank, chunk in enumerate( chunks[ :TOP_CHUNKS_LOG ], start=1 ):
        chunk_id = chunk.get( "chunk_id", "unknown" )
        rrf_score = chunk.get( "rrf_score", 0 )
        content = chunk.get( "content", "" )[ :CHUNK_PREVIEW_LEN ] + "..."

        log_message( LG.LLM, f"  #{rank}. [{chunk_id}] (RRF: {rrf_score:.4f})", LogLevel.DEBUG )
        log_message( LG.LLM, f"      {content}", LogLevel.DEBUG )


def _log_result_summary( expected_type: str, response: LLMResponse ):
    """
    لاگ کردن خلاصه نتیجه نهایی LLM.
    فقط به نوع مورد انتظار و پاسخ نهایی نیاز دارد.
    """

    # 1. چک کردن موفقیت اولیه (Guard Clause)
    if not response.success:
        log_message( LG.LLM, f"❌ خطا در تولید پاسخ: {response.error}", LogLevel.ERROR )
        return

    log_message( LG.LLM, "=" * 70, LogLevel.INFO )
    log_message( LG.LLM, "✅ پاسخ تولید شد!", LogLevel.INFO )

    # 2. اطلاعات فنی (Provider & Usage)
    usage = response.usage or {}
    log_message(
        LG.LLM,
        f"🤖 {response.provider.upper()} | 📦 {response.model} | "          # type: ignore
        f"📊 In:{usage.get('prompt_tokens',0)} Out:{usage.get('completion_tokens',0)} | "
        f"🔢 Pre-Tokens:{response.prompt_tokens}",
        LogLevel.INFO )

    # 3. بررسی نوع سوال (سیستمی یا RAG)
    is_sys_q = response.is_system_question
    correct_type = ( expected_type == "system" and is_sys_q ) or ( expected_type == "rag" and not is_sys_q )

    status_icon = "✅" if correct_type else "⚠️"
    detected = "System" if is_sys_q else "RAG"
    log_message( LG.LLM, f"{status_icon} Type Check: Expected={expected_type}, Detected={detected}", LogLevel.INFO )

    # 4. منابع (فقط برای RAG)
    if response.sources and not is_sys_q:
        log_message( LG.LLM, f"📑 Sources Used: {len(response.sources)}", LogLevel.INFO )
        for s in response.sources[ :TOP_CHUNKS_LOG ]:
            log_message( LG.LLM, f"  • Source {s['index']}: {s['hierarchy'][:60]}...", LogLevel.INFO )

    # 5. پاسخ نهایی
    log_message( LG.LLM, "-" * 70, LogLevel.INFO )
    if response.answer:
        preview = response.answer[ :ANSWER_PREVIEW_LEN ] + ( "..." if len( response.answer ) > ANSWER_PREVIEW_LEN else "" )
        log_message( LG.LLM, f"📄 Answer:\n{preview}", LogLevel.INFO )
    else:
        log_message( LG.LLM, "⚠️ پاسخی دریافت نشد", LogLevel.WARNING )


def test_rag_pipeline():
    log_message( LG.LLM, "🧪 شروع تست RAG Pipeline (End-to-End)", LogLevel.INFO )

    # ==================== Setup ====================
    try:
        retriever = get_hybrid_retriever( bm25_top_k=20, vector_top_k=20, final_top_k=5 )
        orchestrator = get_llm_orchestrator( max_context_tokens=3000, use_fallback=True )
        log_message( LG.LLM, "✅ کامپوننت‌ها آماده شدند", LogLevel.INFO )
    except Exception as e:
        log_message( LG.LLM, f"❌ خطا در Setup: {e}", LogLevel.ERROR )
        return

    # ==================== Test Cases ====================
    test_queries = [
        {
            "query": "انقلاب اسلامی چه تأثیری بر نظریه های غربی گذاشت؟",
            "type": "rag"
        },
        {
            "query": "نقش امام خمینی در انقلاب چه بود؟",
            "type": "rag"
        },
        {
            "query": "تو کی هستی؟",
            "type": "system"
        },
        {
            "query": "سلام، اسمت چیه؟",
            "type": "system"
        },
    ]

    # ==================== Execution Loop ====================
    for i, case in enumerate( test_queries, start=1 ):
        query, expected_type = case[ "query" ], case[ "type" ]

        log_message( LG.LLM, f"\n{'='*70}\n📝 Query #{i}: '{query}' (Type: {expected_type})\n{'='*70}", LogLevel.INFO )

        try:
            # 1. Retrieval
            chunks = retriever.retrieve( query, final_top_k=5 )
            _log_chunks_summary( chunks )

            # 2. Generation
            response = orchestrator.generate_answer( query, chunks, temperature=0.3 )

            # 3. Reporting (تمام لاگ‌های پیچیده به این خط منتقل شد)
            _log_result_summary( expected_type, response )

        except Exception as e:
            log_message( LG.LLM, f"❌ Critical Error: {e}", LogLevel.ERROR )
            import traceback
            log_message( LG.LLM, traceback.format_exc(), LogLevel.ERROR )

    log_message( LG.LLM, "\n🎉 تست RAG Pipeline تکمیل شد", LogLevel.INFO )


if __name__ == "__main__":
    test_rag_pipeline()
