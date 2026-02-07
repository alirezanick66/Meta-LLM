import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent ) )

from backend.app.services.text_extractor import TextExtractor
from backend.app.utils.logging_config import log_message, LG, LogLevel

is_valid: str = "backend/data/documents/calture_citis.docx"
extract = TextExtractor().extract_from_docx( is_valid )
log_message( LG.DataProcessing, extract, LogLevel.INFO )
