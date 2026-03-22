import sys
from pathlib import Path

sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent.parent ) )

from backend.app.services.document.chunker import MarkdownChunker
from backend.app.services.embedding.tokenizer_service import TokenizerService
from backend.app.utils.custom_normalizer import persian_normalizer
from backend.app.utils.logging_config import log_message, LG, LogLevel
# ‫یه متن ساده با header
test_md = """### فصل اول: اصول و تعاریف کلی

**ماده ۱:** کلیه کارگران، کارفرمایان، کارگاه‌ها ملزم به تبعیت از این قانون می‌باشند.

**ماده ۲:** کارگر از نظر این قانون کسی است که در مقابل دریافت حق السعی کار می‌کند.
"""

normalized = persian_normalizer.normalize( test_md )
log_message( LG.DataProcessing, "متن normalize شده:", LogLevel.INFO )
print( repr( normalized[ :200 ] ) )
log_message( LG.DataProcessing, repr( normalized[ :200 ] ), LogLevel.INFO )
print( "---" )

tokenizer = TokenizerService()
chunker = MarkdownChunker( tokenizer_service=tokenizer )
chunks = chunker.create_chunks( normalized, doc_id=1, source_file="test.md" )
log_message( LG.DataProcessing, f"تعداد chunks: {len(chunks)}", LogLevel.INFO )
for c in chunks:
    log_message( LG.DataProcessing, f"chunk_id: {c['chunk_id']}, tokens: {c['token_count']}", LogLevel.INFO )
    log_message( LG.DataProcessing, f"content: {c['content'][:100]}", LogLevel.INFO )
    log_message( LG.DataProcessing, "---", LogLevel.INFO )
