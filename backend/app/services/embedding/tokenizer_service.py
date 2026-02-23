import threading
from typing import Dict
from transformers import AutoTokenizer, PreTrainedTokenizer
from backend.app.core.config import settings
from backend.app.utils.logging_config import log_message, LG, LogLevel


class TokenizerService:
    """‫ سرویس توکن‌سازی با lazy loading و thread safety"""

    def __init__( self ):
        self._tokenizers: Dict[ str, PreTrainedTokenizer ] = {}
        self._lock = threading.Lock()

    def _get_or_load( self, name: str ) -> PreTrainedTokenizer:
        """‫ بارگذاری توکن‌ساز فقط در صورت نیاز (Lazy Loading)"""
        if name not in self._tokenizers:
            with self._lock:
                if name in self._tokenizers:
                    return self._tokenizers[ name ]

                model_path = settings.EMBEDDING_MODEL if name == "chunking" else "HooshvareLab/bert-fa-base-uncased"
                try:
                    log_message( LG.LLM, f"🔄 Loading tokenizer: {name} ({model_path})", LogLevel.INFO )
                    tokenizer = AutoTokenizer.from_pretrained(
                        model_path,
                        use_fast=True,
                        token=getattr( settings, 'EMBEDDING_MODEL_TOKEN', None ) if name == "chunking" else None,
                    )
                    self._tokenizers[ name ] = tokenizer
                except Exception as e:
                    if name == "persian":
                        log_message( LG.LLM, "⚠️ Persian tokenizer failed, using chunking fallback.", LogLevel.WARNING )
                        return self._get_or_load( "chunking" )
                    raise RuntimeError( f"Critical error loading tokenizer {name}: {e}" )

        return self._tokenizers[ name ]

    def count_tokens( self, text: str, tokenizer_name: str = "chunking" ) -> int:
        """‫ شمارش تعداد توکن‌های یک متن"""
        if not text:
            return 0
        try:
            tokenizer = self._get_or_load( tokenizer_name )
            return len( tokenizer.encode( text, add_special_tokens=False, verbose=False ) )
        except Exception as e:
            log_message( LG.DataProcessing, f"⚠️ Fallback counting: {e}", LogLevel.WARNING )
            return int( len( text.split() ) * 2.5 )

    def encode( self, text: str, tokenizer_name: str = "chunking" ) -> list[ int ]:
        """‫ تبدیل متن به لیست توکن‌ها"""
        return self._get_or_load( tokenizer_name ).encode( text, add_special_tokens=False )

    def count_words( self, text: str ) -> int:
        """‫ شمارش کلمات (سریع)"""
        if not text:
            return 0
        return len( text.split() )
