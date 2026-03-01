import threading
from typing import Optional
from transformers import AutoTokenizer, PreTrainedTokenizer
from backend.app.core.config import settings
from backend.app.utils.logging_config import log_message, LG, LogLevel


class TokenizerService:
    """‫ سرویس توکن‌سازی با lazy loading و thread safety"""

    def __init__( self ):
        self._tokenizer: Optional[ PreTrainedTokenizer ] = None
        self._lock = threading.Lock()

    def _get_or_load( self ) -> PreTrainedTokenizer:
        """‫ بارگذاری توکن‌ساز فقط در صورت نیاز (Lazy Loading)"""
        if self._tokenizer is None:
            with self._lock:
                if self._tokenizer is not None:
                    return self._tokenizer

                try:
                    log_message( LG.LLM, f"🔄 Loading tokenizer: {settings.EMBEDDING_MODEL}", LogLevel.INFO )
                    tokenizer = AutoTokenizer.from_pretrained(
                        settings.EMBEDDING_MODEL,
                        use_fast=True,
                        trust_remote_code=True,
                        token=getattr( settings, 'EMBEDDING_MODEL_TOKEN', None ),
                    )
                    self._tokenizer = tokenizer
                except Exception as e:
                    raise RuntimeError( f"❌ خطا در بارگذاری توکنایزر {settings.EMBEDDING_MODEL}: {e}" )

        if self._tokenizer is None:
            raise RuntimeError( "❌ توکنایزر بارگذاری نشد" )
        return self._tokenizer

    def count_tokens( self, text: str ) -> int:
        """‫ شمارش تعداد توکن‌های یک متن"""
        if not text:
            return 0
        try:
            tokenizer = self._get_or_load()
            return len( tokenizer.encode( text, add_special_tokens=False ) )
        except Exception as e:
            log_message( LG.DataProcessing, f"⚠️ Fallback counting: {e}", LogLevel.WARNING )
            return max( 1, len( text ) // 3 )
