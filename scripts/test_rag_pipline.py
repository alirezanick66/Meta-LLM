"""
تست کامل RAG Pipeline (End-to-End)
شامل: Retrieval + LLM Generation
"""

import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent ) )

from backend.app.services.retrieval.hybrid_retriever import create_hybrid_retriever
from backend.app.services.llm.llm_orchestrator import create_llm_orchestrator, LLMResponse
from backend.app.utils.logging_config import log_message, LG, LogLevel


def test_rag_pipeline():
    """
    تست کامل سیستم RAG:
    1. Retrieval (Hybrid BM25 + Vector + RRF)
    2. Prompt Building (با tokenizer + metadata)
    3. LLM Generation (Groq → Gemini fallback)
    """

    log_message( LG.LLM, "=" * 70, LogLevel.INFO )
    log_message( LG.LLM, "🧪 شروع تست RAG Pipeline (End-to-End)", LogLevel.INFO )
    log_message( LG.LLM, "=" * 70, LogLevel.INFO )

    # ==================== Setup ====================
    try:
        # 1️⃣ Retriever
        log_message( LG.LLM, "\n📚 مرحله 1: ساخت Hybrid Retriever...", LogLevel.INFO )
        retriever = create_hybrid_retriever(
            bm25_top_k=20,
            vector_top_k=20,
            final_top_k=5,          # فقط 5 تا برتر
        )
        log_message( LG.LLM, "✅ Retriever آماده شد", LogLevel.INFO )

        # 2️⃣ LLM Orchestrator
        log_message( LG.LLM, "\n🤖 مرحله 2: ساخت LLM Orchestrator...", LogLevel.INFO )
        orchestrator = create_llm_orchestrator(
            temperature=0.3,
            max_context_tokens=3000,
            use_fallback=True,          # فعال کردن Gemini fallback
        )
        log_message( LG.LLM, "✅ LLM Orchestrator آماده شد", LogLevel.INFO )

    except Exception as e:
        log_message( LG.LLM, f"❌ خطا در Setup: {str(e)}", LogLevel.ERROR )
        return

    # ==================== Test Queries ====================
    test_queries = [
          # سوالات عادی (RAG)
        {
            "query": "انقلاب اسلامی چه تأثیری بر نظریه های غربی گذاشت؟",
            "type": "rag",
        },
        {
            "query": "نقش امام خمینی در انقلاب چه بود؟",
            "type": "rag",
        },
          # سوال سیستمی (بدون RAG)
        {
            "query": "تو کی هستی؟",
            "type": "system",
        },
          # سوال با سلام (سیستمی)
        {
            "query": "سلام، اسمت چیه؟",
            "type": "system",
        },
    ]

    for i, test_case in enumerate( test_queries, start=1 ):
        query = test_case[ "query" ]
        expected_type = test_case[ "type" ]

        log_message( LG.LLM, "\n" + "=" * 70, LogLevel.INFO )
        log_message( LG.LLM, f"📝 Query #{i}: '{query}'", LogLevel.INFO )
        log_message( LG.LLM, f"   Expected Type: {expected_type}", LogLevel.INFO )
        log_message( LG.LLM, "=" * 70, LogLevel.INFO )

        try:
            # ==================== Retrieval ====================
            log_message( LG.LLM, "\n🔍 مرحله A: Retrieval...", LogLevel.INFO )
            chunks = retriever.retrieve( query, final_top_k=5 )

            if not chunks:
                log_message(
                    LG.LLM,
                    "⚠️ هیچ chunk ای پیدا نشد - ادامه با chunks خالی",
                    LogLevel.WARNING,
                )
                chunks = []
            else:
                log_message( LG.LLM, f"✅ {len(chunks)} chunk بازیابی شد", LogLevel.INFO )

                # نمایش Top-3 chunks
                log_message( LG.LLM, "\n📚 Top-3 Retrieved Chunks:", LogLevel.INFO )
                for rank, chunk in enumerate( chunks[ :3 ], start=1 ):
                    chunk_id = chunk.get( "chunk_id", "unknown" )
                    rrf_score = chunk.get( "rrf_score", 0 )
                    content_preview = chunk.get( "content", "" )[ :80 ] + "..."

                    log_message(
                        LG.LLM,
                        f"  #{rank}. {chunk_id} (RRF: {rrf_score:.4f})",
                        LogLevel.DEBUG,
                    )
                    log_message( LG.LLM, f"      Preview: {content_preview}", LogLevel.DEBUG )

            # ==================== LLM Generation ====================
            log_message( LG.LLM, "\n🤖 مرحله B: تولید پاسخ با LLM...", LogLevel.INFO )

            response: LLMResponse = orchestrator.generate_answer(
                query=query,
                chunks=chunks,
                temperature=0.3,
                include_metadata=True,
            )

            if not response.success:
                log_message( LG.LLM, f"❌ خطا در تولید پاسخ: {response.error}", LogLevel.ERROR )
                continue

            # ==================== نمایش نتیجه ====================
            log_message( LG.LLM, "\n" + "=" * 70, LogLevel.INFO )
            log_message( LG.LLM, "✅ پاسخ تولید شد!", LogLevel.INFO )
            log_message( LG.LLM, "=" * 70, LogLevel.INFO )

            # اطلاعات Provider
            log_message( LG.LLM, f"🤖 Provider: {response.provider.upper() if response.provider else 'Unknown'}", LogLevel.INFO )
            log_message( LG.LLM, f"📦 Model: {response.model}", LogLevel.INFO )

            # Usage
            usage = response.usage
            if usage:
                log_message(
                    LG.LLM, f"📊 Usage: Prompt={usage.get('prompt_tokens', 0)}, "
                    f"Completion={usage.get('completion_tokens', 0)}, "
                    f"Total={usage.get('total_tokens', 0)}", LogLevel.INFO )

            # Metadata جدید
            log_message( LG.LLM, f"🔢 Prompt Tokens (Pre-calculated): {response.prompt_tokens}", LogLevel.INFO )
            log_message( LG.LLM, f"📚 Sources Used: {len(response.sources) if response.sources else 0}", LogLevel.INFO )
            log_message( LG.LLM, f"🤔 Is System Question: {response.is_system_question}", LogLevel.INFO )

            # بررسی انتظار vs واقعیت
            if expected_type == "system" and response.is_system_question:
                log_message( LG.LLM, "✅ تشخیص صحیح: سوال سیستمی", LogLevel.INFO )
            elif expected_type == "rag" and not response.is_system_question:
                log_message( LG.LLM, "✅ تشخیص صحیح: سوال RAG", LogLevel.INFO )
            else:
                log_message(
                    LG.LLM, f"⚠️ تشخیص نادرست! Expected={expected_type}, Got={'system' if response.is_system_question else 'rag'}",
                    LogLevel.WARNING )

            # نمایش منابع (اگه RAG بود)
            if response.sources and not response.is_system_question:
                log_message( LG.LLM, "\n📑 منابع استفاده شده:", LogLevel.INFO )
                for source in response.sources[ :3 ]:          # فقط 3 تا اول
                    log_message( LG.LLM, f"  • منبع {source['index']}: {source['hierarchy'][:60]}...", LogLevel.INFO )

            # پاسخ نهایی
            log_message( LG.LLM, "\n📄 پاسخ نهایی:", LogLevel.INFO )
            log_message( LG.LLM, "-" * 70, LogLevel.INFO )
            # محدود کردن پاسخ برای خوانایی بهتر لاگ
            if response.answer:
                answer_preview = ( response.answer[ :300 ] + "..." if len( response.answer ) > 300 else response.answer )
                log_message( LG.LLM, answer_preview, LogLevel.INFO )
            else:
                log_message( LG.LLM, "⚠️ پاسخی دریافت نشد", LogLevel.WARNING )
            log_message( LG.LLM, "-" * 70, LogLevel.INFO )

        except Exception as e:
            log_message( LG.LLM, f"❌ خطا در پردازش query: {str(e)}", LogLevel.ERROR )
            import traceback

            log_message( LG.LLM, traceback.format_exc(), LogLevel.ERROR )
            continue

    # ==================== خلاصه ====================
    log_message( LG.LLM, "\n" + "=" * 70, LogLevel.INFO )
    log_message( LG.LLM, "🎉 تست RAG Pipeline تکمیل شد", LogLevel.INFO )
    log_message( LG.LLM, "=" * 70, LogLevel.INFO )


if __name__ == "__main__":
    test_rag_pipeline()
