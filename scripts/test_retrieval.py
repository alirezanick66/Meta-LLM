import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent ) )

from backend.app.services.retrieval.hybrid_retriever import create_hybrid_retriever
from backend.app.core.database import session_local
from backend.app.db.postgres import PostgresManager
from backend.app.utils.logging_config import log_message, LG, LogLevel

from backend.app.services.retrieval.vector_retriever import ResultKeys


def test_retrieval():
    """تست سیستم Retrieval با query های مختلف"""

    log_message( LG.Retrieval, "=" * 70, LogLevel.INFO )
    log_message( LG.Retrieval, "🧪 شروع تست Retrieval System", LogLevel.INFO )
    log_message( LG.Retrieval, "=" * 70, LogLevel.INFO )

    # ساخت Hybrid Retriever
    try:
        retriever = create_hybrid_retriever( bm25_top_k=20, vector_top_k=20, final_top_k=10, rrf_k=60 )
        log_message( LG.Retrieval, "✅ HybridRetriever ساخته شد", LogLevel.INFO )
    except Exception as e:
        log_message( LG.Retrieval, f"❌ خطا در ساخت Retriever: {str(e)}", LogLevel.ERROR )
        return

    # لیست query های تست
    test_queries = [
          # "انقلاب اسلامی چه تأثیری بر نظریه های غربی گذاشت؟",
          # "اسم نویسنده کتاب؟"
        "علی نیک"
          # "ویژگی های انقلاب اسلامی ایران چیست؟",
          # "تعریف نظام سیاسی",
          # "امام خمینی",
          # "مدرنیته و سنت",
    ]

    # تست هر query
    for i, query in enumerate( test_queries, start=1 ):
        log_message( LG.Retrieval, "\n" + "=" * 70, LogLevel.INFO )
        log_message( LG.Retrieval, f"📝 Query #{i}: '{query}'", LogLevel.INFO )
        log_message( LG.Retrieval, "=" * 70, LogLevel.INFO )

        try:
            # اجرای retrieval
            results = retriever.retrieve( query, final_top_k=5 )

            if not results:
                log_message( LG.Retrieval, "⚠️ هیچ نتیجه‌ای پیدا نشد", LogLevel.WARNING )
                continue

            # نمایش نتایج
            log_message( LG.Retrieval, f"\n📊 نتایج (تعداد: {len(results)}):", LogLevel.INFO )
            log_message( LG.Retrieval, "-" * 70, LogLevel.INFO )

            # ایجاد session برای دریافت content
            db = session_local()
            pg_manager = PostgresManager( db )

            for rank, result in enumerate( results, start=1 ):
                log_message( LG.Retrieval, f"\n🔹 Rank #{rank}", LogLevel.INFO )
                log_message( LG.Retrieval, f"   Chunk ID: {result['chunk_id']}", LogLevel.INFO )
                log_message(
                    LG.Retrieval,
                    f"   RRF Score: {result['rrf_score']:.4f}",
                    LogLevel.INFO,
                )

                # امتیازات جداگانه
                if result[ "bm25_score" ] is not None:
                    log_message(
                        LG.Retrieval,
                        f"   BM25 Score: {result['bm25_score']:.4f} (Rank: {result['bm25_rank']})",
                        LogLevel.DEBUG,
                    )
                if result[ "vector_score" ] is not None:
                    log_message(
                        LG.Retrieval,
                        f"   Vector Score: {result['vector_score']:.4f} (Rank: {result['vector_rank']})",
                        LogLevel.DEBUG,
                    )

                # روش های retrieval
                methods = ", ".join( result[ ResultKeys.RETRIEVAL_METHOD ] )
                log_message( LG.Retrieval, f"   Methods: {methods}", LogLevel.INFO )

                # metadata
                metadata = result.get( "metadata", {} )
                if metadata:
                    hierarchy = metadata.get( "hierarchy", "N/A" )
                    log_message( LG.Retrieval, f"   Hierarchy: {hierarchy}", LogLevel.DEBUG )

                # 🆕 نمایش محتوای chunk
                try:
                    content = pg_manager.get_chunk_content( result[ 'chunk_id' ] )

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
