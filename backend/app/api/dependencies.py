"""
Dependency Injection برای سرویس‌های سنگین
این سرویس‌ها یکبار ساخته میشن و برای همه requests استفاده میشن
"""

from functools import lru_cache
from backend.app.services.retrieval.hybrid_retriever import create_hybrid_retriever, HybridRetriever
from backend.app.services.llm.llm_orchestrator import create_llm_orchestrator, LLMOrchestrator
from backend.app.core.config import settings
from backend.app.utils.logging_config import log_message, LG, LogLevel

# ==================== Singleton Instances ====================


@lru_cache( maxsize=1 )
def get_hybrid_retriever() -> HybridRetriever:
    """
    Singleton instance از HybridRetriever
    فقط یکبار ساخته میشه و cache میشه
    """
    log_message( LG.API, "🔧 ساخت HybridRetriever instance (Singleton)", LogLevel.INFO )

    return create_hybrid_retriever( bm25_top_k=settings.BM25_TOP_K,
                                    vector_top_k=settings.VECTOR_TOP_K,
                                    final_top_k=settings.RERANKER_TOP_K,
                                    use_parallel=True )


@lru_cache( maxsize=1 )
def get_llm_orchestrator() -> LLMOrchestrator:
    """
    Singleton instance از LLMOrchestrator
    فقط یکبار ساخته میشه و cache میشه
    """
    log_message( LG.API, "🔧 ساخت LLMOrchestrator instance (Singleton)", LogLevel.INFO )

    return create_llm_orchestrator( max_context_tokens=3000, use_fallback=True )


# ==================== Helper Function ====================


def clear_singletons():
    """
    پاک کردن cache (برای testing یا restart)
    """
    get_hybrid_retriever.cache_clear()
    get_llm_orchestrator.cache_clear()
    log_message( LG.API, "🧹 Singleton cache cleared", LogLevel.INFO )
