import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from backend.app.utils.custom_normalizer import persian_normalizer
from backend.app.utils.logging_config import log_message, LG, LogLevel
import heapq


class BM25Indexer:
    """
    مدیریت BM25 indexing برای جستجوی کلمات کلیدی
    - ساخت index با rank_bm25
    - ذخیره/بارگذاری از pickle
    - جستجوی سریع
    """
    PERSIAN_STOPWORDS = {
        'در', 'به', 'از', 'که', 'این', 'را', 'با', 'برای', 'آن', 'است', 'یک', 'و', 'تا', 'بر', 'هم', 'نیز', 'می', 'شد',
        'یا', 'اما', 'ولی', 'چون', 'اگر', 'تر', 'ترین', 'هر', 'خود'
    }

    def __init__( self, cache_dir: str = "backend/data/storage/bm25_cache" ):
        """
        Args:
            cache_dir: مسیر ذخیره‌سازی فایل‌های BM25
        """
        self.cache_dir = Path( cache_dir )
        self.cache_dir.mkdir( parents=True, exist_ok=True )

        self.index_path = self.cache_dir / "bm25_index.pkl"
        self.mapping_path = self.cache_dir / "chunk_mapping.pkl"
        self.metadata_path = self.cache_dir / "metadata.json"

        self.normalizer = persian_normalizer
        self.bm25_index: Optional[ BM25Okapi ] = None
        self.chunk_ids: List[ str ] = []
        self.chunk_contents: List[ str ] = []

        log_message( LG.Retrieval, f"BM25Indexer آماده شد - مسیر: {self.cache_dir}", LogLevel.INFO )

    def _tokenize( self, text: str ) -> List[ str ]:
        """
        توکنایز متن فارسی
        
        Args:
            text: متن ورودی
            
        Returns:
            لیست توکن‌ها
        """
        # نرمال‌سازی
        normalized = self.normalizer.normalize( text )

        # تقسیم به کلمات (simple tokenization)
        tokens = normalized.split()

        # حذف توکن‌های خیلی کوتاه (کمتر از 2 کاراکتر)
        tokens = [ t for t in tokens if len( t ) >= 2 and t not in self.PERSIAN_STOPWORDS ]

        return tokens

    def build_index( self, chunks: List[ Dict[ str, Any ] ] ) -> bool:
        """
        ساخت BM25 index از chunks
        
        Args:
            chunks: لیست chunks با فیلد 'content' و 'chunk_id'
            
        Returns:
            True در صورت موفقیت
        """
        try:
            if not chunks:
                log_message( LG.Retrieval, "لیست chunks خالی است", LogLevel.WARNING )
                return False

            log_message( LG.Retrieval, f"شروع ساخت BM25 index برای {len(chunks)} chunk...", LogLevel.INFO )

            # استخراج محتوا و chunk_ids
            self.chunk_ids = []
            self.chunk_contents = []
            tokenized_corpus = []

            for chunk in chunks:
                chunk_id = chunk.get( 'chunk_id' )
                content = chunk.get( 'content', '' )

                if not chunk_id or not content.strip():
                    log_message( LG.Retrieval, f"⚠️ Chunk نامعتبر: {chunk_id}", LogLevel.WARNING )
                    continue

                self.chunk_ids.append( chunk_id )
                self.chunk_contents.append( content )

                # توکنایز و اضافه به corpus
                tokens = self._tokenize( content )
                tokenized_corpus.append( tokens )

            if not tokenized_corpus:
                log_message( LG.Retrieval, "❌ هیچ chunk معتبری برای indexing وجود ندارد", LogLevel.ERROR )
                return False

            # ساخت BM25 index
            log_message( LG.Retrieval, "در حال ساخت BM25 index...", LogLevel.INFO )
            self.bm25_index = BM25Okapi( tokenized_corpus )

            # ذخیره در دیسک
            self._save_index()

            log_message( LG.Retrieval, f"✅ BM25 index برای {len(self.chunk_ids)} chunk ساخته شد", LogLevel.INFO )
            return True

        except Exception as e:
            log_message( LG.Retrieval, f"❌ خطا در ساخت BM25 index: {str(e)}", LogLevel.ERROR )
            return False

    def _save_index( self ) -> bool:
        """ذخیره index و mapping در دیسک"""
        try:
            # ذخیره BM25 index
            with open( self.index_path, 'wb' ) as f:
                pickle.dump( self.bm25_index, f )

            # ذخیره chunk mapping
            mapping_data = { 'chunk_ids': self.chunk_ids, 'chunk_contents': self.chunk_contents }
            with open( self.mapping_path, 'wb' ) as f:
                pickle.dump( mapping_data, f )

            log_message( LG.Retrieval, f"✅ BM25 index ذخیره شد: {self.index_path}", LogLevel.DEBUG )
            return True

        except Exception as e:
            log_message( LG.Retrieval, f"خطا در ذخیره BM25 index: {str(e)}", LogLevel.ERROR )
            return False

    def load_index( self ) -> bool:
        """بارگذاری index از دیسک"""
        try:
            if not self.index_path.exists() or not self.mapping_path.exists():
                log_message( LG.Retrieval, "فایل‌های BM25 index وجود ندارند", LogLevel.WARNING )
                return False

            # بارگذاری BM25 index
            with open( self.index_path, 'rb' ) as f:
                self.bm25_index = pickle.load( f )

            # بارگذاری mapping
            with open( self.mapping_path, 'rb' ) as f:
                mapping_data = pickle.load( f )
                self.chunk_ids = mapping_data[ 'chunk_ids' ]
                self.chunk_contents = mapping_data[ 'chunk_contents' ]

            log_message( LG.Retrieval, f"✅ BM25 index بارگذاری شد - {len(self.chunk_ids)} chunks", LogLevel.INFO )
            return True

        except Exception as e:
            log_message( LG.Retrieval, f"خطا در بارگذاری BM25 index: {str(e)}", LogLevel.ERROR )
            return False

    def search( self, query: str, top_k: int = 20 ) -> List[ Dict[ str, Any ] ]:
        """
        جستجوی BM25
        
        Args:
            query: متن جستجو
            top_k: تعداد نتایج
            
        Returns:
            لیست نتایج با فرمت: [{'chunk_id': ..., 'score': ..., 'content': ...}, ...]
        """
        try:
            if self.bm25_index is None:
                log_message( LG.Retrieval, "BM25 index بارگذاری نشده است", LogLevel.WARNING )
                # تلاش برای بارگذاری
                if not self.load_index():
                    return []

            # توکنایز query
            query_tokens = self._tokenize( query )

            if not query_tokens:
                log_message( LG.Retrieval, "Query خالی یا نامعتبر است", LogLevel.WARNING )
                return []

            # محاسبه امتیازات
            scores = self.bm25_index.get_scores( query_tokens )          #type:ignore

            # مرتب‌سازی و انتخاب top-k
            top_indices = heapq.nlargest( top_k, range( len( scores ) ), key=lambda i: scores[ i ] )

            # ساخت نتایج
            results = []
            for idx in top_indices:
                if scores[ idx ] > 0:
                    results.append( {
                        'chunk_id': self.chunk_ids[ idx ],
                        'score': float( scores[ idx ] ),
                        'content': self.chunk_contents[ idx ]
                    } )
            return results

        except Exception as e:
            log_message( LG.Retrieval, f"❌ خطا در BM25 search: {str(e)}", LogLevel.ERROR )
            return []

    def delete_index( self ) -> bool:
        """حذف کامل index از دیسک"""
        try:
            if self.index_path.exists():
                self.index_path.unlink()
            if self.mapping_path.exists():
                self.mapping_path.unlink()

            self.bm25_index = None
            self.chunk_ids = []
            self.chunk_contents = []

            log_message( LG.Retrieval, "✅ BM25 index حذف شد", LogLevel.INFO )
            return True

        except Exception as e:
            log_message( LG.Retrieval, f"خطا در حذف BM25 index: {str(e)}", LogLevel.ERROR )
            return False

    def get_stats( self ) -> Dict[ str, Any ]:
        """آمار BM25 index"""
        return {
            'total_chunks': len( self.chunk_ids ),
            'index_loaded': self.bm25_index is not None,
            'storage_path': str( self.cache_dir )
        }

    def rebuild_from_database( self, db_chunks: List ) -> bool:
        """
        بازسازی کامل index از chunks دیتابیس
        
        Args:
            db_chunks: لیست Chunk objects از PostgreSQL
            
        Returns:
            True در صورت موفقیت
        """
        try:
            if not db_chunks:
                log_message( LG.Retrieval, "لیست chunks دیتابیس خالی است", LogLevel.WARNING )
                return self.delete_index()          # حذف index قدیمی

            # تبدیل به فرمت مناسب
            chunks_data = [ { 'chunk_id': chunk.chunk_id, 'content': chunk.content } for chunk in db_chunks ]

            log_message( LG.Retrieval, f"بازسازی BM25 index با {len(chunks_data)} chunk از دیتابیس...", LogLevel.INFO )

            return self.build_index( chunks_data )

        except Exception as e:
            log_message( LG.Retrieval, f"❌ خطا در rebuild از دیتابیس: {str(e)}", LogLevel.ERROR )
            return False
