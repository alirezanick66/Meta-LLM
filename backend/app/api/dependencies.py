"""
‫‫ Dependency Injection برای سرویس‌های سنگین
‫ همه singleton ها اینجا با @lru_cache مدیریت میشن
"""

from functools import lru_cache

from backend.app.services.retrieval.hybrid_retriever import HybridRetriever
from backend.app.services.retrieval.reranker_service import RerankerService
from backend.app.services.llm.llm_orchestrator import create_llm_orchestrator, LLMOrchestrator
from backend.app.services.llm.intent_detector import IntentDetector, create_intent_detector
from backend.app.services.embedding.embedding_service import EmbeddingService
from backend.app.services.embedding.tokenizer_service import TokenizerService
from backend.app.services.retrieval.vector_retriever import VectorRetriever
from backend.app.services.vector.qdrant_client import QdrantManager
from backend.app.services.retrieval.bm25_indexer import BM25Indexer
from backend.app.services.vector.qdrant_indexer import QdrantIndexer
from backend.app.core.config import settings
from backend.app.utils.logging_config import log_message, LG, LogLevel

# ==================== Singletons ====================


@lru_cache( maxsize=1 )
def get_embedding_service() -> EmbeddingService:
    """‫ Singleton instance از EmbeddingService"""
    log_message( LG.API, "🔧 ساخت EmbeddingService instance (Singleton)", LogLevel.INFO )
    return EmbeddingService()


@lru_cache( maxsize=1 )
def get_tokenizer_service() -> TokenizerService:
    """‫ Singleton instance از  ‫TokenizerService"""
    log_message( LG.API, "🔧 ساخت TokenizerService instance (Singleton)", LogLevel.INFO )
    return TokenizerService()


@lru_cache( maxsize=1 )
def get_qdrant_manager() -> QdrantManager:
    """‫ Singleton instance از QdrantManager"""
    log_message( LG.API, "‫ساخت QdrantManager instance (Singleton)", LogLevel.INFO )
    return QdrantManager()


@lru_cache( maxsize=1 )
def get_bm25_indexer() -> BM25Indexer:
    """‫ Singleton instance از BM25Indexer"""
    log_message( LG.API, "🔧 ساخت BM25Indexer instance (Singleton)", LogLevel.INFO )
    return BM25Indexer()


@lru_cache( maxsize=1 )
def get_qdrant_indexer() -> QdrantIndexer:
    """‫ Singleton instance از QdrantIndexer"""
    log_message( LG.API, "🔧 ساخت QdrantIndexer instance (Singleton)", LogLevel.INFO )
    return QdrantIndexer( qdrant_manager=get_qdrant_manager() )


@lru_cache( maxsize=1 )
def get_intent_detector() -> IntentDetector:
    """‫Singleton instance از IntentDetector"""
    log_message( LG.API, "🔧 ساخت IntentDetector instance (Singleton)", LogLevel.INFO )
    return create_intent_detector()


# ‫این singleton اضافه میشه (قبل از get_hybrid_retriever):
@lru_cache( maxsize=1 )
def get_reranker_service() -> RerankerService:
    """‫Singleton instance از RerankerService"""
    log_message( LG.API, "🔧 ساخت RerankerService instance (Singleton)", LogLevel.INFO )
    return RerankerService()


@lru_cache( maxsize=1 )
def get_hybrid_retriever() -> HybridRetriever:
    """ ‫‫ Singleton instance از HybridRetriever"""
    log_message( LG.API, "🔧 ساخت HybridRetriever instance (Singleton)", LogLevel.INFO )

    return HybridRetriever(
        bm25_indexer=get_bm25_indexer(),
        vector_retriever=VectorRetriever(
            qdrant_manager=get_qdrant_manager(),
            embedding_service=get_embedding_service(),
            top_k=settings.VECTOR_TOP_K,
        ),
        reranker_service=get_reranker_service(),
        bm25_top_k=settings.BM25_TOP_K,
        vector_top_k=settings.VECTOR_TOP_K,
        rrf_top_k=settings.RRF_TOP_K,
        final_top_k=settings.RERANKER_TOP_K,
    )


@lru_cache( maxsize=1 )
def get_llm_orchestrator() -> LLMOrchestrator:
    """‫ Singleton instance از LLMOrchestrator"""
    log_message( LG.API, "🔧 ساخت LLMOrchestrator instance (Singleton)", LogLevel.INFO )
    return create_llm_orchestrator( tokenizer_service=get_tokenizer_service(), use_fallback=True )


# ==================== Helper ====================


def clear_singletons() -> None:
    """ ‫‫ پاک کردن همه cache ها (برای testing یا restart)"""
    get_embedding_service.cache_clear()
    get_tokenizer_service.cache_clear()
    get_qdrant_manager.cache_clear()
    get_bm25_indexer.cache_clear()
    get_qdrant_indexer.cache_clear()
    get_intent_detector.cache_clear()
    get_hybrid_retriever.cache_clear()
    get_reranker_service.cache_clear()
    get_llm_orchestrator.cache_clear()
    log_message( LG.API, "🧹 همه Singleton cache ها پاک شدن", LogLevel.INFO )
