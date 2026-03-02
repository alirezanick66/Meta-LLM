from pathlib import Path
from typing import Any, Dict
from sqlalchemy.orm import Session
from backend.app.db.postgres import PostgresManager
from backend.app.services.document.document_processor import document_processor
from backend.app.services.document.chunker import MarkdownChunker
from backend.app.services.embedding.embedding_service import EmbeddingService
from backend.app.services.retrieval.bm25_indexer import BM25Indexer
from backend.app.services.vector.qdrant_indexer import QdrantIndexer
from backend.app.utils.hash_utils import calculate_file_hash
from backend.app.utils.logging_config import LG, LogLevel, log_message


class IndexingPipeline:
    """
   ‫ ‫Pipeline کامل indexing سند با پشتیبانی از چند فرمت
    """

    def __init__(
        self,
        db_session: Session,
        embedding_service: EmbeddingService,
        qdrant_indexer: QdrantIndexer,
        bm25_indexer: BM25Indexer,
        chunker: MarkdownChunker,
    ):
        self.db = PostgresManager( db_session )
        self.processor = document_processor
        self.chunker = chunker
        self.embedding_service = embedding_service
        self.qdrant_indexer = qdrant_indexer
        self.bm25_indexer = bm25_indexer
        log_message( LG.DataProcessing, "IndexingPipeline آماده شد", LogLevel.INFO )

    # ==================== Public Methods ====================

    def index_document( self, file_path: str, skip_bm25_rebuild: bool = False ) -> Dict[ str, Any ]:
        """
       ‫ اجرای کامل pipeline برای یک سند

        Args:
            ‫file_path: مسیر فایل (.md یا .docx)
            ‫skip_bm25_rebuild: اگر True باشد، BM25 بازسازی نمی‌شود (مفید برای پردازش پوشه)

        Returns:
           ‫ دیکشنری نتیجه با کلیدهای: success, document_id, filename,
            total_chunks, total_tokens, action, error
        """
        document = None

        try:
            path = Path( file_path )

            if not path.exists():
                raise FileNotFoundError( f"فایل پیدا نشد: {file_path}" )

            # بررسی پشتیبانی فرمت
            if not self.processor.is_supported( file_path ):
                raise ValueError( f"فرمت '{path.suffix}' پشتیبانی نمی‌شود." )

            log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )
            log_message( LG.DataProcessing, f"🚀 شروع indexing: {path.name}", LogLevel.INFO )
            log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )

            file_hash = calculate_file_hash( file_path )
            filename = path.name

            # ==================== بررسی Replace ====================
            action, should_continue = self._check_and_handle_existing( filename, file_hash )
            if not should_continue:
                return {
                    'success': True,
                    'action': action,
                    'message': 'فایل قبلاً index شده و تغییری نکرده',
                    'filename': filename,
                }

            # ==================== مرحله ۱: استخراج متن ====================
            log_message( LG.DataProcessing, "📄 مرحله 1: استخراج متن...", LogLevel.INFO )
            normalized_text, metadata = self.processor.extract( file_path )

            if not normalized_text.strip():
                raise ValueError( "متن استخراج‌شده خالی است" )

            log_message( LG.DataProcessing, f"✅ متن استخراج شد - {len(normalized_text)} کاراکتر", LogLevel.INFO )

            # ==================== مرحله ۲: ایجاد Document در DB ====================
            log_message( LG.DataProcessing, "💾 مرحله 2: ایجاد Document در PostgreSQL...", LogLevel.INFO )
            document = self.db.create_document(
                filename=filename,
                file_path=str( file_path ),
                file_hash=file_hash,
                total_chunks=0,
            )
            log_message( LG.DataProcessing, f"✅ Document ایجاد شد - ID: {document.id}", LogLevel.INFO )

            # ==================== مرحله ۳: Chunking ====================
            log_message( LG.DataProcessing, "🧩 مرحله 3: Chunking...", LogLevel.INFO )
            chunks = self.chunker.create_chunks( markdown_text=normalized_text, doc_id=document.id, source_file=filename )

            if not chunks:
                raise ValueError( "هیچ chunk ای ساخته نشد" )

            log_message( LG.DataProcessing, f"✅ {len(chunks)} chunk ساخته شد", LogLevel.INFO )

            # ==================== مرحله ۴: Embeddings ====================
            log_message( LG.DataProcessing, "🤖 مرحله 4: ساخت embeddings...", LogLevel.INFO )
            chunks_with_embeddings = self.embedding_service.embed_chunks( chunks )
            log_message( LG.DataProcessing, "✅ Embeddings ساخته شد", LogLevel.INFO )

            # ==================== مرحله ۵: ذخیره در PostgreSQL ====================
            log_message( LG.DataProcessing, "💾 مرحله 5: ذخیره chunks در PostgreSQL...", LogLevel.INFO )

            # ‫استفاده از List Comprehension برای تمیزی
            chunks_data = [ {
                'document_id': document.id,
                'chunk_id': chunk[ 'chunk_id' ],
                'content': chunk[ 'content' ],
                'chunk_index': chunk[ 'metadata' ].get( 'chunk_index', 0 ),
                'token_count': chunk[ 'token_count' ],
            } for chunk in chunks_with_embeddings ]

            if not self.db.bulk_create_chunks( chunks_data ):
                raise RuntimeError( "خطا در ذخیره chunks در PostgreSQL" )

            self.db.update_document_chunks_count( document.id, len( chunks ) )
            log_message( LG.DataProcessing, f"✅ {len(chunks)} chunk در PostgreSQL ذخیره شد", LogLevel.INFO )

            # ==================== مرحله ۶: Qdrant ====================
            log_message( LG.DataProcessing, "🔍 مرحله 6: Indexing در Qdrant...", LogLevel.INFO )
            if not self.qdrant_indexer.index_chunks( chunks_with_embeddings ):
                raise RuntimeError( "خطا در indexing Qdrant" )
            log_message( LG.DataProcessing, "✅ Qdrant indexing انجام شد", LogLevel.INFO )

            # ==================== مرحله ۷: BM25 (Conditional) ====================
            # ‫بازسازی BM25 فقط اگر در حالت تک فایل هستیم انجام شود
            # برای پوشه، در پایان یکبار انجام می‌شود تا کارایی بالا برود

            if not skip_bm25_rebuild:
                log_message( LG.DataProcessing, "📚 مرحله 7: بازسازی BM25 index...", LogLevel.INFO )
                all_chunks = self.db.get_all_chunks()
                if not self.bm25_indexer.rebuild_from_database( all_chunks ):
                    raise RuntimeError( "خطا در ساخت BM25 index" )
                log_message( LG.DataProcessing, f"✅ BM25 بازسازی شد با {len(all_chunks)} chunk کل", LogLevel.INFO )

            # ==================== نتیجه ====================
            log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )
            log_message( LG.DataProcessing, "🎉 Indexing با موفقیت تکمیل شد!", LogLevel.INFO )
            log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )

            return {
                'success': True,
                'action': action,
                'document_id': document.id,
                'filename': filename,
                'file_type': self.processor.get_file_type( file_path ),
                'total_chunks': len( chunks ),
                'total_tokens': sum( c[ 'token_count' ] for c in chunks ),
                'total_chunks_in_system': self.db.get_total_chunks_count(),
                'file_hash': file_hash,
            }

        except Exception as e:
            log_message( LG.DataProcessing, f"❌ خطا در IndexingPipeline: {str(e)}", LogLevel.ERROR )

            # ‫Rollback — حذف document اگه ساخته شده بود
            if document:
                try:
                    log_message( LG.DataProcessing, f"🔄 Rollback - حذف document {document.id}...", LogLevel.ERROR )
                    # تلاش برای پاکسازی داده‌های ناقص
                    self.qdrant_indexer.delete_document_vectors( document.id )
                    self.db.delete_document( document.id )
                except Exception as rb_err:
                    log_message( LG.DataProcessing, f"خطا در rollback: {str(rb_err)}", LogLevel.ERROR )

            return { 'success': False, 'error': str( e ) }

    def index_folder( self, folder_path: str ) -> Dict[ str, Any ]:
        """
        پردازش کامل یک پوشه — همه فایل‌های پشتیبانی‌شده
        
        بهینه‌سازی: بازسازی BM25 تنها یک بار در پایان انجام می‌شود.
        """
        log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )
        log_message( LG.DataProcessing, f"📁 شروع پردازش پوشه: {folder_path}", LogLevel.INFO )
        log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )

        files = self.processor.scan_folder( folder_path )

        if not files:
            log_message( LG.DataProcessing, "⚠️ هیچ فایل قابل پردازشی در پوشه یافت نشد", LogLevel.WARNING )
            return {
                'total_found': 0,
                'succeeded': 0,
                'skipped': 0,
                'replaced': 0,
                'failed': 0,
                'results': [],
            }

        summary = { 'total_found': len( files ), 'succeeded': 0, 'skipped': 0, 'replaced': 0, 'failed': 0, 'results': [] }

        # ‫پردازش فایل‌ها بدون بازسازی مداوم BM25
        for i, file_info in enumerate( files, start=1 ):
            log_message( LG.DataProcessing, f"\n📄 فایل {i}/{len(files)}: {file_info['name']}", LogLevel.INFO )

            # ‫‫ارسال skip_bm25_rebuild=True برای افزایش سرعت
            result = self.index_document( file_info[ 'path' ], skip_bm25_rebuild=True )
            result[ 'filename' ] = file_info[ 'name' ]
            summary[ 'results' ].append( result )

            if not result[ 'success' ]:
                summary[ 'failed' ] += 1
            elif result.get( 'action' ) == 'skipped':
                summary[ 'skipped' ] += 1
            elif result.get( 'action' ) == 'replaced':
                summary[ 'replaced' ] += 1
            else:
                summary[ 'succeeded' ] += 1

        # ==================== بازسازی نهایی BM25 ====================
        # فقط یک بار در پایان همه کارها
        if summary[ 'succeeded' ] > 0 or summary[ 'replaced' ] > 0:
            log_message( LG.DataProcessing, "\n🔄 بازسازی نهایی BM25 برای کل پوشه...", LogLevel.INFO )
            try:
                all_chunks = self.db.get_all_chunks()
                self.bm25_indexer.rebuild_from_database( all_chunks )
                log_message( LG.DataProcessing, "✅ BM25 نهایی بازسازی شد", LogLevel.INFO )
            except Exception as e:
                log_message( LG.DataProcessing, f"⚠️ خطا در بازسازی نهایی BM25: {str(e)}", LogLevel.WARNING )

        # ==================== خلاصه نهایی ====================
        log_message( LG.DataProcessing, "\n" + "=" * 70, LogLevel.INFO )
        log_message( LG.DataProcessing, "📊 خلاصه پردازش پوشه:", LogLevel.INFO )
        log_message( LG.DataProcessing, f"   فایل‌های یافت‌شده: {summary['total_found']}", LogLevel.INFO )
        log_message( LG.DataProcessing, f"   ✅ موفق (جدید): {summary['succeeded']}", LogLevel.INFO )
        log_message( LG.DataProcessing, f"   🔄 جایگزین‌شده: {summary['replaced']}", LogLevel.INFO )
        log_message( LG.DataProcessing, f"   ⏭️ Skip شده: {summary['skipped']}", LogLevel.INFO )
        log_message( LG.DataProcessing, f"   ❌ خطا: {summary['failed']}", LogLevel.INFO )
        log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )

        return summary

    def get_pipeline_stats( self ) -> Dict[ str, Any ]:
        """دریافت آمار کلی pipeline"""
        try:
            return {
                'total_documents': self.db.get_total_documents_count(),
                'total_chunks': self.db.get_total_chunks_count(),
                'qdrant_stats': self.qdrant_indexer.get_stats(),
                'bm25_stats': self.bm25_indexer.get_stats(),
            }
        except Exception as e:
            log_message( LG.DataProcessing, f"خطا در دریافت آمار: {str(e)}", LogLevel.ERROR )
            return {}

    # ==================== Private Methods ====================

    def _check_and_handle_existing( self, filename: str, file_hash: str ) -> tuple[ str, bool ]:
        """
       ‫ منطق ‫Replace by Filename
        """

        existing_by_hash = self.db.get_document_by_hash( file_hash )
        if existing_by_hash and str( existing_by_hash.file_name ) != str( filename ):
            log_message( LG.DataProcessing, f"⚠️ محتوای '{filename}' با '{existing_by_hash.file_name}' یکیه — skip",
                         LogLevel.WARNING )
            return 'skipped', False

        existing = self.db.get_document_by_filename( filename )

        if not existing:
            return 'new', True

        if existing.file_hash == file_hash:
            log_message( LG.DataProcessing, f"⏭️ فایل '{filename}' بدون تغییر است — skip", LogLevel.WARNING )
            return 'skipped', False

        # ‫‫فایل تغییر کرده → جایگزین کن
        log_message( LG.DataProcessing, f"🔄 فایل '{filename}' تغییر کرده — جایگزین می‌شود", LogLevel.INFO )

        self._delete_document_data( existing.id, rebuild_bm25=False )
        return 'replaced', True

    def _delete_document_data( self, document_id: int, rebuild_bm25: bool = True ) -> None:
        """
       ‫ حذف کامل یه document از همه store ها
        
       ‫ تغییر: پارامتر rebuild_bm25 اضافه شد.
       ‫ مقدار پیش‌فرض True است تا اگر این متد از جای دیگری (مثل دکمه delete در پنل ادمین) 
       ‫ صدا زده شد، BM25 خود به خود آپدیت شود.
        """
        try:
            log_message( LG.DataProcessing, f"🗑️ حذف document {document_id}...", LogLevel.INFO )

            self.qdrant_indexer.delete_document_vectors( document_id )
            self.db.delete_document( document_id )

            # ‫تغییر در این خط: شرط بازسازی BM25
            if rebuild_bm25:
                remaining = self.db.get_all_chunks()
                if remaining:
                    self.bm25_indexer.rebuild_from_database( remaining )
                else:
                    self.bm25_indexer.delete_index()
            else:
                log_message( LG.DataProcessing, f"ℹ️ BM25 rebuild رد شد (Batch Mode)", LogLevel.DEBUG )

            log_message( LG.DataProcessing, f"✅ Document {document_id} حذف شد", LogLevel.INFO )

        except Exception as e:
            log_message( LG.DataProcessing, f"⚠️ خطا در حذف document: {str(e)}", LogLevel.WARNING )
