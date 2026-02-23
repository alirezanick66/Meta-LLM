from typing import List, Dict, Any, Optional
from collections import defaultdict
from backend.app.services.retrieval.bm25_indexer import BM25Indexer
from backend.app.services.retrieval.vector_retriever import VectorRetriever, ResultKeys
from backend.app.utils.logging_config import log_message, LG, LogLevel
import time
from concurrent.futures import ThreadPoolExecutor


class HybridRetriever:
    """
    ترکیب BM25 (keyword) و Vector (semantic) retrieval با Reciprocal Rank Fusion (RRF)
    
    ویژگی‌های جدید:
    - اجرای موازی BM25 و Vector (با concurrent.futures)
    - RRF استاندارد بدون double weighting
    - Score threshold برای هر دو روش
    
    RRF Formula (استاندارد):
    score(doc) = Σ (1 / (k + rank_i))
    
    که در آن:
    - k: ثابت (معمولاً 60)
    - rank_i: رتبه document در هر retriever
    """

    def __init__(
        self,
        bm25_indexer: BM25Indexer,
        vector_retriever: VectorRetriever,
        bm25_top_k: int = 20,
        vector_top_k: int = 20,
        final_top_k: int = 20,
        rrf_k: int = 60,
        use_parallel: bool = True,
    ):
        """
        Args:
            bm25_indexer: instance از BM25Indexer
            vector_retriever: instance از VectorRetriever
            bm25_top_k: تعداد نتایج BM25
            vector_top_k: تعداد نتایج Vector
            final_top_k: تعداد نتایج نهایی بعد از RRF
            rrf_k: ثابت RRF (معمولاً 60)
            use_parallel: اجرای موازی BM25 و Vector (default: True)
        """
        self.bm25_indexer = bm25_indexer
        self.vector_retriever = vector_retriever
        self.bm25_top_k = bm25_top_k
        self.vector_top_k = vector_top_k
        self.final_top_k = final_top_k
        self.rrf_k = rrf_k
        self.use_parallel = use_parallel

        log_message( LG.Retrieval, "HybridRetriever آماده شد", LogLevel.INFO )
        log_message(
            LG.Retrieval,
            f"  - BM25 Top-K: {bm25_top_k}, Vector Top-K: {vector_top_k}",
            LogLevel.DEBUG,
        )
        log_message(
            LG.Retrieval,
            f"  - RRF k={rrf_k}, Parallel: {use_parallel}",
            LogLevel.DEBUG,
        )

    def retrieve( self, query: str, final_top_k: Optional[ int ] = None ) -> List[ Dict[ str, Any ] ]:
        """
        جستجوی Hybrid با RRF
        
        Args:
            query: متن جستجوی کاربر
            final_top_k: تعداد نتایج نهایی (اختیاری)
            
        Returns:
            لیست نتایج merged و re-ranked با فرمت:
            [
                {
                    'chunk_id': str,
                    'rrf_score': float,
                    'bm25_score': float or None,
                    'vector_score': float or None,
                    'bm25_rank': int or None,
                    'vector_rank': int or None,
                    'retrieval_methods': list,
                    'metadata': dict
                },
                ...
            ]
        """
        try:
            if not query or not query.strip():
                log_message( LG.Retrieval, "Query خالی است", LogLevel.WARNING )
                return []

            k = final_top_k if final_top_k is not None else self.final_top_k

            log_message( LG.Retrieval, "=" * 70, LogLevel.INFO )
            log_message( LG.Retrieval, f"🔍 Hybrid Retrieval: '{query[:50]}...'", LogLevel.INFO )
            log_message( LG.Retrieval, "=" * 70, LogLevel.INFO )

            # اجرای BM25 و Vector (موازی یا ترتیبی)
            if self.use_parallel:
                bm25_results, vector_results = self._retrieve_parallel( query )
            else:
                bm25_results, vector_results = self._retrieve_sequential( query )

            # Reciprocal Rank Fusion
            log_message( LG.Retrieval, "🔀 مرحله 3: Reciprocal Rank Fusion...", LogLevel.INFO )
            merged_results = self._apply_rrf( bm25_results, vector_results )

            # انتخاب Top-K نهایی
            final_results = merged_results[ :k ]

            log_message( LG.Retrieval, "=" * 70, LogLevel.INFO )
            log_message(
                LG.Retrieval,
                f"✅ Hybrid Retrieval تکمیل شد - {len(final_results)} نتیجه نهایی",
                LogLevel.INFO,
            )
            log_message( LG.Retrieval, "=" * 70, LogLevel.INFO )

            return final_results

        except Exception as e:
            log_message( LG.Retrieval, f"❌ خطا در hybrid retrieval: {str(e)}", LogLevel.ERROR )
            return []

    def _retrieve_parallel( self, query: str ) -> tuple[ List[ Dict[ str, Any ] ], List[ Dict[ str, Any ] ] ]:
        """
        اجرای موازی BM25 و Vector با ThreadPoolExecutor
        
        نکته: از concurrent.futures استفاده می‌کنیم چون:
        - عملیات I/O bound هستن
        - asyncio نیاز به تغییرات گسترده داره
        - ThreadPool برای الان کافیه
        """

        log_message(
            LG.Retrieval,
            "⚡ اجرای موازی BM25 و Vector...",
            LogLevel.INFO,
        )

        start_time = time.time()

        with ThreadPoolExecutor( max_workers=2 ) as executor:
            # Submit کردن هر دو task
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

    def _retrieve_sequential( self, query: str ) -> tuple[ List[ Dict[ str, Any ] ], List[ Dict[ str, Any ] ] ]:
        """اجرای ترتیبی BM25 و Vector (fallback)"""

        log_message( LG.Retrieval, "📚 مرحله 1: BM25 Retrieval...", LogLevel.INFO )
        start_bm25 = time.time()
        bm25_results = self.bm25_indexer.search( query, top_k=self.bm25_top_k )
        bm25_time = time.time() - start_bm25
        log_message( LG.Retrieval, f"  ✅ {len(bm25_results)} نتیجه ({bm25_time:.2f}s)", LogLevel.INFO )

        log_message( LG.Retrieval, "🤖 مرحله 2: Vector Retrieval...", LogLevel.INFO )
        start_vector = time.time()
        vector_results = self.vector_retriever.retrieve( query, top_k=self.vector_top_k )
        vector_time = time.time() - start_vector
        log_message( LG.Retrieval, f"  ✅ {len(vector_results)} نتیجه ({vector_time:.2f}s)", LogLevel.INFO )

        total_time = bm25_time + vector_time
        log_message( LG.Retrieval, f"  ⏱️ زمان کل: {total_time:.2f}s (ترتیبی)", LogLevel.DEBUG )

        return bm25_results, vector_results

    def _apply_rrf( self, bm25_results: List[ Dict[ str, Any ] ],
                    vector_results: List[ Dict[ str, Any ] ] ) -> List[ Dict[ str, Any ] ]:
        """
        اعمال Reciprocal Rank Fusion استاندارد (بدون وزن‌دهی)
        
        فرمول RRF:
        score(doc) = Σ (1 / (k + rank_i))
        
        Args:
            bm25_results: نتایج BM25
            vector_results: نتایج Vector
            
        Returns:
            لیست merged و sorted بر اساس RRF score
        """
        # ذخیره اطلاعات هر chunk
        chunk_data: Dict[ str, Dict[ str, Any ] ] = defaultdict(
            lambda: {
                ResultKeys.CHUNK_ID: None,
                "bm25_score": None,
                "vector_score": None,
                "bm25_rank": None,
                "vector_rank": None,
                ResultKeys.RETRIEVAL_METHOD: list(),
                ResultKeys.METADATA: {},
                "rrf_score": 0.0,
            } )

        # پردازش نتایج BM25
        for rank, result in enumerate( bm25_results, start=1 ):
            chunk_id = result[ ResultKeys.CHUNK_ID ]
            chunk = chunk_data[ chunk_id ]          # ‫یه بار reference میگیریم
            chunk[ ResultKeys.CHUNK_ID ] = chunk_id
            chunk[ "bm25_score" ] = result[ ResultKeys.SCORE ]
            chunk[ "bm25_rank" ] = rank
            chunk[ ResultKeys.RETRIEVAL_METHOD ].append( "bm25" )
            chunk[ ResultKeys.METADATA ] = result.get( ResultKeys.METADATA, {} )
            chunk[ "rrf_score" ] += 1.0 / ( self.rrf_k + rank )

        # پردازش نتایج Vector
        for rank, result in enumerate( vector_results, start=1 ):
            chunk_id = result[ ResultKeys.CHUNK_ID ]
            chunk = chunk_data[ chunk_id ]          # ‫یه بار reference میگیریم
            chunk[ ResultKeys.CHUNK_ID ] = chunk_id
            chunk[ "vector_score" ] = result[ ResultKeys.SCORE ]
            chunk[ "vector_rank" ] = rank

            if "vector" not in chunk[ ResultKeys.RETRIEVAL_METHOD ]:
                chunk[ ResultKeys.RETRIEVAL_METHOD ].append( "vector" )

            if not chunk[ ResultKeys.METADATA ]:
                chunk[ ResultKeys.METADATA ] = result.get( ResultKeys.METADATA, {} )

            chunk[ "rrf_score" ] += 1.0 / ( self.rrf_k + rank )

        # تبدیل به لیست و مرتب‌سازی
        merged_results = sorted( chunk_data.values(), key=lambda x: x[ "rrf_score" ], reverse=True )

        stats = { "both": 0, "only_bm25": 0, "only_vector": 0 }
        for r in merged_results:
            methods = r[ ResultKeys.RETRIEVAL_METHOD ]
            if len( methods ) == 2:
                stats[ "both" ] += 1
            elif methods == [ "bm25" ]:
                stats[ "only_bm25" ] += 1
            else:
                stats[ "only_vector" ] += 1

        log_message( LG.Retrieval, f"  📊 RRF Stats:", LogLevel.INFO )
        log_message( LG.Retrieval, f"     Both Methods: {stats['both']}", LogLevel.INFO )
        log_message( LG.Retrieval, f"     Only BM25: {stats['only_bm25']}", LogLevel.INFO )
        log_message( LG.Retrieval, f"     Only Vector: {stats['only_vector']}", LogLevel.INFO )

        return merged_results

    def get_stats( self ) -> Dict[ str, Any ]:
        """آمار HybridRetriever"""
        return {
            "method": "hybrid",
            "bm25_top_k": self.bm25_top_k,
            "vector_top_k": self.vector_top_k,
            "final_top_k": self.final_top_k,
            "rrf_k": self.rrf_k,
            "parallel_execution": self.use_parallel,
        }
