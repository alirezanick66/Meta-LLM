import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent ) )

from backend.app.core.database import session_local
from backend.app.services.indexing_pipeline import IndexingPipeline
from backend.app.utils.logging_config import log_message, LG, LogLevel


def test_full_indexing():
    """تست کامل indexing pipeline"""

    # مسیر فایل تست
    test_file = "backend/data/documents/enghelab.md"

    log_message( LG.DataProcessing, "🧪 شروع تست کامل Indexing Pipeline", LogLevel.INFO )
    log_message( LG.DataProcessing, f"📁 فایل تست: {test_file}", LogLevel.INFO )
    log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )

    # ایجاد session
    db = session_local()

    try:
        # ایجاد pipeline
        pipeline = IndexingPipeline( db )

        # اجرای indexing
        result = pipeline.index_document( test_file )

        # نمایش نتیجه
        if result[ 'success' ]:
            log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )
            log_message( LG.DataProcessing, "✅ تست موفقیت‌آمیز بود!", LogLevel.INFO )
            log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )
            log_message( LG.DataProcessing, f"📄 Document ID: {result['document_id']}", LogLevel.INFO )
            log_message( LG.DataProcessing, f"📄 Filename: {result['filename']}", LogLevel.INFO )
            log_message( LG.DataProcessing, f"🧩 Total Chunks: {result['total_chunks']}", LogLevel.INFO )
            log_message( LG.DataProcessing, f"🔤 Total Tokens: {result['total_tokens']}", LogLevel.INFO )
            log_message( LG.DataProcessing, f"✅ Qdrant Indexed: {result['qdrant_indexed']}", LogLevel.INFO )
            # نمایش آمار کلی
            stats = pipeline.get_pipeline_stats()
            log_message( LG.DataProcessing, "📊 آمار کلی سیستم:", LogLevel.INFO )
            log_message( LG.DataProcessing, f"   Documents: {stats['total_documents']}", LogLevel.INFO )
            log_message( LG.DataProcessing, f"   Chunks: {stats['total_chunks']}", LogLevel.INFO )
            log_message( LG.DataProcessing, f"   Qdrant Vectors: {stats['qdrant_stats']['total_vectors']}",
                         LogLevel.INFO )
            log_message( LG.DataProcessing, f"   BM25 Chunks: {stats['bm25_stats']['total_chunks']}", LogLevel.INFO )
            log_message( LG.DataProcessing, "=" * 70, LogLevel.INFO )

        else:
            log_message( LG.DataProcessing, "❌ تست ناموفق بود!", LogLevel.ERROR )
            log_message( LG.DataProcessing, f"خطا: {result.get('error', 'نامشخص')}", LogLevel.ERROR )

    except Exception as e:
        log_message( LG.DataProcessing, f"❌ خطای غیرمنتظره: {str(e)}", LogLevel.ERROR )

    finally:
        db.close()
        log_message( LG.DataProcessing, "🔚 پایان تست", LogLevel.INFO )


test_full_indexing()
