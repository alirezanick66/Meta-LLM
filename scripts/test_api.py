import sys
import argparse
from pathlib import Path
import requests
import json

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent ) )

from backend.app.utils.logging_config import log_message, LG, LogLevel

# ==================== Config ====================
parser = argparse.ArgumentParser( description="Test Meta API Endpoints" )
parser.add_argument( "--url", default="http://localhost:8000", help="Base URL of the API server" )
parser.add_argument( "--timeout", type=int, default=30, help="Request timeout in seconds" )
parser.add_argument( "--verbose", action="store_true", help="Enable verbose output" )
args = parser.parse_args()

BASE_URL = args.url
API_BASE = f"{BASE_URL}/api"
TIMEOUT = args.timeout
VERBOSE = args.verbose

# شمارنده تست‌ها
PASSED_TESTS = 0
FAILED_TESTS = 0

# ==================== Helper Functions ====================


def log_result( test_name: str, passed: bool, error_msg: str = "" ):
    """ثبت نتیجه تست"""
    global PASSED_TESTS, FAILED_TESTS

    if passed:
        PASSED_TESTS += 1
        log_message( LG.API, f"✅ {test_name}: PASSED", LogLevel.INFO )
    else:
        FAILED_TESTS += 1
        log_message( LG.API, f"❌ {test_name}: FAILED", LogLevel.ERROR )
        if error_msg:
            log_message( LG.API, f"   Error: {error_msg}", LogLevel.ERROR )


def safe_request( method: str, endpoint: str, **kwargs ):
    """
    ارسال درخواست با error handling
    
    Args:
        method: GET, POST, etc.
        endpoint: مسیر endpoint (مثلاً "/api/chat")
        **kwargs: پارامترهای اضافی برای requests
    """
    url = f"{BASE_URL}{endpoint}"
    kwargs.setdefault( "timeout", TIMEOUT )

    try:
        if method.upper() == "GET":
            return requests.get( url, **kwargs )
        elif method.upper() == "POST":
            kwargs.setdefault( "headers", { "Content-Type": "application/json" } )
            return requests.post( url, **kwargs )
        else:
            raise ValueError( f"Unsupported method: {method}" )

    except requests.exceptions.Timeout:
        log_message( LG.API, f"⏱️ Timeout calling {url}", LogLevel.WARNING )
        return None
    except requests.exceptions.ConnectionError:
        log_message( LG.API, f"🔌 Connection error calling {url}", LogLevel.ERROR )
        return None
    except requests.exceptions.RequestException as e:
        log_message( LG.API, f"⚠️ Network error calling {url}: {str(e)}", LogLevel.ERROR )
        return None


# ==================== Test Functions ====================


def test_root() -> bool:
    """تست endpoint اصلی"""
    test_name = "Root Endpoint"
    log_message( LG.API, f"\n🧪 {test_name}", LogLevel.INFO )

    try:
        response = safe_request( "GET", "" )

        if not response:
            raise Exception( "No response from server" )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "message" in data, "Missing 'message' field"
        assert "status" in data, "Missing 'status' field"
        assert data[ "status" ] == "running", f"Expected status='running', got '{data['status']}'"

        if VERBOSE:
            log_message( LG.API, f"Response: {json.dumps(data, ensure_ascii=False, indent=2)}", LogLevel.DEBUG )

        log_result( test_name, True )
        return True

    except AssertionError as e:
        log_result( test_name, False, str( e ) )
        return False
    except Exception as e:
        log_result( test_name, False, str( e ) )
        return False


def test_health() -> bool:
    """تست health check"""
    test_name = "Health Check"
    log_message( LG.API, f"\n🧪 {test_name}", LogLevel.INFO )

    try:
        response = safe_request( "GET", "/health" )

        if not response:
            raise Exception( "No response from server" )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "status" in data, "Missing 'status' field"
        assert data[ "status" ] in [ "healthy", "unhealthy" ], f"Invalid status: {data['status']}"

        # بررسی components
        if "components" in data:
            components = data[ "components" ]
            log_message( LG.API, f"   PostgreSQL: {components.get('postgres', 'unknown')}", LogLevel.INFO )
            log_message( LG.API, f"   Qdrant: {components.get('qdrant', 'unknown')}", LogLevel.INFO )

        log_result( test_name, True )
        return True

    except AssertionError as e:
        log_result( test_name, False, str( e ) )
        return False
    except Exception as e:
        log_result( test_name, False, str( e ) )
        return False


def test_stats() -> bool:
    """تست stats endpoint"""
    test_name = "Stats Endpoint"
    log_message( LG.API, f"\n🧪 {test_name}", LogLevel.INFO )

    try:
        response = safe_request( "GET", "/api/stats" )

        if not response:
            raise Exception( "No response from server" )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        required_fields = [ "total_documents", "total_chunks", "qdrant_vectors", "bm25_chunks" ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        if VERBOSE:
            log_message( LG.API, f"   Documents: {data['total_documents']}", LogLevel.INFO )
            log_message( LG.API, f"   Chunks: {data['total_chunks']}", LogLevel.INFO )
            log_message( LG.API, f"   Vectors: {data['qdrant_vectors']}", LogLevel.INFO )

        log_result( test_name, True )
        return True

    except AssertionError as e:
        log_result( test_name, False, str( e ) )
        return False
    except Exception as e:
        log_result( test_name, False, str( e ) )
        return False


def test_chat_rag() -> bool:
    """تست chat endpoint با سوال RAG"""
    test_name = "Chat RAG Question"
    log_message( LG.API, f"\n🧪 {test_name}", LogLevel.INFO )

    payload = { "query": "انقلاب اسلامی چه تأثیری بر نظریه‌های غربی گذاشت؟", "temperature": 0.3 }

    log_message( LG.API, f"   Query: {payload['query'][:50]}...", LogLevel.INFO )

    try:
        response = safe_request( "POST", "/api/chat", json=payload )

        if not response:
            raise Exception( "No response from server" )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "success" in data, "Missing 'success' field"
        assert data[ "success" ] is True, f"API returned success={data['success']}"
        assert "answer" in data, "Missing 'answer' field"
        assert data[ "answer" ], "Answer is empty"
        assert "metadata" in data, "Missing 'metadata' field"

        # بررسی metadata
        meta = data[ "metadata" ]
        assert "provider" in meta, "Missing 'provider' in metadata"
        assert "response_time" in meta, "Missing 'response_time' in metadata"

        log_message( LG.API, f"   Provider: {meta['provider']}", LogLevel.INFO )
        log_message( LG.API, f"   Response Time: {meta['response_time']}s", LogLevel.INFO )
        log_message( LG.API, f"   Sources: {len(data.get('sources', []))}", LogLevel.INFO )

        if VERBOSE:
            answer_preview = data[ "answer" ][ :200 ] + "..." if len( data[ "answer" ] ) > 200 else data[ "answer" ]
            log_message( LG.API, f"   Answer: {answer_preview}", LogLevel.DEBUG )

        log_result( test_name, True )
        return True

    except AssertionError as e:
        log_result( test_name, False, str( e ) )
        return False
    except Exception as e:
        log_result( test_name, False, str( e ) )
        return False


def test_chat_system() -> bool:
    """تست chat endpoint با سوال سیستمی"""
    test_name = "Chat System Question"
    log_message( LG.API, f"\n🧪 {test_name}", LogLevel.INFO )

    payload = { "query": "تو کی هستی؟" }

    log_message( LG.API, f"   Query: {payload['query']}", LogLevel.INFO )

    try:
        response = safe_request( "POST", "/api/chat", json=payload )

        if not response:
            raise Exception( "No response from server" )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data.get( "success" ) is True, "Expected success=True"
        assert data.get( "answer" ), "Answer is empty"

        # بررسی تشخیص سوال سیستمی
        meta = data.get( "metadata", {} )
        is_system = meta.get( "is_system_question", False )
        assert is_system is True, "Should be detected as system question"

        log_message( LG.API, f"   System Question: {is_system}", LogLevel.INFO )

        if VERBOSE:
            log_message( LG.API, f"   Answer: {data['answer']}", LogLevel.DEBUG )

        log_result( test_name, True )
        return True

    except AssertionError as e:
        log_result( test_name, False, str( e ) )
        return False
    except Exception as e:
        log_result( test_name, False, str( e ) )
        return False


def test_validation_error() -> bool:
    """تست validation error handling"""
    test_name = "Validation Error Handling"
    log_message( LG.API, f"\n🧪 {test_name}", LogLevel.INFO )

    payload = {
        "query": "",          # خالی
        "temperature": 5.0          # خارج از محدوده
    }

    try:
        response = safe_request( "POST", "/api/chat", json=payload )

        # ✅ اصلاح: چک کن که response وجود داره یا نه
        if response is None:
            raise Exception( "Network error - no response" )

        # ✅ اینجا response وجود داره (حتی اگه 422 باشه)
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"

        data = response.json()
        assert "error" in data or "detail" in data, "Missing error field"

        log_result( test_name, True )
        return True

    except AssertionError as e:
        log_result( test_name, False, str( e ) )
        return False
    except Exception as e:
        log_result( test_name, False, str( e ) )
        return False


# ==================== Main ====================


def run_all_tests():
    """اجرای تمام تست‌ها"""

    log_message( LG.API, "\n" + "=" * 70, LogLevel.INFO )
    log_message( LG.API, "🚀 شروع تست API Endpoints", LogLevel.INFO )
    log_message( LG.API, f"📍 Base URL: {BASE_URL}", LogLevel.INFO )
    log_message( LG.API, f"⏱️  Timeout: {TIMEOUT}s", LogLevel.INFO )
    log_message( LG.API, "=" * 70, LogLevel.INFO )

    # بررسی در دسترس بودن سرور
    log_message( LG.API, "🔍 بررسی اتصال به سرور...", LogLevel.INFO )
    try:
        response = requests.get( BASE_URL, timeout=5 )
        log_message( LG.API, "✅ سرور در دسترس است", LogLevel.INFO )
    except requests.RequestException as e:
        log_message( LG.API, "❌ سرور در دسترس نیست!", LogLevel.ERROR )
        log_message( LG.API, f"   Error: {str(e)}", LogLevel.ERROR )
        log_message( LG.API, "\nلطفاً ابتدا API را اجرا کنید:", LogLevel.ERROR )
        log_message( LG.API, "  uvicorn backend.app.main:app --reload", LogLevel.ERROR )
        sys.exit( 1 )

    # اجرای تست‌ها
    tests = [
        test_root,
        test_health,
        test_stats,
        test_chat_rag,
        test_chat_system,
        test_validation_error,
    ]

    for test in tests:
        test()

    # نمایش خلاصه
    total = PASSED_TESTS + FAILED_TESTS

    log_message( LG.API, "\n" + "=" * 70, LogLevel.INFO )
    log_message( LG.API, "📊 خلاصه نتایج", LogLevel.INFO )
    log_message( LG.API, "=" * 70, LogLevel.INFO )
    log_message( LG.API, f"✅ Passed: {PASSED_TESTS}/{total}", LogLevel.INFO )
    log_message( LG.API, f"❌ Failed: {FAILED_TESTS}/{total}", LogLevel.INFO )
    log_message( LG.API, "=" * 70, LogLevel.INFO )

    if FAILED_TESTS == 0:
        log_message( LG.API, "🎉 تمام تست‌ها با موفقیت گذراندند!", LogLevel.INFO )
        sys.exit( 0 )
    else:
        log_message( LG.API, f"⚠️ {FAILED_TESTS} تست با شکست مواجه شد", LogLevel.ERROR )
        sys.exit( 1 )


if __name__ == "__main__":
    run_all_tests()
