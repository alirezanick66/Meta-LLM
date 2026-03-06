import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, UploadFile, File
from sqlalchemy.orm import Session

from backend.app.core.database import get_db, SessionLocal
from backend.app.core.config import settings
from fastapi.concurrency import run_in_threadpool
from backend.app.db.postgres import PostgresManager
from backend.app.api.dependencies import ( get_embedding_service, get_hybrid_retriever, get_llm_orchestrator, get_qdrant_indexer,
                                           get_qdrant_manager, get_bm25_indexer, get_tokenizer_service )
from backend.app.schemas.api_schemas import SystemStats, UsageInfo
from backend.app.schemas.base_schemas import LLMProvider
from backend.app.schemas.chat_schemas import ChatMetadata, ChatRequest, ChatResponse, Source
from backend.app.services.document.chunker import MarkdownChunker
from backend.app.services.retrieval.hybrid_retriever import HybridRetriever
from backend.app.services.llm.llm_orchestrator import LLMOrchestrator
from backend.app.utils.logging_config import log_message, LG, LogLevel
from backend.app.services.document.indexing_pipeline import IndexingPipeline
from backend.app.services.document.document_processor import SUPPORTED_EXTENSIONS
import shutil

# ==================== Router ====================
router = APIRouter( prefix="/api", tags=[ "API" ] )


# ==================== Chat Endpoint ====================
@router.post( "/chat",
              response_model=ChatResponse,
              status_code=status.HTTP_200_OK,
              summary="ارسال سوال و دریافت پاسخ",
              description="چت با سیستم" )
async def chat(
    request: ChatRequest,
    db: Session = Depends( get_db ),
    retriever: HybridRetriever = Depends( get_hybrid_retriever ),
    orchestrator: LLMOrchestrator = Depends( get_llm_orchestrator )
) -> ChatResponse:
    """پردازش سوال کاربر و تولید پاسخ هوشمند"""
    start_time = time.time()

    try:
        log_message( LG.API, f"📩 درخواست جدید: '{request.query[:50]}...'", LogLevel.INFO )

        # ==================== مرحله 1: Retrieval ====================
        log_message( LG.API, "🔍 مرحله 1: Retrieval...", LogLevel.DEBUG )
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

        # ==================== مرحله 2: دریافت Content (Bulk Query) ====================
        pg_manager = PostgresManager( db )
        chunk_ids = [ chunk[ 'chunk_id' ] for chunk in chunks ]
        contents_map = await run_in_threadpool( pg_manager.get_chunks_content_bulk, chunk_ids )

        # اتصال محتوا به chunks
        for chunk in chunks:
            chunk[ 'content' ] = contents_map.get( chunk[ 'chunk_id' ], "" )

        # ==================== مرحله 3: LLM Generation ====================
        log_message( LG.API, "🤖 مرحله 2: تولید پاسخ با LLM...", LogLevel.DEBUG )
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

        sources = [
            Source(
                index=src.index,
                chunk_id=src.chunk_id or "",
                source=src.source,
                hierarchy=src.hierarchy,
                content=src.content,
            ) for src in llm_response.sources
        ]

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

        error_msg = "خطای داخلی سرور."
        if "connection" in str( e ).lower():
            error_msg = "خطا در اتصال به سرویس‌ها. لطفاً بعداً تلاش کنید."
        elif "timeout" in str( e ).lower():
            error_msg = "زمان پردازش بیش از حد طولانی شد. لطفاً دوباره تلاش کنید."

        raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg )


# ==================== Stats Endpoint ====================
@router.get( "/stats", response_model=SystemStats, status_code=status.HTTP_200_OK, summary="دریافت آمار سیستم" )
async def get_stats( db: Session = Depends( get_db ) ) -> SystemStats:
    try:
        log_message( LG.API, "📊 درخواست آمار سیستم", LogLevel.DEBUG )
        pg_manager = PostgresManager( db )

        def fetch_all_stats() -> tuple:
            qdrant_manager = get_qdrant_manager()
            bm25_indexer = get_bm25_indexer()
            return (
                qdrant_manager.get_collection_info(),
                bm25_indexer.get_stats(),
                pg_manager.get_total_documents_count(),
                pg_manager.get_total_chunks_count(),
            )

        qdrant_info, bm25_stats, total_docs, total_chunks = await run_in_threadpool( fetch_all_stats )

        return SystemStats( total_documents=total_docs,
                            total_chunks=total_chunks,
                            qdrant_vectors=qdrant_info.get( 'vectors_count', 0 ),
                            bm25_chunks=bm25_stats.get( 'total_chunks', 0 ),
                            embedding_model=settings.EMBEDDING_MODEL,
                            llm_primary=f"{settings.LLM_PRIMARY}: {settings.GROQ_MODEL}" )

    except Exception as e:
        log_message( LG.API, f"❌ خطا در دریافت آمار: {str(e)}", LogLevel.ERROR )
        raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="خطا در دریافت آمار سیستم" )


# ==================== Upload Endpoint ====================
@router.post(
    "/documents/upload",
    status_code=status.HTTP_202_ACCEPTED,
    summary="آپلود و index کردن سند",
    description="آپلود فایل .md یا .docx و شروع خودکار indexing",
)
async def upload_document(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        db: Session = Depends( get_db )          # این سشن فقط برای چک کردن سریع است، در بک‌گراند استفاده نمی‌شود
) -> Dict[ str, Any ]:
    """
    آپلود فایل و indexing در background.
    FIX: اصلاح نشت ارتباط دیتابیس در بک‌گراند.
    """

    if not file.filename:
        raise HTTPException( status_code=status.HTTP_400_BAD_REQUEST, detail="نام فایل نامعتبر است" )

    suffix = Path( file.filename ).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"فرمت '{suffix}' پشتیبانی نمی‌شود. فرمت‌های مجاز: {list(SUPPORTED_EXTENSIONS.keys())}",
        )

    # پیشنهاد: استفاده از تنظیمات برای مسیر ذخیره‌سازی
    documents_dir = documents_dir = Path( settings.DOCUMENTS_DIR )
    documents_dir.mkdir( parents=True, exist_ok=True )
    dest_path = documents_dir / file.filename

    try:
        with open( dest_path, "wb" ) as f:
            shutil.copyfileobj( file.file, f )
    except Exception as e:
        raise HTTPException( status_code=500, detail=f"خطا در ذخیره فایل: {str(e)}" )

    log_message( LG.API, f"📁 فایل '{file.filename}' ذخیره شد", LogLevel.INFO )

    def run_indexing():
        # ایجاد یک سشن کاملاً جدید و مستقل برای ترد بک‌گراند
        # ‫با استفاده از context manager مطمئن می‌شویم که سشن حتماً بسته می‌شود
        with SessionLocal() as bg_db:
            try:
                pipeline = IndexingPipeline(
                    db_session=bg_db,
                    embedding_service=get_embedding_service(),
                    qdrant_indexer=get_qdrant_indexer(),
                    bm25_indexer=get_bm25_indexer(),
                    chunker=MarkdownChunker( tokenizer_service=get_tokenizer_service() ),
                )
                result = pipeline.index_document( str( dest_path ) )
                log_message( LG.API, f"✅ Indexing تکمیل شد: {result}", LogLevel.INFO )
            except Exception as e:
                log_message( LG.API, f"❌ شکست در Indexing بک‌گراند: {str(e)}", LogLevel.ERROR )

    background_tasks.add_task( run_indexing )

    return {
        "success": True,
        "message": f"فایل '{file.filename}' دریافت شد و در حال پردازش است",
        "filename": file.filename,
        "status": "processing",
    }


# ==================== Index Folder Endpoint ====================
@router.post(
    "/documents/index-folder",
    status_code=status.HTTP_200_OK,
    summary="index کردن کل پوشه documents",
)
async def index_folder() -> Dict[ str, Any ]:

    folder_path = getattr( settings, 'DOCUMENTS_DIR', "backend/data/documents" )

    def run():
        with SessionLocal() as db:
            pipeline = IndexingPipeline(
                db_session=db,
                embedding_service=get_embedding_service(),
                qdrant_indexer=get_qdrant_indexer(),
                bm25_indexer=get_bm25_indexer(),
                chunker=MarkdownChunker( tokenizer_service=get_tokenizer_service() ),
            )
            return pipeline.index_folder( folder_path )

    result = await run_in_threadpool( run )
    return {
        "success": True,
        "folder": folder_path,
        "total_found": result[ 'total_found' ],
        "succeeded": result[ 'succeeded' ],
        "replaced": result[ 'replaced' ],
        "skipped": result[ 'skipped' ],
        "failed": result[ 'failed' ],
        "details": result[ 'results' ],
    }


# ==================== List Documents Endpoint ====================
@router.get(
    "/documents",
    status_code=status.HTTP_200_OK,
    summary=" ‫لیست اسناد index شده",
)
async def list_documents( db: Session = Depends( get_db ) ) -> Dict[ str, Any ]:
    """دریافت لیست همه اسناد index‌شده در سیستم"""
    pg_manager = PostgresManager( db )
    documents = await run_in_threadpool( pg_manager.get_all_documents )

    return {
        "success":
        True,
        "total":
        len( documents ),
        "documents": [ {
            "id": doc.id,
            "filename": doc.file_name,
            "total_chunks": doc.total_chunks,
            "indexed_at": doc.indexed_at.isoformat() if doc.indexed_at is not None else None,
        } for doc in documents ],
    }


    # backend/app/api/routes.py
@router.delete( "/documents/{document_id}" )
async def delete_document( document_id: int ) -> Dict[ str, Any ]:

    def run():
        with SessionLocal() as db:
            pipeline = IndexingPipeline(
                db_session=db,
                embedding_service=get_embedding_service(),
                qdrant_indexer=get_qdrant_indexer(),
                bm25_indexer=get_bm25_indexer(),
                chunker=MarkdownChunker( tokenizer_service=get_tokenizer_service() ),
            )
            pipeline._delete_document_data( document_id, rebuild_bm25=True )

    await run_in_threadpool( run )
    return { "success": True }


@router.post( "/documents/bulk-delete" )
async def bulk_delete( body: dict ) -> Dict[ str, Any ]:
    ids = body.get( "ids", [] )

    def run():
        with SessionLocal() as db:
            pipeline = IndexingPipeline(
                db_session=db,
                embedding_service=get_embedding_service(),
                qdrant_indexer=get_qdrant_indexer(),
                bm25_indexer=get_bm25_indexer(),
                chunker=MarkdownChunker( tokenizer_service=get_tokenizer_service() ),
            )
            pg_manager = PostgresManager( db )
            for doc_id in ids:
                pipeline._delete_document_data( doc_id, rebuild_bm25=False )
            # یک بار BM25 rebuild در پایان
            all_chunks = pg_manager.get_all_chunks()
            bm25_indexer = get_bm25_indexer()
            if all_chunks:
                bm25_indexer.rebuild_from_database( all_chunks )
            else:
                bm25_indexer.delete_index()

    await run_in_threadpool( run )
    return { "success": True, "deleted": len( ids ) }
