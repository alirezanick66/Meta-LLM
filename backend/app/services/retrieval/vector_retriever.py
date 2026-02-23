from typing import List, Dict, Any, Optional
from backend.app.services.vector.qdrant_client import QdrantManager
from backend.app.services.embedding.embedding_service import EmbeddingService
from backend.app.utils.custom_normalizer import persian_normalizer
from backend.app.utils.logging_config import log_message, LG, LogLevel


class ResultKeys:
    CHUNK_ID = "chunk_id"
    SCORE = "score"
    RETRIEVAL_METHOD = "retrieval_method"
    METADATA = "metadata"
    CONTENT = "content"          # برای استفاده در BM25 و LLM Pipeline


class VectorRetriever:
    """
    جستجوی Semantic با استفاده از Vector Embeddings در Qdrant
    
    ویژگی‌های جدید:
    - Score threshold برای فیلتر کردن نتایج بی‌ربط
    - بهینه‌سازی با list comprehension
    
    فرآیند:
    1. دریافت query از کاربر
    2. نرمال‌سازی query
    3. تبدیل query به embedding
    4. جستجو در Qdrant با cosine similarity
    5. فیلتر بر اساس score_threshold
    6. بازگشت Top-K نتایج
    """

    def __init__(
        self,
        qdrant_manager: QdrantManager,
        embedding_service: EmbeddingService,
        top_k: int = 20,
        score_threshold: float = 0.5,
    ):
        """
        Args:
            qdrant_manager: instance از QdrantManager
            embedding_service: instance از EmbeddingService
            top_k: تعداد نتایج برتر (default: 20)
            score_threshold: حداقل score برای قبول نتیجه (0-1، default: 0.5)
                           - 0.7+: خیلی مرتبط
                           - 0.5-0.7: نسبتاً مرتبط
                           - <0.5: احتمالاً نامربوط
        """
        self.qdrant = qdrant_manager
        self.embedding_service = embedding_service
        self.normalizer = persian_normalizer
        self.top_k = top_k
        self.score_threshold = score_threshold

        log_message(
            LG.Retrieval,
            f"VectorRetriever آماده شد (top_k: {top_k}, threshold: {score_threshold})",
            LogLevel.INFO,
        )

    def retrieve( self,
                  query: str,
                  top_k: Optional[ int ] = None,
                  score_threshold: Optional[ float ] = None,
                  document_id: Optional[ int ] = None ) -> List[ Dict[ str, Any ] ]:
        """
        جستجوی semantic با vector embedding
        
        Args:
            query: متن جستجوی کاربر
            top_k: تعداد نتایج (اختیاری، default از __init__)
            score_threshold: حداقل score (اختیاری، default از __init__)
            document_id: فیلتر بر اساس document_id (اختیاری)
            
        Returns:
            لیست نتایج با فرمت:
            [
                {
                    ResultKeys.CHUNK_ID: str,
                    ResultKeys.SCORE: float,
                    ResultKeys.RETRIEVAL_METHOD: 'vector',
                    ResultKeys.METADATA: dict
                },
                ...
            ]
        """
        try:
            if not query or not query.strip():
                log_message( LG.Retrieval, "Query خالی است", LogLevel.WARNING )
                return []

            k = top_k if top_k is not None else self.top_k
            threshold = ( score_threshold if score_threshold is not None else self.score_threshold )

            log_message(
                LG.Retrieval,
                f"🔍 Vector retrieval: query='{query[:50]}...', top_k={k}, threshold={threshold}",
                LogLevel.INFO,
            )

            # 1. نرمال‌سازی query
            normalized_query = self.normalizer.normalize( query )
            log_message(
                LG.Retrieval,
                f"Query نرمال شد: '{normalized_query[:50]}...'",
                LogLevel.DEBUG,
            )

            # 2. تبدیل query به embedding
            query_embedding = self.embedding_service.embed_single( normalized_query, normalize=True )

            if query_embedding is None or len( query_embedding ) == 0:
                log_message( LG.Retrieval, "❌ خطا در ساخت embedding", LogLevel.ERROR )
                return []

            log_message(
                LG.Retrieval,
                f"✅ Query embedding ساخته شد (dim: {len(query_embedding)})",
                LogLevel.DEBUG,
            )

            # 3. جستجو در Qdrant
            qdrant_results = self.qdrant.search_vectors(
                query_vector=query_embedding.tolist(),
                top_k=k,
                document_id=document_id,
            )

            if not qdrant_results:
                log_message( LG.Retrieval, "⚠️ هیچ نتیجه‌ای از Qdrant بازنگشت", LogLevel.WARNING )
                return []

            # 4. فیلتر و فرمت کردن نتایج (با list comprehension)
            formatted_results = [
                {
                    ResultKeys.CHUNK_ID: result[ ResultKeys.CHUNK_ID ],
                    ResultKeys.SCORE: float( result[ ResultKeys.SCORE ] ),
                    ResultKeys.RETRIEVAL_METHOD: "vector",
                    ResultKeys.METADATA: result.get( ResultKeys.METADATA, {} ),
                } for result in qdrant_results if result[ ResultKeys.SCORE ] >= threshold          # فیلتر بر اساس threshold
            ]

            # لاگ تعداد نتایج فیلتر شده
            filtered_count = len( qdrant_results ) - len( formatted_results )
            if filtered_count > 0:
                log_message(
                    LG.Retrieval,
                    f"⚠️ {filtered_count} نتیجه به دلیل score < {threshold} فیلتر شد",
                    LogLevel.INFO,
                )

            log_message(
                LG.Retrieval,
                f"✅ {len(formatted_results)} نتیجه معتبر از vector search",
                LogLevel.INFO,
            )

            return formatted_results

        except Exception as e:
            log_message( LG.Retrieval, f"❌ خطا در vector retrieval: {str(e)}", LogLevel.ERROR )
            return []

    def get_stats( self ) -> Dict[ str, Any ]:
        """آمار VectorRetriever"""
        return {
            "method": "vector",
            "top_k": self.top_k,
            "score_threshold": self.score_threshold,
            "qdrant_collection": self.qdrant.collection_name,
            "embedding_dim": self.embedding_service.get_embedding_dimension(),
        }
