from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings
from backend.app.utils.logging_config import LG, LogLevel, log_message

#برای اتصال به پایگاه داده PostgreSQL
engine = create_engine(
    settings.postgres_url,
    echo=False,          #برای دیدن کوئری های اجرا شده
    pool_pre_ping=True,          #برای بررسی اتصال، قبل از استفاده از آن
    pool_size=10,          #تعداد کانکشن های همزمان
    max_overflow=20,          #تعداد کانکشن های اضافی در صورت نیاز
)
#Session Factory
SessionLocal = sessionmaker( autocommit=False, autoflush=False, bind=engine )

Base = declarative_base()


def get_db():
    """ گرفتن دیتابیس با استفاده از سیشن"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """ایجاد جداول در پایگاه داده"""
    try:
        Base.metadata.create_all( bind=engine )
        log_message( LG.Database, "جداول دیتابیس با موفقیت ایجاد شدند.", LogLevel.INFO )
    except Exception as e:
        log_message( LG.Database, f"خطا در ایجاد جداول دیتابیس: {e}", LogLevel.ERROR )


def check_db_connection():
    """بررسی اتصال به پایگاه داده"""
    try:
        with engine.connect() as connection:
            connection.execute( text( "SELECT 1" ) )
        log_message( LG.Database, "اتصال به دیتابیس برقرار شد.", LogLevel.INFO )
        return True
    except Exception as e:
        log_message( LG.Database, f"خطا در اتصال به دیتابیس: {e}", LogLevel.ERROR )
        return False
