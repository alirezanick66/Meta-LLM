import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent ) )

from backend.app.services.document.markdown_extractor import MarkdownExtractor
from backend.app.utils.logging_config import log_message, LG, LogLevel
from backend.app.utils.custom_normalizer import persian_normalizer

file_path: str = "backend/data/documents/enghelab.md"

extracted_text, metadata = MarkdownExtractor().extract_from_markdown( file_path )

# نوشتن متن استخراج شده در فایل
with open( "backend/data/test/extracted_text.txt", "w", encoding="utf-8" ) as f:
    f.write( extracted_text )
