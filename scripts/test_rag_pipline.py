"""
‫تست کامل RAG Pipeline (End-to-End)
‫شامل: Retrieval + Content Fetch + Reranking + LLM Generation
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent ) )

from backend.app.api.dependencies import get_hybrid_retriever, get_llm_orchestrator
from backend.app.core.database import SessionLocal
from backend.app.core.config import settings
from backend.app.db.postgres import PostgresManager
from backend.app.schemas.base_schemas import QueryIntent
from backend.app.services.llm.llm_orchestrator import LLMResponse
from backend.app.utils.logging_config import log_message, LG, LogLevel

# ==================== Constants ====================
ANSWER_PREVIEW_LEN = 300
CHUNK_PREVIEW_LEN = 80
TOP_CHUNKS_LOG = 3


def _log_chunks_summary( chunks: List[ Dict[ str, Any ] ] ):
    """‫لاگ کردن خلاصه chunk های بازیابی شده"""
    if not chunks:
        log_message( LG.LLM, "⚠️ هیچ chunk ای پیدا نشد", LogLevel.WARNING )
        return

    log_message( LG.LLM, f"✅ {len(chunks)} chunk بازیابی شد", LogLevel.INFO )
    log_message( LG.LLM, f"📚 Top-{TOP_CHUNKS_LOG} Retrieved Chunks:", LogLevel.INFO )

    for rank, chunk in enumerate( chunks[ :TOP_CHUNKS_LOG ], start=1 ):
        chunk_id = chunk.get( "chunk_id", "unknown" )
        rrf_score = chunk.get( "rrf_score", 0 )
        reranker_score = chunk.get( "reranker_score", "N/A" )
        content_preview = chunk.get( "content", "" )[ :CHUNK_PREVIEW_LEN ] + "..."

        log_message(
            LG.LLM, f"  #{rank}. [{chunk_id}] (RRF: {rrf_score:.4f} | Reranker: {reranker_score:.4f})" if isinstance(
                reranker_score, float ) else f"  #{rank}. [{chunk_id}] (RRF: {rrf_score:.4f})", LogLevel.DEBUG )
        log_message( LG.LLM, f"      {content_preview}", LogLevel.DEBUG )


def _log_result_summary( expected_type: str, response: LLMResponse ):
    """‫لاگ کردن خلاصه نتیجه نهایی LLM"""
    if not response.success:
        log_message( LG.LLM, f"❌ خطا در تولید پاسخ: {response.error}", LogLevel.ERROR )
        return

    log_message( LG.LLM, "=" * 70, LogLevel.INFO )
    log_message( LG.LLM, "✅ پاسخ تولید شد!", LogLevel.INFO )

    # ‫اطلاعات فنی
    usage = response.usage
    log_message(
        LG.LLM,
        f"🤖 {response.provider} | 📦 {response.model} | "
        f"📊 In:{usage.prompt_tokens} Out:{usage.completion_tokens} | "
        f"🔢 Pre-Tokens:{response.prompt_tokens}",
        LogLevel.INFO,
    )

    # ‫بررسی intent
    detected_intent = response.intent
    expected_intent = QueryIntent.RAG if expected_type == "rag" else QueryIntent.OUT_OF_SCOPE
    correct_type = detected_intent == expected_intent
    status_icon = "✅" if correct_type else "⚠️"
    log_message( LG.LLM, f"{status_icon} Intent Check: Expected={expected_type}, Detected={detected_intent}", LogLevel.INFO )

    # ‫منابع — فقط برای RAG
    if response.sources and detected_intent == QueryIntent.RAG:
        log_message( LG.LLM, f"📑 Sources Used: {len(response.sources)}", LogLevel.INFO )
        for s in response.sources[ :TOP_CHUNKS_LOG ]:
            log_message( LG.LLM, f"  • Source {s.index}: {s.hierarchy[:60]}", LogLevel.INFO )

    # ‫پاسخ نهایی
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
        retriever = get_hybrid_retriever()
        orchestrator = get_llm_orchestrator()
        log_message( LG.LLM, "✅ کامپوننت‌ها آماده شدند", LogLevel.INFO )
    except Exception as e:
        log_message( LG.LLM, f"❌ خطا در Setup: {e}", LogLevel.ERROR )
        return

    # ==================== Test Cases ====================
    test_queries = [
        {
            "query": "حداقل مزد کارگر در سال 1404 چقدر است؟",
            "type": "rag"
        },
        {
            "query": "شرایط دریافت بیمه بیکاری چیست؟",
            "type": "rag"
        },
        {
            "query": "مرخصی زایمان کارگر زن چند روز است؟",
            "type": "rag"
        },
        {
            "query": "سلام، اسمت چیه؟",
            "type": "conversational"
        },
        {
            "query": "آب و هوای تهران چطوره؟",
            "type": "out_of_scope"
        },
    ]

    # ==================== Execution Loop ====================
    for i, case in enumerate( test_queries, start=1 ):
        query, expected_type = case[ "query" ], case[ "type" ]

        log_message( LG.LLM, f"\n{'='*70}\n📝 Query #{i}: '{query}'\n{'='*70}", LogLevel.INFO )

        try:
            # ‫مرحله ۱: RRF
            chunks = retriever.retrieve( query )

            # ‫مرحله ۲: fetch content از PostgreSQL
            db = SessionLocal()
            pg_manager = PostgresManager( db )
            chunk_ids = [ c[ 'chunk_id' ] for c in chunks ]
            contents_map = pg_manager.get_chunks_content_bulk( chunk_ids )
            for c in chunks:
                c[ 'content' ] = contents_map.get( c[ 'chunk_id' ], "" )

            # ‫مرحله ۳: Rerank
            chunks = chunks[ :settings.RERANKER_INPUT_SIZE ]
            chunks = retriever.rerank( query, chunks, final_top_k=settings.RERANKER_TOP_K )
            db.close()

            _log_chunks_summary( chunks )

            # ‫مرحله ۴: LLM Generation
            response = orchestrator.generate_answer(
                query=query,
                chunks=chunks,
                intent=QueryIntent.RAG if expected_type == "rag" else QueryIntent.OUT_OF_SCOPE,
                temperature=0.3,
            )

            _log_result_summary( expected_type, response )

        except Exception as e:
            log_message( LG.LLM, f"❌ Critical Error: {e}", LogLevel.ERROR )
            import traceback
            log_message( LG.LLM, traceback.format_exc(), LogLevel.ERROR )

    log_message( LG.LLM, "\n🎉 تست RAG Pipeline تکمیل شد", LogLevel.INFO )


if __name__ == "__main__":
    test_rag_pipeline()
