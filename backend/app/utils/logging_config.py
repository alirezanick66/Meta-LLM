import sys
from enum import Enum
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from loguru import logger

CURRENT_DIR = Path( __file__ ).resolve().parent.parent.parent          # پیدا کردن مسیر ریشه پروژه
LOG_DIR = CURRENT_DIR / "data" / "logs"          # مسیر دایرکتوری لاگ‌ها
LOG_DIR.mkdir( parents=True, exist_ok=True )


class LG( str, Enum ):
    Public = "Public"
    DataProcessing = "DataProcessing"
    Retrieval = "Retrieval"
    LLM = "LLM"
    Reranking = "Reranking"
    API = "API"
    Redis = "Redis"
    Database = "Database"
    Embedding = "Embedding"
    BM25 = "BM25"


class LogLevel( Enum ):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# فرمت لاگ کنسول
CONSOLE_FORMAT = ( "<green>{time:YYYY-MM-DD HH:mm}</green> | <cyan>{extra[category]}</cyan> | "
                   "<level>{level: <8}</level> | <level>{message}</level>{extra[custom_extra]}" )
# فرمت لاگ فایل
FILE_FORMAT = ( "{time:YYYY-MM-DD HH:mm} | {extra[category]} | {level} | {message} {extra[custom_extra]}" )

logger.remove()          # پاک کردن تنظیمات پیش‌فرض loguru

# تغییر استایل و رنگ پیش‌فرض
logger.level( "INFO", color="<white>" )          # فقط سفید، بدون بولد
logger.level( "DEBUG", color="<light-green>" )
logger.level( "WARNING", color="<yellow>" )
logger.level( "ERROR", color="<red>" )
logger.level( "CRITICAL", color="<red><bold>" )

# لاگ کنسول
logger.add(
    sys.stderr,
    format=CONSOLE_FORMAT,
    colorize=True,
    level="DEBUG",
    filter=lambda record: record[ "extra" ].get( "target" ) == "console",
)

# لاگ فایل‌ها برای هر دسته‌بندی
for category in LG:
    logger.add(
        LOG_DIR / f"{category.value.lower()}.log",
        format=FILE_FORMAT,
        level="DEBUG",
        rotation="10 MB",          # چرخش وقتی به 10 مگابایت برسه
        retention=7,          # نگه داشتن 7 فایل بک‌آپ
        encoding="utf-8",          # برای پشتیبانی از فارسی
        filter=lambda record, cat=category.value: record[ "extra" ].get( "category" ) == cat and record[ "extra" ].get(
            "target" ) == "file",
    )


# تابع ثبت لاگ
def log_message( category, message, level=LogLevel.INFO, **kwargs ):
    processed_message = get_display( arabic_reshaper.reshape( message ) )
    extra = { "category": category.value, "custom_extra": str( kwargs ) if kwargs else "" }

    logger.bind( target="console", **extra ).log( level.value, processed_message )          # لاگ برای کنسول
    logger.bind( target="file", **extra ).log( level.value, message )          # لاگ برای فایل
