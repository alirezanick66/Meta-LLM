import threading
from typing import Optional, Dict
from transformers import AutoTokenizer, PreTrainedTokenizer
from backend.app.core.config import settings
from backend.app.utils.logging_config import log_message, LG, LogLevel


class TokenizerService:
    _instance: Optional[ "TokenizerService" ] = None
    _lock = threading.Lock()
    _tokenizers: Dict[ str, PreTrainedTokenizer ]

    def __new__( cls ):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__( cls )
                    cls._instance._tokenizers = {}
        return cls._instance

    def _get_or_load( self, name: str ) -> PreTrainedTokenizer:
        """بارگذاری توکن‌ساز فقط در صورت نیاز (Lazy Loading)"""
        if name not in self._tokenizers:
            with self._lock:
                # Double-check inside lock
                if name in self._tokenizers:
                    return self._tokenizers[ name ]

                model_path = settings.EMBEDDING_MODEL if name == "chunking" else "HooshvareLab/bert-fa-base-uncased"
                try:
                    log_message( LG.LLM, f"🔄 Loading tokenizer: {name} ({model_path})", LogLevel.INFO )
                    tokenizer = AutoTokenizer.from_pretrained(
                        model_path,
                        use_fast=True,          # سرعت بالاتر در توکن‌سازی
                        token=getattr( settings, 'EMBEDDING_MODEL_TOKEN', None ) if name == "chunking" else None )
                    self._tokenizers[ name ] = tokenizer
                except Exception as e:
                    if name == "persian":          # Fallback logic
                        log_message( LG.LLM, f"⚠️ Persian tokenizer failed, using chunking fallback.", LogLevel.WARNING )
                        return self._get_or_load( "chunking" )
                    raise RuntimeError( f"Critical error loading tokenizer {name}: {e}" )

        return self._tokenizers[ name ]

    def count_tokens( self, text: str, tokenizer_name: str = "chunking" ) -> int:
        if not text: return 0
        try:
            tokenizer = self._get_or_load( tokenizer_name )
            # استفاده از فیلد input_ids بدون ساخت Tensor برای سرعت بیشتر
            return len( tokenizer.encode( text, add_special_tokens=False, verbose=False ) )
        except Exception as e:
            log_message( LG.DataProcessing, f"⚠️ Fallback counting: {e}", LogLevel.WARNING )
            return int( len( text.split() ) * 2.5 )

    def encode( self, text: str, tokenizer_name: str = "chunking" ) -> list[ int ]:
        return self._get_or_load( tokenizer_name ).encode( text, add_special_tokens=False )

    def count_words( self, text: str ) -> int:
        """شمارش کلمات (سریع)"""
        if not text:
            return 0
        return len( text.split() )


# تکیه بر مکانیزم Singleton خودِ ماژول در پایتون
tokenizer_service = TokenizerService()
