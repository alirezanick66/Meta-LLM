import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent ) )
from backend.app.utils.logging_config import log_message, LG, LogLevel
from backend.app.services.llm.groq_client import create_groq_client


def test_groq_client():
    """
    تست اولیه GroqClient:
    1. ساخت کلاینت
    2. ارسال یک پرامپت ساده
    3. بررسی پاسخ
    """

    try:
        # 1. ساخت کلاینت
        log_message( LG.LLM, "🤖 ساخت GroqClient...", LogLevel.INFO )
        groq_client = create_groq_client()
        log_message( LG.LLM, "✅ GroqClient آماده شد", LogLevel.INFO )

        # 2. ارسال یک پرامپت ساده
        test_prompt = "رییس جمهور فعلی امریکا کیه؟"
        log_message( LG.LLM, f"📨 ارسال پرامپت: '{test_prompt}'", LogLevel.INFO )
        response = groq_client.generate( test_prompt )

        # 3. بررسی پاسخ
        if response[ "success" ]:
            log_message( LG.LLM, f"✅ پاسخ دریافت شد: {response['content']}", LogLevel.INFO )
            log_message( LG.LLM, f"📊 Usage: {response['usage']}", LogLevel.INFO )
        else:
            log_message( LG.LLM, f"❌ خطا در تولید پاسخ: {response['error']}", LogLevel.ERROR )

    except Exception as e:
        log_message( LG.LLM, f"❌ خطا در تست GroqClient: {str(e)}", LogLevel.ERROR )


test_groq_client()
