import argparse, subprocess, sys, time, traceback
from pathlib import Path
import psycopg2
import urllib.request

sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent ) )

from backend.app.services.vector.qdrant_client import QdrantManager
from backend.app.services.retrieval.bm25_indexer import BM25Indexer
from backend.app.utils.logging_config import log_message, LG, LogLevel
from backend.app.core.config import settings


def run_cmd( cmd: str, desc: str, check: bool = True ) -> bool:
    """‫ اجرای دستور shell """
    log_message( LG.Database, f"🚀 {desc}...", LogLevel.INFO )
    try:
        result = subprocess.run( cmd, shell=True, capture_output=True, text=True, check=check )
        if result.stdout:
            log_message( LG.Database, result.stdout, LogLevel.DEBUG )
        log_message( LG.Database, f"✅ {desc}", LogLevel.INFO )
        return True
    except subprocess.CalledProcessError as e:
        log_message( LG.Database, f"❌ {desc} - خطا: {e.stderr}", LogLevel.ERROR )
        return False


def run_alembic() -> bool:
    """‫ اجرای database migration"""
    return run_cmd( "alembic upgrade head", "Database Migration" )


# ==================== Private Func ====================
def _check_postgres() -> bool:
    """‫ چک واقعی اتصال به PostgreSQL   """
    try:
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            dbname=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            connect_timeout=2,
        )
        conn.close()
        return True
    except Exception:
        return False


def _check_qdrant() -> bool:
    """‫ چک واقعی اتصال به Qdrant با HTTP API"""
    try:

        req = urllib.request.urlopen( "http://localhost:6333/collections", timeout=2 )
        return req.status == 200
    except Exception:
        return False


def _wait_for_services( max_retries: int = 20, delay: int = 5 ) -> bool:
    """‫ صبر هوشمند برای آماده شدن واقعی همه سرویس‌ها"""
    log_message( LG.Database, f"⏳ صبر برای آماده شدن سرویس‌ها (حداکثر {max_retries * delay} ثانیه)...", LogLevel.INFO )

    checks = {
        "Qdrant": _check_qdrant,
        "PostgreSQL": _check_postgres,
    }

    for attempt in range( 1, max_retries + 1 ):
        results = { name: fn() for name, fn in checks.items() }

        if all( results.values() ):
            log_message( LG.Database, f"✅ همه سرویس‌ها آماده‌اند (تلاش {attempt})", LogLevel.INFO )
            return True

        not_ready = [ name for name, ok in results.items() if not ok ]
        log_message( LG.Database, f"🔄 تلاش {attempt}/{max_retries} - در انتظار: {', '.join(not_ready)}", LogLevel.DEBUG )
        time.sleep( delay )

    log_message( LG.Database, "❌ سرویس‌ها در زمان مقرر آماده نشدند", LogLevel.ERROR )
    return False


# ==================== Steps ====================


def _reset_qdrant( qdrant: QdrantManager ) -> None:
    """‫ حذف و بازسازی Qdrant collection"""
    try:
        qdrant.client.delete_collection( settings.QDRANT_COLLECTION_NAME )          # type: ignore
        log_message( LG.Database, f"✅ Collection '{settings.QDRANT_COLLECTION_NAME}' حذف شد", LogLevel.INFO )
    except Exception:
        log_message( LG.Database, "⚠️ Collection وجود نداشت", LogLevel.WARNING )

    qdrant._create_collection_if_not_exists()
    log_message( LG.Database, "✅ Collection جدید (خالی) ساخته شد", LogLevel.INFO )


# ==================== Main ====================


def cleanup( restart: bool = True ) -> bool:
    """
    ‫ پاکسازی کامل Qdrant collection و BM25 index

    ‫ ترتیب عملیات:
    ‫ 1. پاکسازی BM25 (محلی، همیشه)
    ‫ 2. restart سرویس‌های Docker (اختیاری)
    ‫ 3. صبر برای آماده شدن واقعی سرویس‌ها
    ‫ 4. پاکسازی Qdrant (بعد از restart)
    ‫ 5. اجرای migration

    Args:
        restart: ‫اگر True باشه سرویس‌های Docker رو restart می‌کنه
    """
    log_message( LG.Database, "🗑️ شروع پاکسازی کامل", LogLevel.INFO )

    bm25 = BM25Indexer()

    try:
        # ==================== 1. پاکسازی BM25 ====================
        log_message( LG.Database, "\n🔸 مرحله 1: پاکسازی BM25...", LogLevel.INFO )
        bm25.delete_index()

        if not restart:
            # ‫بدون restart — Qdrant رو مستقیم پاک کن
            qdrant = QdrantManager()
            _reset_qdrant( qdrant )
            return True

        # ==================== 2. Restart سرویس‌ها ====================
        log_message( LG.Database, "\n🔸 مرحله 2: restart سرویس‌های Docker...", LogLevel.INFO )

        if not run_cmd( "docker compose down -v", "Stop services", check=False ):
            log_message( LG.Database, "⚠️ توقف با مشکل مواجه شد، ادامه می‌دهیم...", LogLevel.WARNING )

        if not run_cmd( "docker compose up -d", "Start services" ):
            return False

        # ==================== 3. صبر برای آماده شدن ====================
        if not _wait_for_services():
            log_message( LG.Database, "❌ سرویس‌ها آماده نشدند", LogLevel.ERROR )
            return False

        # ==================== 4. پاکسازی Qdrant ====================
        # ‫بعد از restart ساخته میشه تا connection جدید و تازه باشه
        log_message( LG.Database, "\n🔸 مرحله 3: پاکسازی Qdrant...", LogLevel.INFO )
        qdrant = QdrantManager()
        _reset_qdrant( qdrant )

        # ==================== 5. Migration ====================
        log_message( LG.Database, "\n🔸 مرحله 4: اجرای migration...", LogLevel.INFO )
        if not run_alembic():
            log_message( LG.Database, "⚠️ migration با مشکل مواجه شد، ادامه می‌دهیم...", LogLevel.WARNING )

        log_message( LG.Database, "✅ پاکسازی با موفقیت انجام شد! 🎉", LogLevel.INFO )
        return True

    except Exception as e:
        log_message( LG.Database, f"❌ خطا در پاکسازی: {str(e)}", LogLevel.ERROR )
        log_message( LG.Database, traceback.format_exc(), LogLevel.ERROR )
        return False


# ==================== Entry Point ====================

if __name__ == "__main__":
    parser = argparse.ArgumentParser( description="🗑️ پاکسازی کامل Qdrant و BM25" )
    parser.add_argument( "--no-restart", action="store_true", help="بدون restart کردن سرویس‌های Docker" )
    args = parser.parse_args()

    if cleanup( restart=not args.no_restart ):
        log_message( LG.Database, "💡 مراحل بعدی:", LogLevel.INFO )
        log_message( LG.Database, "=" * 70, LogLevel.INFO )
        log_message( LG.Database, "1️⃣  اجرای indexing مجدد:", LogLevel.INFO )
        log_message( LG.Database, "    python scripts/test_full_indexing.py", LogLevel.INFO )
        log_message( LG.Database, "2️⃣  راه‌اندازی API:", LogLevel.INFO )
        log_message( LG.Database, "    uvicorn backend.app.main:app --reload", LogLevel.INFO )
    else:
        sys.exit( 1 )
