import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent ) )
from backend.app.utils.logging_config import log_message, LG, LogLevel
from backend.app.services.llm.gemini_client import create_gemini_client, get_gemini_model_list


def test_gemini_client():
    log_message( LG.LLM, "شروع تست GeminiClient...", LogLevel.INFO )

    try:

        gemini_client = create_gemini_client()
        response = gemini_client.generate( "سلام داداش خوبی ؟" )
        log_message( LG.LLM, f"پاسخ Gemini: {response}", LogLevel.INFO )
    except Exception as e:
        log_message( LG.LLM, f"❌ خطا در تست GeminiClient: {str(e)}", LogLevel.ERROR )


test_gemini_client()
# get_gemini_model_list()
