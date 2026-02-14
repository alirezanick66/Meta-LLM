import sys
import shutil
import subprocess
from pathlib import Path
import time
import argparse
# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent ) )

from backend.app.db.qdrant_client import get_qdrant_manager
from backend.app.services.bm25_indexer import BM25Indexer
from backend.app.utils.logging_config import log_message, LG, LogLevel
from backend.app.core.config import settings


def run_docker_command( command: str, description: str ) -> bool:
    """
    اجرای دستورات Docker با نمایش خروجی
    """
    try:
        log_message( LG.Database, f"🐳 {description}...", LogLevel.INFO )

        result = subprocess.run( command, shell=True, check=True, capture_output=True, text=True )

        if result.stdout:
            log_message( LG.Database, result.stdout, LogLevel.DEBUG )

        log_message( LG.Database, f"✅ {description} با موفقیت انجام شد", LogLevel.INFO )
        return True

    except subprocess.CalledProcessError as e:
        log_message( LG.Database, f"❌ خطا در {description}", LogLevel.ERROR )
        if e.stderr:
            log_message( LG.Database, f"جزئیات خطا: {e.stderr}", LogLevel.ERROR )
        return False


def run_alembic_upgrade() -> bool:
    """
    اجرای alembic upgrade head در virtual environment
    """
    try:
        log_message( LG.Database, "🔄 اجرای alembic upgrade head...", LogLevel.INFO )

        # مسیر venv
        venv_python = Path( ".venv/bin/python" )

        if not venv_python.exists():
            # برای Windows
            venv_python = Path( ".venv/Scripts/python.exe" )

        if not venv_python.exists():
            log_message( LG.Database, "⚠️ Virtual environment پیدا نشد، از python سیستم استفاده می‌کنیم",
                         LogLevel.WARNING )
            command = "alembic upgrade head"
        else:
            command = f"{venv_python} -m alembic upgrade head"

        result = subprocess.run( command, shell=True, check=True, capture_output=True, text=True )

        if result.stdout:
            log_message( LG.Database, result.stdout, LogLevel.INFO )

        log_message( LG.Database, "✅ Migration با موفقیت اجرا شد", LogLevel.INFO )
        return True

    except subprocess.CalledProcessError as e:
        log_message( LG.Database, "❌ خطا در اجرای alembic upgrade", LogLevel.ERROR )
        if e.stderr:
            log_message( LG.Database, f"جزئیات خطا: {e.stderr}", LogLevel.ERROR )
        if e.stdout:
            log_message( LG.Database, f"خروجی: {e.stdout}", LogLevel.ERROR )
        return False


def cleanup_qdrant_and_bm25( restart_services: bool = True ):
    """
    پاکسازی کامل Qdrant collection و BM25 index
    به همراه restart سرویس‌های Docker و اجرای migration
    
    Args:
        restart_services: اگر True باشه، سرویس‌ها رو restart می‌کنه
    """

    log_message( LG.Database, "=" * 70, LogLevel.INFO )
    log_message( LG.Database, "🗑️ شروع پاکسازی کامل Qdrant و BM25", LogLevel.INFO )
    log_message( LG.Database, "=" * 70, LogLevel.INFO )

    try:
        # مرحله 1: توقف سرویس‌ها (اگر درخواست شده)
        if restart_services:
            log_message( LG.Database, "\n🔸 مرحله 1: توقف سرویس‌های Docker", LogLevel.INFO )
            if not run_docker_command( "docker-compose down -v", "توقف و حذف volumes" ):
                log_message( LG.Database, "⚠️ هشدار: مشکل در توقف سرویس‌ها، ادامه می‌دهیم...", LogLevel.WARNING )

        # مرحله 2: پاک کردن فایل‌های محلی
        log_message( LG.Database, "\n🔸 مرحله 2: پاک کردن فایل‌های محلی", LogLevel.INFO )

        # پاک کردن BM25 index files
        log_message( LG.Database, "🔹 پاک کردن BM25 index files...", LogLevel.INFO )
        bm25_indexer = BM25Indexer()
        bm25_indexer.delete_index()
        log_message( LG.Database, "✅ BM25 index files حذف شد", LogLevel.INFO )

        # پاک کردن cache directory (اگر وجود داره)
        cache_dir = Path( "./cache" )
        if cache_dir.exists():
            shutil.rmtree( cache_dir )
            log_message( LG.Database, "✅ Cache directory حذف شد", LogLevel.INFO )

        # مرحله 3: راه‌اندازی مجدد سرویس‌ها
        if restart_services:
            log_message( LG.Database, "\n🔸 مرحله 3: راه‌اندازی مجدد سرویس‌ها", LogLevel.INFO )
            if not run_docker_command( "docker-compose up -d", "راه‌اندازی سرویس‌ها" ):
                log_message( LG.Database, "❌ خطا در راه‌اندازی سرویس‌ها", LogLevel.ERROR )
                return False

            # صبر کردن برای آماده شدن سرویس‌ها

            log_message( LG.Database, "⏳ صبر برای آماده شدن سرویس‌ها (20 ثانیه)...", LogLevel.INFO )
            time.sleep( 20 )

            # اجرای alembic migration
            log_message( LG.Database, "\n🔸 مرحله 3.5: اجرای Database Migration", LogLevel.INFO )
            if not run_alembic_upgrade():
                log_message( LG.Database, "⚠️ هشدار: مشکل در migration، ولی ادامه می‌دهیم...", LogLevel.WARNING )

        # مرحله 4: پاکسازی Qdrant
        log_message( LG.Database, "\n🔸 مرحله 4: پاکسازی Qdrant collection", LogLevel.INFO )

        qdrant_manager = get_qdrant_manager()

        if qdrant_manager.client:
            try:
                # حذف collection
                qdrant_manager.client.delete_collection( collection_name=settings.QDRANT_COLLECTION_NAME )
                log_message( LG.Database, f"✅ Collection '{settings.QDRANT_COLLECTION_NAME}' حذف شد", LogLevel.INFO )
            except Exception as e:
                log_message( LG.Database, f"⚠️ Collection وجود نداشت یا خطا: {str(e)}", LogLevel.WARNING )

            # ساخت مجدد collection خالی
            qdrant_manager._create_collection_if_not_exists()
            log_message( LG.Database, "✅ Collection جدید (خالی) ساخته شد", LogLevel.INFO )

        # مرحله 5: نمایش وضعیت نهایی
        log_message( LG.Database, "\n" + "=" * 70, LogLevel.INFO )
        log_message( LG.Database, "📊 وضعیت نهایی:", LogLevel.INFO )
        log_message( LG.Database, "=" * 70, LogLevel.INFO )

        qdrant_info = qdrant_manager.get_collection_info()
        log_message( LG.Database, f"   ✓ Qdrant Vectors: {qdrant_info.get('vectors_count', 0)}", LogLevel.INFO )

        bm25_stats = bm25_indexer.get_stats()
        log_message( LG.Database, f"   ✓ BM25 Chunks: {bm25_stats.get('total_chunks', 0)}", LogLevel.INFO )

        log_message( LG.Database, "=" * 70, LogLevel.INFO )
        log_message( LG.Database, "✅ پاکسازی کامل با موفقیت انجام شد! 🎉", LogLevel.INFO )
        log_message( LG.Database, "=" * 70, LogLevel.INFO )

        return True

    except Exception as e:
        log_message( LG.Database, f"❌ خطا در پاکسازی: {str(e)}", LogLevel.ERROR )
        import traceback
        log_message( LG.Database, traceback.format_exc(), LogLevel.ERROR )
        return False


if __name__ == "__main__":

    parser = argparse.ArgumentParser( description="🗑️ پاکسازی کامل Qdrant و BM25" )
    parser.add_argument( "--no-restart", action="store_true", help="بدون restart کردن سرویس‌های Docker" )

    args = parser.parse_args()

    success = cleanup_qdrant_and_bm25( restart_services=not args.no_restart )

    if success:
        log_message( LG.Database, "\n💡 مراحل بعدی:", LogLevel.INFO )
        log_message( LG.Database, "=" * 70, LogLevel.INFO )
        log_message( LG.Database, "1️⃣ حذف documents از PostgreSQL:", LogLevel.INFO )
        log_message( LG.Database, "   DELETE FROM documents;", LogLevel.INFO )
        log_message( LG.Database, "", LogLevel.INFO )
        log_message( LG.Database, "2️⃣ اجرای indexing مجدد:", LogLevel.INFO )
        log_message( LG.Database, "   python scripts/test_full_indexing.py", LogLevel.INFO )
        log_message( LG.Database, "=" * 70, LogLevel.INFO )
    else:
        log_message( LG.Database, "\n❌ پاکسازی با خطا مواجه شد", LogLevel.ERROR )
        sys.exit( 1 )
