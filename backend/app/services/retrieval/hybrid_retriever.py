from typing import List, Dict, Any, Optional
from collections import defaultdict
from backend.app.schemas.retrieval_schemas import ResultKeys, RetrievalMethod, RRFKeys, RRFStats
from backend.app.services.retrieval.bm25_indexer import BM25Indexer
from backend.app.services.retrieval.vector_retriever import VectorRetriever
from backend.app.services.retrieval.reranker_service import RerankerService
from backend.app.utils.logging_config import log_message, LG, LogLevel
import time
from concurrent.futures import ThreadPoolExecutor


class HybridRetriever:
    """
   ‫ ترکیب BM25 + Vector با RRF و Reranking
    ‫جریان:
    BM25(top_k) + Vector(top_k) → RRF(rrf_top_k) → Reranker → final_top_k
    """

    def __init__(
        self,
        bm25_indexer: BM25Indexer,
        vector_retriever: VectorRetriever,
        reranker_service: RerankerService,
        bm25_top_k: int = 20,
        vector_top_k: int = 20,
        rrf_top_k: int = 20,
        final_top_k: int = 20,
        rrf_k: int = 60,
    ):
        """
        Args:
            ‫bm25_indexer:‫ instance از BM25Indexer
            ‫vector_retriever:‫ instance از VectorRetriever
            ‫bm25_top_k: ‫تعداد نتایج BM25
            ‫vector_top_k: ‫تعداد نتایج Vector
            ‫rrf_top_k: ‫تعداد نتایج بعد از RRF
            ‫final_top_k: ‫تعداد نتایج نهایی بعد از Reranking
            ‫rrf_k: ‫ثابت RRF (معمولاً 60)
        """
        self.bm25_indexer = bm25_indexer
        self.vector_retriever = vector_retriever
        self.reranker_service = reranker_service
        self.bm25_top_k = bm25_top_k
        self.vector_top_k = vector_top_k
        self.rrf_top_k = rrf_top_k
        self.final_top_k = final_top_k
        self.rrf_k = rrf_k

        log_message( LG.Retrieval, "HybridRetriever آماده شد", LogLevel.INFO )
        log_message( LG.Retrieval, f"  - BM25 Top-K: {bm25_top_k}, Vector Top-K: {vector_top_k}, - RRF k={rrf_k}", LogLevel.DEBUG )

    def retrieve( self, query: str, final_top_k: int | None = None ) -> List[ Dict[ str, Any ] ]:
        """‫جستجوی Hybrid: BM25 + Vector → RRF (بدون Rerank)"""
        try:
            if not query or not query.strip():
                log_message( LG.Retrieval, "Query خالی است", LogLevel.WARNING )
                return []

            log_message( LG.Retrieval, f"🔍 Hybrid Retrieval: '{query[:50]}...'", LogLevel.INFO )

            bm25_results, vector_results = self._retrieve_parallel( query )

            log_message( LG.Retrieval, "🔀 مرحله ۲: Reciprocal Rank Fusion...", LogLevel.INFO )
            rrf_results = self._apply_rrf( bm25_results, vector_results )[ :self.rrf_top_k ]

            log_message( LG.Retrieval, f"✅ RRF تکمیل شد - {len(rrf_results)} نتیجه", LogLevel.INFO )
            return rrf_results

        except Exception as e:
            log_message( LG.Retrieval, f"❌ خطا در hybrid retrieval: {str(e)}", LogLevel.ERROR )
            return []

    def rerank( self, query: str, chunks: List[ Dict[ str, Any ] ], final_top_k: int | None = None ) -> List[ Dict[ str, Any ] ]:
        """‫Reranking chunks که content شان از PostgreSQL تکمیل شده"""
        try:
            top_k = final_top_k if final_top_k is not None else self.final_top_k
            log_message( LG.Retrieval, f"🎯 Reranking {len(chunks)} chunk...", LogLevel.INFO )
            final_results = self.reranker_service.rerank( query, chunks, top_k )
            log_message( LG.Retrieval, f"✅ Hybrid Retrieval تکمیل شد - {len(final_results)} نتیجه نهایی", LogLevel.INFO )
            return final_results
        except Exception as e:
            log_message( LG.Retrieval, f"❌ خطا در reranking: {str(e)}", LogLevel.ERROR )
            return chunks[ :self.final_top_k ]

    def _retrieve_parallel( self, query: str ) -> tuple[ List[ Dict[ str, Any ] ], List[ Dict[ str, Any ] ] ]:
        """
       ‫ اجرای موازی BM25 و Vector با ThreadPoolExecutor
        
        نکته‫: از concurrent.futures استفاده می‌کنیم چون:
        - ‫عملیات I/O bound هستن
        - ‫asyncio نیاز به تغییرات گسترده داره
        - ‫ThreadPool برای الان کافیه
        """

        log_message( LG.Retrieval, "⚡ اجرای موازی BM25 و Vector...", LogLevel.INFO )

        start_time = time.time()

        with ThreadPoolExecutor( max_workers=2 ) as executor:
            #‫ Submit کردن هر دو task
            future_bm25 = executor.submit( self.bm25_indexer.search, query, self.bm25_top_k )
            future_vector = executor.submit( self.vector_retriever.retrieve, query, self.vector_top_k )

            # دریافت نتایج
            bm25_results = future_bm25.result()
            vector_results = future_vector.result()

        elapsed = time.time() - start_time

        log_message( LG.Retrieval, f"  ✅ BM25: {len(bm25_results)} نتیجه", LogLevel.INFO )
        log_message( LG.Retrieval, f"  ✅ Vector: {len(vector_results)} نتیجه", LogLevel.INFO )
        log_message( LG.Retrieval, f"  ⚡ زمان کل: {elapsed:.2f}s (موازی)", LogLevel.DEBUG )

        return bm25_results, vector_results

    def _apply_rrf( self, bm25_results: List[ Dict[ str, Any ] ], vector_results: List[ Dict[ str,
                                                                                              Any ] ] ) -> List[ Dict[ str, Any ] ]:
        """
       ‫ اعمال Reciprocal Rank Fusion استاندارد (بدون وزن‌دهی)
        
        فرمول RRF:
        score(doc) = Σ (1 / (k + rank_i))
        
        Args:
            bm25_results: نتایج BM25
            vector_results: نتایج Vector
            
        Returns:
           ‫ لیست merged و sorted بر اساس RRF score
        """
        #‫ ذخیره اطلاعات هر chunk
        chunk_data: Dict[ str, Dict[ str, Any ] ] = defaultdict(
            lambda: {
                ResultKeys.CHUNK_ID: None,
                RRFKeys.BM25_SCORE: None,
                RRFKeys.VECTOR_SCORE: None,
                RRFKeys.BM25_RANK: None,
                RRFKeys.VECTOR_RANK: None,
                ResultKeys.RETRIEVAL_METHOD: list(),
                ResultKeys.METADATA: {},
                RRFKeys.RRF_SCORE: 0.0,
            } )

        # ‫پردازش نتایج BM25
        for rank, result in enumerate( bm25_results, start=1 ):
            chunk_id = result[ ResultKeys.CHUNK_ID ]
            chunk = chunk_data[ chunk_id ]          # ‫یه بار reference میگیریم
            chunk[ ResultKeys.CHUNK_ID ] = chunk_id
            chunk[ RRFKeys.BM25_SCORE ] = result[ ResultKeys.SCORE ]
            chunk[ RRFKeys.BM25_RANK ] = rank
            chunk[ RRFKeys.RRF_SCORE ] += 1.0 / ( self.rrf_k + rank )
            chunk[ ResultKeys.RETRIEVAL_METHOD ].append( RetrievalMethod.BM25 )
            chunk[ ResultKeys.METADATA ] = result.get( ResultKeys.METADATA, {} )

        # ‫پردازش نتایج Vector
        for rank, result in enumerate( vector_results, start=1 ):
            chunk_id = result[ ResultKeys.CHUNK_ID ]
            chunk = chunk_data[ chunk_id ]          # ‫یه بار reference میگیریم
            chunk[ ResultKeys.CHUNK_ID ] = chunk_id
            chunk[ RRFKeys.VECTOR_SCORE ] = result[ ResultKeys.SCORE ]
            chunk[ RRFKeys.VECTOR_RANK ] = rank

            if RetrievalMethod.VECTOR not in chunk[ ResultKeys.RETRIEVAL_METHOD ]:
                chunk[ ResultKeys.RETRIEVAL_METHOD ].append( RetrievalMethod.VECTOR )

            if not chunk[ ResultKeys.METADATA ]:
                chunk[ ResultKeys.METADATA ] = result.get( ResultKeys.METADATA, {} )

            chunk[ RRFKeys.RRF_SCORE ] += 1.0 / ( self.rrf_k + rank )

        # تبدیل به لیست و مرتب‌سازی
        merged_results = sorted( chunk_data.values(), key=lambda x: x[ RRFKeys.RRF_SCORE ], reverse=True )

        stats = { RRFStats.BOTH: 0, RRFStats.ONLY_BM25: 0, RRFStats.ONLY_VECTOR: 0 }
        for r in merged_results:
            methods = r[ ResultKeys.RETRIEVAL_METHOD ]
            if len( methods ) == 2:
                stats[ RRFStats.BOTH ] += 1
            elif methods == [ RetrievalMethod.BM25 ]:
                stats[ RRFStats.ONLY_BM25 ] += 1
            else:
                stats[ RRFStats.ONLY_VECTOR ] += 1

        log_message( LG.Retrieval, f"  📊 RRF Stats:", LogLevel.INFO )
        log_message( LG.Retrieval, f"     Both Methods: {stats[RRFStats.BOTH]}", LogLevel.INFO )
        log_message( LG.Retrieval, f"     Only BM25: {stats[RRFStats.ONLY_BM25]}", LogLevel.INFO )
        log_message( LG.Retrieval, f"     Only Vector: {stats[RRFStats.ONLY_VECTOR]}", LogLevel.INFO )

        return merged_results
