import sys
from pathlib import Path

# ‫اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent ) )

from backend.app.core.database import SessionLocal
from backend.app.services.document.indexing_pipeline import IndexingPipeline
from backend.app.utils.logging_config import log_message, LG, LogLevel
from backend.app.api.dependencies import ( get_embedding_service, get_qdrant_indexer, get_bm25_indexer, get_tokenizer_service )
from backend.app.services.document.chunker import MarkdownChunker


def test_full_indexing():
    """‫تست کامل indexing pipeline برای همه فایل‌های corpus"""

    folder_path = "docs/corpus"

    log_message( LG.DataProcessing, "🧪 شروع تست کامل Indexing Pipeline", LogLevel.INFO )
    log_message( LG.DataProcessing, f"📁 پوشه: {folder_path}", LogLevel.INFO )
    log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )

    with SessionLocal() as db:
        try:
            pipeline = IndexingPipeline(
                db_session=db,
                embedding_service=get_embedding_service(),
                qdrant_indexer=get_qdrant_indexer(),
                bm25_indexer=get_bm25_indexer(),
                chunker=MarkdownChunker( get_tokenizer_service() ),
            )

            result = pipeline.index_folder( folder_path )

            log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )

            if result[ 'total_found' ] == 0:
                log_message( LG.DataProcessing, "❌ هیچ فایلی در پوشه پیدا نشد", LogLevel.ERROR )
                return

            log_message( LG.DataProcessing, "✅ تست موفقیت‌آمیز بود!", LogLevel.INFO )
            log_message( LG.DataProcessing, f"📁 فایل‌های یافت‌شده: {result['total_found']}", LogLevel.INFO )
            log_message( LG.DataProcessing, f"✅ موفق (جدید): {result['succeeded']}", LogLevel.INFO )
            log_message( LG.DataProcessing, f"🔄 جایگزین‌شده: {result['replaced']}", LogLevel.INFO )
            log_message( LG.DataProcessing, f"⏭️ Skip شده: {result['skipped']}", LogLevel.INFO )
            log_message( LG.DataProcessing, f"❌ خطا: {result['failed']}", LogLevel.INFO )

            if result[ 'failed' ] > 0:
                log_message( LG.DataProcessing, "\n⚠️ جزئیات خطاها:", LogLevel.WARNING )
                for r in result[ 'results' ]:
                    if not r[ 'success' ]:
                        log_message( LG.DataProcessing, f"  - {r.get('filename')}: {r.get('error')}", LogLevel.ERROR )

        except Exception as e:
            log_message( LG.DataProcessing, f"❌ خطای غیرمنتظره: {str(e)}", LogLevel.ERROR )

        finally:
            db.close()
            log_message( LG.DataProcessing, "🔚 پایان تست", LogLevel.INFO )


test_full_indexing()
