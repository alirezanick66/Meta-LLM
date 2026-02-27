from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings

#‫برای اتصال به پایگاه داده PostgreSQL
engine = create_engine(
    settings.postgres_url,
    echo=settings.POSTGRES_ECHO,          #برای دیدن کوئری های اجرا شده
    pool_pre_ping=True,          #برای بررسی اتصال، قبل از استفاده از آن
    pool_size=5,          #تعداد کانکشن های همزمان
    max_overflow=10,          #تعداد کانکشن های اضافی در صورت نیاز
    pool_recycle=3600 )

#Session
SessionLocal = sessionmaker( autocommit=False, autoflush=False, bind=engine )

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_db_connection():
    """بررسی اتصال به پایگاه داده"""
    try:
        with engine.connect() as connection:
            connection.execute( text( "SELECT 1" ) )
        return True
    except Exception:
        return False
