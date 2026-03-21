import sys
from pathlib import Path

sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent.parent ) )

from backend.app.api.dependencies import get_hybrid_retriever
from backend.app.core.database import SessionLocal
from backend.app.db.postgres import PostgresManager
from backend.app.utils.logging_config import log_message, LG, LogLevel
from backend.app.schemas.retrieval_schemas import ResultKeys, RRFKeys
from backend.app.core.config import settings


def test_retrieval():
    """‫تست سیستم Retrieval با query های مختلف"""

    try:
        retriever = get_hybrid_retriever()
        log_message( LG.Retrieval, "✅ HybridRetriever ساخته شد", LogLevel.INFO )
    except Exception as e:
        log_message( LG.Retrieval, f"❌ خطا در ساخت Retriever: {str(e)}", LogLevel.ERROR )
        return

    test_queries = [
        "حداقل مزد کارگر در سال 1404 چقدر است؟",
        "شرایط دریافت بیمه بیکاری چیست؟",
        "مرخصی زایمان کارگر زن چند روز است؟",
        "حق سنوات چگونه محاسبه می‌شود؟",
        "سن بازنشستگی در قانون تامین اجتماعی",
        "سلام خوبی؟",
        "آب و هوای تهران چطوره؟",
    ]

    for i, query in enumerate( test_queries, start=1 ):
        log_message( LG.Retrieval, "\n" + "=" * 70, LogLevel.INFO )
        log_message( LG.Retrieval, f"📝 Query #{i}: '{query}'", LogLevel.INFO )
        log_message( LG.Retrieval, "=" * 70, LogLevel.INFO )

        try:
            # ‫مرحله ۱: RRF
            results = retriever.retrieve( query )

            if not results:
                log_message( LG.Retrieval, "⚠️ هیچ نتیجه‌ای پیدا نشد", LogLevel.WARNING )
                continue

            # ‫مرحله ۲: دریافت content از PostgreSQL
            db = SessionLocal()
            pg_manager = PostgresManager( db )
            chunk_ids = [ r[ 'chunk_id' ] for r in results ]
            contents_map = pg_manager.get_chunks_content_bulk( chunk_ids )
            for r in results:
                r[ 'content' ] = contents_map.get( r[ 'chunk_id' ], "" )

            # ‫مرحله ۳: محدود کردن ورودی reranker و rerank
            results = results[ :settings.RERANKER_INPUT_SIZE ]
            results = retriever.rerank( query, results, final_top_k=5 )

            # ‫نمایش نتایج
            log_message( LG.Retrieval, f"\n📊 نتایج (تعداد: {len(results)}):", LogLevel.INFO )
            log_message( LG.Retrieval, "-" * 70, LogLevel.INFO )

            for rank, result in enumerate( results, start=1 ):
                log_message( LG.Retrieval, f"\n🔹 Rank #{rank}", LogLevel.INFO )
                log_message( LG.Retrieval, f"   Chunk ID: {result['chunk_id']}", LogLevel.INFO )
                log_message( LG.Retrieval, f"   RRF Score: {result[RRFKeys.RRF_SCORE]:.4f}", LogLevel.INFO )

                if result[ RRFKeys.BM25_SCORE ] is not None:
                    log_message( LG.Retrieval, f"   BM25 Score: {result[RRFKeys.BM25_SCORE]:.4f} (Rank: {result[RRFKeys.BM25_RANK]})",
                                 LogLevel.DEBUG )
                if result[ RRFKeys.VECTOR_SCORE ] is not None:
                    log_message( LG.Retrieval,
                                 f"   Vector Score: {result[RRFKeys.VECTOR_SCORE]:.4f} (Rank: {result[RRFKeys.VECTOR_RANK]})",
                                 LogLevel.DEBUG )

                reranker_score = result.get( "reranker_score", "N/A" )
                log_message(
                    LG.Retrieval, f"   Reranker Score: {reranker_score:.4f}"
                    if isinstance( reranker_score, float ) else f"   Reranker Score: {reranker_score}", LogLevel.INFO )
                log_message( LG.Retrieval, f"   Methods: {', '.join( result[ ResultKeys.RETRIEVAL_METHOD ] )}", LogLevel.INFO )

                metadata = result.get( "metadata", {} )
                if metadata:
                    log_message( LG.Retrieval, f"   Hierarchy: {metadata.get('hierarchy', 'N/A')}", LogLevel.DEBUG )

                content = result.get( "content", "" )
                if content:
                    preview = content[ :300 ] + "..." if len( content ) > 300 else content
                    log_message( LG.Retrieval, f"   📄 Content Preview:\n      {preview}", LogLevel.INFO )

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
