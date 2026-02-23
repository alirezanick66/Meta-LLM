import hashlib
from pathlib import Path
from backend.app.utils.logging_config import log_message, LG, LogLevel


def calculate_file_hash( file_path: str ) -> str:
    """
    محاسبه SHA-256 hash  فایل
    برای تشخیص تغییرات فایل
    
    Args:
        file_path: مسیر فایل
        
    Returns:
        hash string (64 کاراکتر hex)
    """
    try:
        sha256_hash = hashlib.sha256()

        with open( file_path, "rb" ) as f:
            # خواندن فایل به صورت chunk برای فایل‌های بزرگ
            for byte_block in iter( lambda: f.read( 4096 ), b"" ):
                sha256_hash.update( byte_block )

        file_hash = sha256_hash.hexdigest()
        log_message( LG.DataProcessing, f"هش محاسبه شد برای {Path(file_path).name}: {file_hash[:16]}...", LogLevel.DEBUG )
        return file_hash

    except Exception as e:
        log_message( LG.DataProcessing, f"خطا در محاسبه هش فایل {file_path}: {str(e)}", LogLevel.ERROR )
        raise


def verify_file_changed( file_path: str, old_hash: str ) -> bool:
    """
    بررسی تغییر فایل با مقایسه هش‌ها
    
    Args:
        file_path: مسیر فایل
        old_hash: هش قبلی
        
    Returns:
        True اگر فایل تغییر کرده باشد
    """
    try:
        new_hash = calculate_file_hash( file_path )
        return new_hash != old_hash
    except Exception:
        return True          # در صورت خطا، فرض می‌کنیم فایل تغییر کرده
