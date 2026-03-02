import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent.parent ) )

from backend.app.api.dependencies import get_hybrid_retriever
from backend.app.core.database import SessionLocal
from backend.app.db.postgres import PostgresManager
from backend.app.utils.logging_config import log_message, LG, LogLevel

from backend.app.schemas.retrieval_schemas import ResultKeys, RRFKeys


def test_retrieval():
    """ ‫تست سیستم Retrieval با query های مختلف"""

    # ‫ساخت Hybrid Retriever
    try:
        retriever = get_hybrid_retriever()
        log_message( LG.Retrieval, "✅ HybridRetriever ساخته شد", LogLevel.INFO )
    except Exception as e:
        log_message( LG.Retrieval, f"❌ خطا در ساخت Retriever: {str(e)}", LogLevel.ERROR )
        return

    # ‫‫لیست query های تست
    test_queries = [
        "اسم نویسنده کتاب؟",
        "علی نیک",
        "ویژگی های انقلاب اسلامی ایران چیست؟",
        "تعریف نظام سیاسی",
        "امام خمینی",
        "کص ننت",
        "مادر قحبه",
        "تاریخ ایران",
        "اقتصاد ایران",
        "کیر",
        "مرده",
        "موزیک ایرانی",
    ]

    # ‫تست هر query
    for i, query in enumerate( test_queries, start=1 ):
        log_message( LG.Retrieval, "\n" + "=" * 70, LogLevel.INFO )
        log_message( LG.Retrieval, f"📝 Query #{i}: '{query}'", LogLevel.INFO )
        log_message( LG.Retrieval, "=" * 70, LogLevel.INFO )

        try:
            # ‫اجرای retrieval
            results = retriever.retrieve( query, final_top_k=5 )

            if not results:
                log_message( LG.Retrieval, "⚠️ هیچ نتیجه‌ای پیدا نشد", LogLevel.WARNING )
                continue

            # نمایش نتایج
            log_message( LG.Retrieval, f"\n📊 نتایج (تعداد: {len(results)}):", LogLevel.INFO )
            log_message( LG.Retrieval, "-" * 70, LogLevel.INFO )

            # ‫ایجاد session برای دریافت content
            db = SessionLocal()
            pg_manager = PostgresManager( db )

            for rank, result in enumerate( results, start=1 ):
                log_message( LG.Retrieval, f"\n🔹 Rank #{rank}", LogLevel.INFO )
                log_message( LG.Retrieval, f"   Chunk ID: {result['chunk_id']}", LogLevel.INFO )
                log_message( LG.Retrieval, f"   RRF Score: {result[RRFKeys.RRF_SCORE]:.4f}", LogLevel.INFO )

                # امتیازات جداگانه
                if result[ RRFKeys.BM25_SCORE ] is not None:
                    log_message(
                        LG.Retrieval,
                        f"   BM25 Score: {result[RRFKeys.BM25_SCORE]:.4f} (Rank: {result[RRFKeys.BM25_RANK]})",
                        LogLevel.DEBUG,
                    )
                if result[ RRFKeys.VECTOR_SCORE ] is not None:
                    log_message(
                        LG.Retrieval,
                        f"   Vector Score: {result[RRFKeys.VECTOR_SCORE]:.4f} (Rank: {result[RRFKeys.VECTOR_RANK]})",
                        LogLevel.DEBUG,
                    )

                # ‫روش های retrieval
                methods = ", ".join( result[ ResultKeys.RETRIEVAL_METHOD ] )
                log_message( LG.Retrieval, f"   Methods: {methods}", LogLevel.INFO )

                # metadata
                metadata = result.get( "metadata", {} )
                if metadata:
                    hierarchy = metadata.get( "hierarchy", "N/A" )
                    log_message( LG.Retrieval, f"   Hierarchy: {hierarchy}", LogLevel.DEBUG )

                # 🆕 ‫نمایش محتوای chunk
                try:
                    contents = pg_manager.get_chunks_content_bulk( [ result[ 'chunk_id' ] ] )
                    content = contents.get( result[ 'chunk_id' ], "" )

                    if content:
                        # نمایش 300 کاراکتر اول
                        preview = content[ :300 ] + "..." if len( content ) > 300 else content
                        log_message( LG.Retrieval, f"   📄 Content Preview:\n      {preview}", LogLevel.INFO )
                except Exception as e:
                    log_message( LG.Retrieval, f"   ⚠️ خطا در دریافت content: {str(e)}", LogLevel.WARNING )

            db.close()
            log_message( LG.Retrieval, "-" * 70, LogLevel.INFO )

        except Exception as e:
            log_message( LG.Retrieval, f"❌ خطا در پردازش query: {str(e)}", LogLevel.ERROR )
            continue

    log_message( LG.Retrieval, "\n" + "=" * 70, LogLevel.INFO )
    log_message( LG.Retrieval, "🎉 تست Retrieval System تکمیل شد", LogLevel.INFO )
    log_message( LG.Retrieval, "=" * 70, LogLevel.INFO )


if __name__ == "__main__":
    test_retrieval()
