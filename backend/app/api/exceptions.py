import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, OperationalError

try:
    from httpx import TimeoutException, ConnectError as HttpxConnectError
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

from backend.app.core.config import settings
from backend.app.utils.logging_config import log_message, LG, LogLevel


async def validation_exception_handler( request: Request, exc: RequestValidationError ) -> JSONResponse:
    """مدیریت خطاهای اعتبارسنجی ورودی"""

    errors = exc.errors()
    first_error = errors[ 0 ] if errors else {}

    # استخراج فیلد و پیام با ایمنی بالا
    loc = first_error.get( 'loc', [ 'unknown' ] )
    field = loc[ -1 ] if loc else 'unknown'
    msg = first_error.get( 'msg', 'خطای اعتبارسنجی' )

    log_message( LG.API, f"⚠️ Validation - Path: {request.url.path}, Field: {field}, Msg: {msg}", LogLevel.WARNING )

    # امنیت: فقط در محیط توسعه جزئیات را برمی‌گردانیم
    details = errors if settings.API_RELOAD else "اطلاعات بیشتر برای امنیت مخفی شده است"

    return JSONResponse( status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                         content={
                             "success": False,
                             "error": f"خطا در فیلد '{field}': {msg}",
                             "details": details
                         } )


async def database_exception_handler( request: Request, exc: SQLAlchemyError ) -> JSONResponse:
    """مدیریت خطاهای دیتابیس"""

    log_message( LG.API, f"❌ DB Error on {request.url.path}: {traceback.format_exc()}", LogLevel.ERROR )

    user_message = "خطای دیتابیس"
    if isinstance( exc, OperationalError ):
        user_message = "سرویس دیتابیس در دسترس نیست یا ارتباط قطع شده است"

    return JSONResponse( status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                         content={
                             "success": False,
                             "error": user_message,
                             "details": None
                         } )


async def general_exception_handler( request: Request, exc: Exception ) -> JSONResponse:
    """مدیریت خطاهای عمومی و پیش‌بینی نشده"""

    # لاگ کامل برای دیباگ
    log_message( LG.API, f"❌ Critical Error on {request.url.path}: {traceback.format_exc()}", LogLevel.ERROR )

    # بررسی خطاهای خاص شبکه/زمان در صورت وجود httpx
    if HAS_HTTPX:
        if isinstance( exc, TimeoutException ):
            return JSONResponse( status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                                 content={
                                     "success": False,
                                     "error": "زمان درخواست منقضی شد (Timeout)"
                                 } )

        if isinstance( exc, HttpxConnectError ):
            return JSONResponse( status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                 content={
                                     "success": False,
                                     "error": "ارتباط با سرویس خارجی برقرار نشد"
                                 } )

    # پاسخ پیش‌فرض برای سایر خطاها
    return JSONResponse( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                         content={
                             "success": False,
                             "error": "خطای داخلی سرور رخ داده است",
                             "details": None
                         } )
