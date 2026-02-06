from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import check_db_connection, init_db
from backend.app.db.qdrant_client import qdrant_manager
from backend.app.utils.logging_config import log_message, LG, LogLevel


@asynccontextmanager
async def lifespan( app: FastAPI ):
    """مدیریت lifecycle اپلیکیشن"""

    # Startup
    log_message( LG.API, "=" * 50, LogLevel.INFO )
    log_message( LG.API, "Meta API در حال راه‌اندازی...", LogLevel.INFO )

    # چک کردن اتصال PostgreSQL
    if check_db_connection():
        log_message( LG.Database, "✅ PostgreSQL متصل است", LogLevel.INFO )
        # ایجاد جداول (فقط development)
        init_db()

    else:
        log_message( LG.Database, "❌ خطا در اتصال به PostgreSQL", LogLevel.ERROR )

    # چک کردن Qdrant
    try:
        info = qdrant_manager.get_collection_info()
        log_message( LG.Database, f"✅ Qdrant متصل است - Vectors: {info.get('vectors_count', 0)}", LogLevel.INFO )
    except Exception as e:
        log_message( LG.Database, f"❌ خطا در اتصال به Qdrant: {str(e)}", LogLevel.ERROR )

    log_message( LG.API, f"Embedding Model: {settings.EMBEDDING_MODEL}", LogLevel.INFO )
    log_message( LG.API, f"Device: {settings.EMBEDDING_DEVICE}", LogLevel.INFO )
    log_message( LG.API, "=" * 50, LogLevel.INFO )

    yield

    # Shutdown
    log_message( LG.API, "Meta API در حال خاموش شدن...", LogLevel.WARNING )


app = FastAPI( title="Meta API",
               description="سیستم پرسش و پاسخ هوشمند فارسی - شهرسازی و عمران",
               version="1.0.0",
               docs_url="/docs",
               redoc_url="/redoc",
               lifespan=lifespan )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ "*" ],
    allow_credentials=True,
    allow_methods=[ "*" ],
    allow_headers=[ "*" ],
)


@app.get( "/" )
async def root():
    """Endpoint اصلی برای تست"""
    log_message( LG.API, "درخواست به endpoint اصلی", LogLevel.DEBUG )
    return { "message": "به Meta API خوش آمدید", "status": "running", "version": "1.0.0" }


@app.get( "/health" )
async def health_check():
    """Health check endpoint"""
    db_status = check_db_connection()

    try:
        qdrant_info = qdrant_manager.get_collection_info()
        qdrant_status = True
    except Exception as e:
        log_message( LG.Database, f"❌ خطا در اتصال به Qdrant: {str(e)}", LogLevel.ERROR )
        qdrant_status = False
        qdrant_info = {}

    return {
        "status": "healthy" if ( db_status and qdrant_status ) else "unhealthy",
        "service": "Meta API",
        "postgres": "connected" if db_status else "disconnected",
        "qdrant": "connected" if qdrant_status else "disconnected",
        "qdrant_vectors": qdrant_info.get( "vectors_count", 0 )
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run( "main:app",
                 host=settings.API_HOST,
                 port=settings.API_PORT,
                 reload=settings.API_RELOAD,
                 log_level="info" )
