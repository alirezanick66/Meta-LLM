import time
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from backend.app.schemas.api_schemas import ( ChatRequest, ChatResponse, ChatMetadata, UsageInfo, Source, SystemStats,
                                              LLMProvider )
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.db.postgres import PostgresManager
from backend.app.api.dependencies import get_hybrid_retriever, get_llm_orchestrator
from backend.app.services.retrieval.hybrid_retriever import HybridRetriever
from backend.app.services.llm.llm_orchestrator import LLMOrchestrator
from backend.app.utils.logging_config import log_message, LG, LogLevel
from backend.app.db.qdrant_client import get_qdrant_manager
from backend.app.services.retrieval.bm25_indexer import BM25Indexer

# ==================== Router ====================
router = APIRouter( prefix="/api", tags=[ "API" ] )


# ==================== Chat Endpoint ====================
@router.post( "/chat",
              response_model=ChatResponse,
              status_code=status.HTTP_200_OK,
              summary="ارسال سوال و دریافت پاسخ",
              description="Endpoint اصلی برای چت با سیستم RAG" )
async def chat(
        request: ChatRequest,
        db: Session = Depends( get_db ),
        retriever: HybridRetriever = Depends( get_hybrid_retriever ),          # ✅ Singleton
        orchestrator: LLMOrchestrator = Depends( get_llm_orchestrator )          # ✅ Singleton
) -> ChatResponse:
    """
    پردازش سوال کاربر و تولید پاسخ هوشمند
    
    ✅ بهینه‌سازی‌ها:
    - Dependency Injection برای سرویس‌های سنگین
    - run_in_threadpool برای عملیات sync
    - Bulk query برای دریافت chunks
    """

    start_time = time.time()

    try:
        log_message( LG.API, f"📩 درخواست جدید: '{request.query[:50]}...'", LogLevel.INFO )

        # ==================== مرحله 1: Retrieval (Async-safe) ====================
        log_message( LG.API, "🔍 مرحله 1: Retrieval...", LogLevel.DEBUG )

        # ✅ اجرای sync function در threadpool
        chunks = await run_in_threadpool( retriever.retrieve, query=request.query, final_top_k=settings.RERANKER_TOP_K )

        if not chunks:
            log_message( LG.API, "⚠️ هیچ chunk ای پیدا نشد", LogLevel.WARNING )
            return ChatResponse( success=False,
                                 answer=None,
                                 sources=[],
                                 metadata=None,
                                 error="متأسفانه در اسناد موجود، اطلاعاتی مرتبط با سوال شما پیدا نشد.",
                                 timestamp=datetime.fromtimestamp( time.time() ) )

        log_message( LG.API, f"✅ {len(chunks)} chunk بازیابی شد", LogLevel.DEBUG )

        # ==================== مرحله 2: دریافت Content (Optimized - Bulk Query) ====================
        pg_manager = PostgresManager( db )

        # ✅ استخراج تمام chunk_ids
        chunk_ids = [ chunk[ 'chunk_id' ] for chunk in chunks ]

        # ✅ یک کوئری برای همه (نه N کوئری!)
        contents_map = await run_in_threadpool( pg_manager.get_chunks_content_bulk, chunk_ids )

        # اتصال محتوا به chunks
        for chunk in chunks:
            chunk[ 'content' ] = contents_map.get( chunk[ 'chunk_id' ], "" )

        # ==================== مرحله 3: LLM Generation (Async-safe) ====================
        log_message( LG.API, "🤖 مرحله 2: تولید پاسخ با LLM...", LogLevel.DEBUG )

        # ✅ اجرای sync function در threadpool
        llm_response = await run_in_threadpool( orchestrator.generate_answer,
                                                query=request.query,
                                                chunks=chunks,
                                                temperature=request.temperature,
                                                include_metadata=True )

        # ==================== مرحله 4: ساخت Response ====================
        response_time = time.time() - start_time

        if not llm_response.success:
            log_message( LG.API, f"❌ خطا در تولید پاسخ: {llm_response.error}", LogLevel.ERROR )
            return ChatResponse( success=False,
                                 answer=None,
                                 sources=[],
                                 metadata=None,
                                 error=llm_response.error or "خطای نامشخص در تولید پاسخ",
                                 timestamp=datetime.fromtimestamp( time.time() ) )

        # تبدیل sources به فرمت Pydantic
        sources = [ Source( **src ) for src in llm_response.sources ]

        # ساخت metadata
        metadata = ChatMetadata( provider=LLMProvider( llm_response.provider ) if llm_response.provider else LLMProvider.GROQ,
                                 model=llm_response.model or "unknown",
                                 usage=UsageInfo( prompt_tokens=llm_response.usage.get( 'prompt_tokens', 0 ),
                                                  completion_tokens=llm_response.usage.get( 'completion_tokens', 0 ) ),
                                 is_system_question=llm_response.is_system_question,
                                 retrieval_count=len( chunks ),
                                 response_time=round( response_time, 2 ) )

        log_message( LG.API, f"✅ پاسخ آماده شد - زمان: {response_time:.2f}s", LogLevel.INFO )

        return ChatResponse( success=True,
                             answer=llm_response.answer,
                             sources=sources,
                             metadata=metadata,
                             error=None,
                             timestamp=datetime.fromtimestamp( time.time() ) )

    except Exception as e:
        log_message( LG.API, f"❌ خطای غیرمنتظره در chat endpoint: {str(e)}", LogLevel.ERROR )

        # بررسی نوع خطا برای پیغام مناسب
        if "connection" in str( e ).lower():
            error_msg = "خطا در اتصال به سرویس‌ها. لطفاً بعداً تلاش کنید."
        elif "timeout" in str( e ).lower():
            error_msg = "زمان پردازش بیش از حد طولانی شد. لطفاً دوباره تلاش کنید."
        else:
            error_msg = "خطای داخلی سرور. لطفاً با پشتیبانی تماس بگیرید."

        raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg )


# ==================== Stats Endpoint ====================
@router.get( "/stats",
             response_model=SystemStats,
             status_code=status.HTTP_200_OK,
             summary="دریافت آمار سیستم",
             description="نمایش آمار کلی سیستم (تعداد اسناد، chunks و ...)" )
async def get_stats( db: Session = Depends( get_db ) ) -> SystemStats:
    """
    دریافت آمار کلی سیستم
    """

    try:
        log_message( LG.API, "📊 درخواست آمار سیستم", LogLevel.DEBUG )

        pg_manager = PostgresManager( db )

        # ✅ اجرای موازی تمام queries در threadpool
        def fetch_all_stats():
            """دریافت تمام آمارها به صورت موازی"""
            qdrant_manager = get_qdrant_manager()
            bm25_indexer = BM25Indexer()

            return ( qdrant_manager.get_collection_info(), bm25_indexer.get_stats(), pg_manager.get_total_documents_count(),
                     pg_manager.get_total_chunks_count() )

        qdrant_info, bm25_stats, total_docs, total_chunks = await run_in_threadpool( fetch_all_stats )

        stats = SystemStats( total_documents=total_docs,
                             total_chunks=total_chunks,
                             qdrant_vectors=qdrant_info.get( 'vectors_count', 0 ),
                             bm25_chunks=bm25_stats.get( 'total_chunks', 0 ),
                             embedding_model=settings.EMBEDDING_MODEL,
                             llm_primary=f"{settings.LLM_PRIMARY}: {settings.GROQ_MODEL}" )

        log_message( LG.API, f"✅ آمار ارسال شد: {stats.total_documents} docs", LogLevel.DEBUG )

        return stats

    except Exception as e:
        log_message( LG.API, f"❌ خطا در دریافت آمار: {str(e)}", LogLevel.ERROR )
        raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="خطا در دریافت آمار سیستم" )
