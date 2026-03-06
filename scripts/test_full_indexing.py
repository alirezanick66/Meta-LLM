import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent ) )

from backend.app.core.database import SessionLocal
from backend.app.services.document.indexing_pipeline import IndexingPipeline
from backend.app.utils.logging_config import log_message, LG, LogLevel
from backend.app.api.dependencies import ( get_embedding_service, get_qdrant_indexer, get_bm25_indexer, get_tokenizer_service )
from backend.app.services.document.chunker import MarkdownChunker


def test_full_indexing():
    """ ‫تست کامل indexing pipeline"""

    # مسیر فایل تست
    test_file = "backend/data/documents/enghelab.md"

    log_message( LG.DataProcessing, "🧪 شروع تست کامل Indexing Pipeline", LogLevel.INFO )
    log_message( LG.DataProcessing, f"📁 فایل تست: {test_file}", LogLevel.INFO )
    log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )

    # ایجاد session
    with SessionLocal() as db:
        try:
            # ایجاد pipeline
            pipeline = IndexingPipeline(
                db_session=db,
                embedding_service=get_embedding_service(),
                qdrant_indexer=get_qdrant_indexer(),
                bm25_indexer=get_bm25_indexer(),
                chunker=MarkdownChunker( get_tokenizer_service() ),
            )

            # اجرای indexing
            result = pipeline.index_document( test_file )
            # نمایش نتیجه
            if result[ 'success' ]:
                log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )
                log_message( LG.DataProcessing, "✅ تست موفقیت‌آمیز بود!", LogLevel.INFO )
                log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )

                if result[ 'action' ] == 'skipped':
                    log_message( LG.DataProcessing, "⏭️ فایل بدون تغییر بود", LogLevel.INFO )

                else:
                    log_message( LG.DataProcessing, f"📁 فایل ساخته شد", LogLevel.INFO )
                    log_message( LG.DataProcessing, f"📄 Document ID: {result['document_id']}", LogLevel.INFO )
                    log_message( LG.DataProcessing, f"📄 Filename: {result['filename']}", LogLevel.INFO )
                    log_message( LG.DataProcessing, f"🧩 Total Chunks: {result['total_chunks']}", LogLevel.INFO )
                    log_message( LG.DataProcessing, f"🔤 Total Tokens: {result['total_tokens']}", LogLevel.INFO )

            else:
                log_message( LG.DataProcessing, f"❌ خطا: {result.get('error')}", LogLevel.ERROR )

        except Exception as e:
            log_message( LG.DataProcessing, f"❌ خطای غیرمنتظره: {str(e)}", LogLevel.ERROR )

        finally:
            db.close()
            log_message( LG.DataProcessing, "🔚 پایان تست", LogLevel.INFO )


test_full_indexing()
