from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from backend.app.api.dependencies import ( get_qdrant_manager, get_embedding_service, get_bm25_indexer, get_llm_orchestrator,
                                           get_hybrid_retriever, get_tokenizer_service )
from backend.app.core.config import settings
from backend.app.core.database import check_db_connection
from backend.app.utils.logging_config import log_message, LG, LogLevel

# Import API routes و exception handlers
from backend.app.api.routes import router as api_router
from backend.app.api.exceptions import ( validation_exception_handler, database_exception_handler, general_exception_handler )


@asynccontextmanager
async def lifespan( app: FastAPI ):
    """ ‫مدیریت lifecycle اپلیکیشن"""

    # ==================== Startup ====================
    log_message( LG.API, "=" * 70, LogLevel.INFO )
    log_message( LG.API, "🚀 Meta API در حال راه‌اندازی...", LogLevel.INFO )
    log_message( LG.API, "=" * 70, LogLevel.INFO )

    # ‫چک اتصال PostgreSQL
    if check_db_connection():
        log_message( LG.Database, "✅ PostgreSQL متصل است", LogLevel.INFO )
    else:
        log_message( LG.Database, "❌ خطا در اتصال به PostgreSQL", LogLevel.ERROR )
        raise RuntimeError( "Cannot start without Database connection" )

    # ‫چک اتصال Qdrant
    try:
        qdrant_manager = get_qdrant_manager()
        info = qdrant_manager.get_collection_info()
        vectors_count = info.get( 'vectors_count', 0 )
        log_message( LG.Database, f"✅ Qdrant متصل است - Vectors: {vectors_count}", LogLevel.INFO )
    except Exception as e:
        log_message( LG.Database, f"❌ خطا در اتصال به Qdrant: {str(e)}", LogLevel.ERROR )
        raise RuntimeError( f"Cannot start without Qdrant: {str(e)}" )

    log_message( LG.API, "⏳ در حال بارگذاری سرویس‌ها...", LogLevel.INFO )

    try:
        get_tokenizer_service()
        get_embedding_service()
        get_bm25_indexer()
        get_llm_orchestrator()
        get_hybrid_retriever()
        log_message( LG.API, "✅ همه سرویس‌ها آماده‌اند", LogLevel.INFO )

    except Exception as e:
        log_message( LG.API, f"❌ خطا در بارگذاری سرویس‌ها: {str(e)}", LogLevel.ERROR )
        raise RuntimeError( f"Cannot start without services: {str(e)}" )

    # نمایش تنظیمات
    log_message( LG.API, f"🤖 Embedding Model: {settings.EMBEDDING_MODEL}", LogLevel.INFO )
    log_message( LG.API, f"💻 Device: {settings.EMBEDDING_DEVICE}", LogLevel.INFO )
    log_message( LG.API, f"🚀 LLM Primary: {settings.LLM_PRIMARY} ({settings.GROQ_MODEL})", LogLevel.INFO )
    log_message( LG.API, f"🔄 LLM Fallback: {settings.LLM_FALLBACK} ({settings.GEMINI_MODEL})", LogLevel.INFO )
    log_message( LG.API, f"🌡️ Temperature: {settings.TEMPERATURE}", LogLevel.INFO )
    log_message( LG.API, "=" * 70, LogLevel.INFO )
    log_message( LG.API, "✅ Meta API آماده است!", LogLevel.INFO )
    log_message( LG.API, "📚 Docs: http://localhost:8000/docs", LogLevel.INFO )
    log_message( LG.API, "=" * 70, LogLevel.INFO )

    yield

    # ==================== Shutdown ====================
    log_message( LG.API, "🛑 Meta API در حال خاموش شدن...", LogLevel.WARNING )


# ==================== FastAPI App ====================
app = FastAPI( title="Meta API",
               description="سیستم پرسش و پاسخ هوشمند فارسی - شهرسازی و عمران",
               version="1.0.0",
               docs_url="/docs",
               redoc_url="/redoc",
               lifespan=lifespan )

# ==================== CORS Middleware ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ "*" ],          # ‫⚠️ در production باید محدود شود
    allow_credentials=True,
    allow_methods=[ "*" ],
    allow_headers=[ "*" ] )

# ==================== Exception Handlers ====================
app.exception_handler( RequestValidationError )( validation_exception_handler )
app.exception_handler( SQLAlchemyError )( database_exception_handler )
app.exception_handler( Exception )( general_exception_handler )

# ==================== Include Routers ====================
app.include_router( api_router )


# ==================== Root Endpoints ====================
@app.get( "/" )
async def root():
    """
    ‫Endpoint اصلی برای تست و راهنما
    """
    log_message( LG.API, "📨 درخواست به root endpoint", LogLevel.DEBUG )

    return {
        "message": "به Meta API خوش آمدید",
        "status": "running",
        "version": "1.0.0",
        "description": "سیستم پرسش و پاسخ هوشمند فارسی - شهرسازی و عمران",
        "docs": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "chat": {
                "url": "/api/chat",
                "method": "POST",
                "description": "ارسال سوال و دریافت پاسخ هوشمند"
            },
            "stats": {
                "url": "/api/stats",
                "method": "GET",
                "description": "دریافت آمار سیستم"
            },
            "health": {
                "url": "/health",
                "method": "GET",
                "description": "بررسی وضعیت سرویس‌ها"
            }
        }
    }


@app.get( "/health" )
async def health_check():
    """
    Health check endpoint برای monitoring
    """
    log_message( LG.API, "🏥 Health check request", LogLevel.DEBUG )

    # چک PostgreSQL
    db_status = check_db_connection()

    # چک Qdrant
    try:
        qdrant_manager = get_qdrant_manager()
        qdrant_info = qdrant_manager.get_collection_info()
        qdrant_status = True
        vectors_count = qdrant_info.get( 'vectors_count', 0 )
    except Exception as e:
        log_message( LG.Database, f"❌ Qdrant health check failed: {str(e)}", LogLevel.ERROR )
        qdrant_status = False
        vectors_count = 0

    # تعیین وضعیت کلی
    overall_status = "healthy" if ( db_status and qdrant_status ) else "unhealthy"

    return {
        "status": overall_status,
        "service": "Meta API",
        "version": "1.0.0",
        "components": {
            "postgres": "connected" if db_status else "disconnected",
            "qdrant": "connected" if qdrant_status else "disconnected",
            "redis": "not_implemented"          # فاز 7
        },
        "metrics": {
            "qdrant_vectors": vectors_count
        }
    }


# ==================== Main Entry Point ====================
if __name__ == "__main__":
    import uvicorn

    log_message( LG.API, "🚀 Starting uvicorn server...", LogLevel.INFO )

    uvicorn.run( "backend.app.main:app",
                 host=settings.API_HOST,
                 port=settings.API_PORT,
                 reload=settings.API_RELOAD,
                 log_level="info" )
