import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent ) )

from backend.app.services.llm.llm_orchestrator import create_llm_orchestrator
from backend.app.services.retrieval.hybrid_retriever import create_hybrid_retriever
from backend.app.utils.logging_config import log_message, LG, LogLevel


def test_rag_pipeline():
    """
    تست کامل سیستم RAG:
    1. Retrieval (Hybrid)
    2. LLM Generation (Groq + Gemini fallback)
    """

    log_message( LG.LLM, "=" * 70, LogLevel.INFO )
    log_message( LG.LLM, "🧪 شروع تست RAG Pipeline (End-to-End)", LogLevel.INFO )
    log_message( LG.LLM, "=" * 70, LogLevel.INFO )

    # ==================== Setup ====================
    try:
        # 1. Retriever
        log_message( LG.LLM, "📚 مرحله 1: ساخت Retriever...", LogLevel.INFO )
        retriever = create_hybrid_retriever( bm25_top_k=20, vector_top_k=20, final_top_k=5 )
        log_message( LG.LLM, "✅ Retriever آماده شد", LogLevel.INFO )

        # 2. LLM Orchestrator
        log_message( LG.LLM, "🤖 مرحله 2: ساخت LLM Orchestrator...", LogLevel.INFO )
        llm = create_llm_orchestrator( temperature=0.3, max_context_length=4000 )
        log_message( LG.LLM, "✅ LLM Orchestrator آماده شد", LogLevel.INFO )

    except Exception as e:
        log_message( LG.LLM, f"❌ خطا در Setup: {str(e)}", LogLevel.ERROR )
        return

    # ==================== Test Queries ====================
    test_queries = [
        "انقلاب اسلامی چه تأثیری بر نظریه های غربی گذاشت؟",
        "تعریف نظام سیاسی چیست؟",
        "نقش امام خمینی در انقلاب چه بود؟",
    ]

    for i, query in enumerate( test_queries, start=1 ):
        log_message( LG.LLM, "\n" + "=" * 70, LogLevel.INFO )
        log_message( LG.LLM, f"📝 Query #{i}: '{query}'", LogLevel.INFO )
        log_message( LG.LLM, "=" * 70, LogLevel.INFO )

        try:
            # ==================== Retrieval ====================
            log_message( LG.LLM, "🔍 مرحله A: Retrieval...", LogLevel.INFO )
            chunks = retriever.retrieve( query, final_top_k=5 )

            if not chunks:
                log_message( LG.LLM, "⚠️ هیچ chunk ای پیدا نشد - رد شدن", LogLevel.WARNING )
                continue

            log_message( LG.LLM, f"✅ {len(chunks)} chunk بازیابی شد", LogLevel.INFO )

            # نمایش Top-3 chunks
            log_message( LG.LLM, "\n📚 Top-3 Retrieved Chunks:", LogLevel.INFO )
            for rank, chunk in enumerate( chunks[ :3 ], start=1 ):
                chunk_preview = chunk.get( "content", "" )[ :100 ] + "..."
                log_message(
                    LG.LLM,
                    f"  {rank}. {chunk['chunk_id']} (RRF: {chunk['rrf_score']:.4f})",
                    LogLevel.DEBUG,
                )
                log_message( LG.LLM, f"     Preview: {chunk_preview}", LogLevel.DEBUG )

            # ==================== LLM Generation ====================
            log_message( LG.LLM, "\n🤖 مرحله B: تولید پاسخ با LLM...", LogLevel.INFO )

            result = llm.generate_answer( query, chunks )

            if not result[ "success" ]:
                log_message(
                    LG.LLM,
                    f"❌ خطا در تولید پاسخ: {result.get('error')}",
                    LogLevel.ERROR,
                )
                continue

            # ==================== نمایش نتیجه ====================
            log_message( LG.LLM, "\n" + "=" * 70, LogLevel.INFO )
            log_message( LG.LLM, "✅ پاسخ تولید شد!", LogLevel.INFO )
            log_message( LG.LLM, "=" * 70, LogLevel.INFO )

            # اطلاعات provider
            provider = result[ "provider" ]
            model = result[ "model" ]
            usage = result.get( "usage", {} )

            log_message( LG.LLM, f"🤖 Provider: {provider.upper()}", LogLevel.INFO )
            log_message( LG.LLM, f"📦 Model: {model}", LogLevel.INFO )
            log_message(
                LG.LLM,
                f"📊 Usage: {usage.get('total_tokens', 'N/A')} tokens",
                LogLevel.INFO,
            )
            log_message( LG.LLM, f"📚 Chunks Used: {result['chunks_used']}", LogLevel.INFO )

            # پاسخ نهایی
            answer = result[ "answer" ]
            log_message( LG.LLM, "\n📄 پاسخ نهایی:", LogLevel.INFO )
            log_message( LG.LLM, "-" * 70, LogLevel.INFO )
            log_message( LG.LLM, answer, LogLevel.INFO )
            log_message( LG.LLM, "-" * 70, LogLevel.INFO )

        except Exception as e:
            log_message( LG.LLM, f"❌ خطا در پردازش query: {str(e)}", LogLevel.ERROR )
            continue

    # ==================== خلاصه ====================
    log_message( LG.LLM, "\n" + "=" * 70, LogLevel.INFO )
    log_message( LG.LLM, "🎉 تست RAG Pipeline تکمیل شد", LogLevel.INFO )
    log_message( LG.LLM, "=" * 70, LogLevel.INFO )


if __name__ == "__main__":
    test_rag_pipeline()
