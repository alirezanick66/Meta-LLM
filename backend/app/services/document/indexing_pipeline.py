from typing import Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session
from backend.app.services.document.markdown_extractor import markdown_extractor
from backend.app.services.document.chunker import MarkdownChunker
from backend.app.services.embedding_service import get_embedding_service
from backend.app.services.qdrant_indexer import create_qdrant_indexer
from backend.app.services.retrieval.bm25_indexer import BM25Indexer
from backend.app.db.postgres import PostgresManager
from backend.app.utils.hash_utils import calculate_file_hash
from backend.app.utils.logging_config import log_message, LG, LogLevel


class IndexingPipeline:
    """
    Pipeline کامل indexing یک document
    
    مراحل:
    1. استخراج متن از Markdown
    2. Chunking
    3. Generate embeddings
    4. ذخیره در PostgreSQL (metadata)
    5. Index در Qdrant (vectors)
    6. Rebuild BM25 (با تمام chunks دیتابیس)
    """

    def __init__( self, db_session: Session ):
        """
        Args:
            db_session: SQLAlchemy session
        """
        self.db = PostgresManager( db_session )
        self.markdown_extractor = markdown_extractor
        self.chunker = MarkdownChunker()
        self.embedding_service = get_embedding_service()
        self.qdrant_indexer = create_qdrant_indexer()
        self.bm25_indexer = BM25Indexer()

        log_message( LG.DataProcessing, "IndexingPipeline آماده شد", LogLevel.INFO )

    def index_document( self, file_path: str ) -> Dict[ str, Any ]:
        """
        اجرای کامل pipeline برای یک document
        
        Args:
            file_path: مسیر فایل .md
            
        Returns:
            دیکشنری حاوی نتیجه و آمار
        """
        document = None          # برای rollback

        try:
            file_path_obj = Path( file_path )

            # بررسی وجود فایل
            if not file_path_obj.exists():
                raise FileNotFoundError( f"فایل پیدا نشد: {file_path}" )

            log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )
            log_message( LG.DataProcessing, f"🚀 شروع indexing: {file_path_obj.name}", LogLevel.INFO )
            log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )

            # ==================== مرحله 1: بررسی تکراری ====================
            file_hash = calculate_file_hash( file_path )
            filename = file_path_obj.name

            existing_doc = self.db.get_document_by_filename( filename )
            if existing_doc:
                # بررسی تغییرات
                if str( existing_doc.file_hash ) == str( file_hash ):
                    log_message( LG.DataProcessing, f"⚠️ این فایل قبلاً ایندکس شده و تغییری نکرده: {filename}",
                                 LogLevel.WARNING )
                    return { 'success': False, 'message': 'فایل قبلاً ایندکس شده', 'document_id': existing_doc.id }
                else:
                    log_message( LG.DataProcessing, f"🔄 فایل تغییر کرده، در حال به‌روزرسانی: {filename}", LogLevel.INFO )
                    # حذف اطلاعات قبلی
                    self._delete_document_data( existing_doc.id )          # type: ignore

            # ==================== مرحله 2: استخراج متن ====================
            log_message( LG.DataProcessing, "📄 مرحله 1: استخراج متن از Markdown...", LogLevel.INFO )
            normalized_text, metadata = self.markdown_extractor.extract_from_markdown( file_path )

            if not normalized_text.strip():
                raise ValueError( "متن استخراج شده خالی است" )

            log_message( LG.DataProcessing, f"✅ متن استخراج شد - طول: {len(normalized_text)} کاراکتر", LogLevel.INFO )

            # ==================== مرحله 3: ایجاد Document در DB ====================
            log_message( LG.DataProcessing, "💾 مرحله 2: ایجاد Document در PostgreSQL...", LogLevel.INFO )

            document = self.db.create_document(
                filename=filename,
                file_path=str( file_path ),
                file_hash=file_hash,
                total_chunks=0          # بعداً update میشه
            )

            log_message( LG.DataProcessing, f"✅ Document ایجاد شد - ID: {document.id}", LogLevel.INFO )

            # ==================== مرحله 4: Chunking ====================
            log_message( LG.DataProcessing, "🧩 مرحله 3: Chunking متن...", LogLevel.INFO )

            chunks = self.chunker.create_chunks(
                markdown_text=normalized_text,
                doc_id=document.id,          # type: ignore
                source_file=filename )

            if not chunks:
                raise ValueError( "هیچ chunk ای ساخته نشد" )

            log_message( LG.DataProcessing, f"✅ {len(chunks)} chunk ساخته شد", LogLevel.INFO )

            # ==================== مرحله 5: Generate Embeddings ====================
            log_message( LG.DataProcessing, "🤖 مرحله 4: ساخت embeddings...", LogLevel.INFO )

            chunks_with_embeddings = self.embedding_service.embed_chunks( chunks )

            log_message( LG.DataProcessing, "✅ Embeddings ساخته شد", LogLevel.INFO )

            # ==================== مرحله 6: ذخیره Chunks در PostgreSQL ====================
            log_message( LG.DataProcessing, "💾 مرحله 5: ذخیره chunks در PostgreSQL...", LogLevel.INFO )

            chunks_data = []
            for chunk in chunks_with_embeddings:
                chunks_data.append( {
                    'document_id': document.id,
                    'chunk_id': chunk[ 'chunk_id' ],
                    'content': chunk[ 'content' ],
                    'chunk_index': chunk[ 'metadata' ][ 'chunk_index' ],
                    'token_count': chunk[ 'token_count' ]
                } )

            success = self.db.bulk_create_chunks( chunks_data )
            if not success:
                raise RuntimeError( "خطا در ذخیره chunks در PostgreSQL" )

            # به‌روزرسانی تعداد chunks در document
            self.db.update_document_chunks_count( document.id, len( chunks ) )          # type: ignore

            log_message( LG.DataProcessing, f"✅ {len(chunks)} chunk در PostgreSQL ذخیره شد", LogLevel.INFO )

            # ==================== مرحله 7: Index در Qdrant ====================
            log_message( LG.DataProcessing, "🔍 مرحله 6: Indexing در Qdrant...", LogLevel.INFO )

            qdrant_success = self.qdrant_indexer.index_chunks( chunks_with_embeddings )
            if not qdrant_success:
                raise RuntimeError( "خطا در indexing Qdrant" )

            log_message( LG.DataProcessing, "✅ Indexing در Qdrant انجام شد", LogLevel.INFO )

            # ==================== مرحله 8: Rebuild BM25 با تمام chunks ====================
            log_message( LG.DataProcessing, "📚 مرحله 7: بازسازی BM25 index...", LogLevel.INFO )

            # دریافت تمام chunks از دیتابیس (شامل chunks جدید و قدیمی)
            all_db_chunks = self.db.get_all_chunks()

            bm25_success = self.bm25_indexer.rebuild_from_database( all_db_chunks )
            if not bm25_success:
                raise RuntimeError( "خطا در ساخت BM25 index" )

            log_message( LG.DataProcessing, f"✅ BM25 index بازسازی شد با {len(all_db_chunks)} chunk کل", LogLevel.INFO )

            # ==================== خلاصه نتایج ====================
            log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )
            log_message( LG.DataProcessing, "🎉 Indexing با موفقیت تکمیل شد!", LogLevel.INFO )
            log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )

            result = {
                'success': True,
                'document_id': document.id,
                'filename': filename,
                'total_chunks': len( chunks ),
                'total_tokens': sum( c[ 'token_count' ] for c in chunks ),
                'total_chunks_in_system': len( all_db_chunks ),
                'qdrant_indexed': qdrant_success,
                'bm25_indexed': bm25_success,
                'file_hash': file_hash
            }

            # نمایش آمار
            log_message( LG.DataProcessing, f"📊 Document ID: {result['document_id']}", LogLevel.INFO )
            log_message( LG.DataProcessing, f"📊 Chunks این سند: {result['total_chunks']}", LogLevel.INFO )
            log_message( LG.DataProcessing, f"📊 Total Chunks سیستم: {result['total_chunks_in_system']}", LogLevel.INFO )
            log_message( LG.DataProcessing, f"📊 Total Tokens: {result['total_tokens']}", LogLevel.INFO )
            log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )

            return result

        except Exception as e:
            log_message( LG.DataProcessing, f"❌ خطا در IndexingPipeline: {str(e)}", LogLevel.ERROR )

            # ✅ Rollback: حذف document اگه ساخته شده بود
            if document:
                try:
                    log_message( LG.DataProcessing, f"🔄 برگرداندن تغییرات - حذف document {document.id}...",
                                 LogLevel.ERROR )
                    self.db.delete_document( document.id )          # type: ignore
                except Exception as rollback_error:
                    log_message( LG.DataProcessing, f"خطا در rollback: {str(rollback_error)}", LogLevel.ERROR )

            return { 'success': False, 'error': str( e ) }

    def _delete_document_data( self, document_id: int ):
        """حذف اطلاعات یک document از همه جا"""
        try:
            log_message( LG.DataProcessing, f"🗑️ حذف اطلاعات document {document_id}...", LogLevel.INFO )

            # 1. حذف از Qdrant
            self.qdrant_indexer.delete_document_vectors( document_id )

            # 2. حذف از PostgreSQL (chunks به صورت cascade حذف میشن)
            self.db.delete_document( document_id )

            # 3. ✅ بازسازی BM25 با chunks باقیمانده
            remaining_chunks = self.db.get_all_chunks()

            if remaining_chunks:
                self.bm25_indexer.rebuild_from_database( remaining_chunks )
                log_message( LG.DataProcessing, f"✅ BM25 بازسازی شد با {len(remaining_chunks)} chunk باقیمانده",
                             LogLevel.INFO )
            else:
                # اگه هیچ chunk ای نمونده، index رو پاک کن
                self.bm25_indexer.delete_index()
                log_message( LG.DataProcessing, "✅ BM25 index حذف شد (هیچ chunk ای باقی نمونده)", LogLevel.INFO )

            log_message( LG.DataProcessing, f"✅ اطلاعات document {document_id} حذف شد", LogLevel.INFO )

        except Exception as e:
            log_message( LG.DataProcessing, f"خطا در حذف document: {str(e)}", LogLevel.WARNING )

    def get_pipeline_stats( self ) -> Dict[ str, Any ]:
        """دریافت آمار کلی pipeline"""
        try:
            return {
                'total_documents': self.db.get_total_documents_count(),
                'total_chunks': self.db.get_total_chunks_count(),
                'qdrant_stats': self.qdrant_indexer.get_stats(),
                'bm25_stats': self.bm25_indexer.get_stats()
            }
        except Exception as e:
            log_message( LG.DataProcessing, f"خطا در دریافت آمار: {str(e)}", LogLevel.ERROR )
            return {}
