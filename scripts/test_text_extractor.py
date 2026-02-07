import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent ) )

from backend.app.services.text_extractor import TextExtractor
from backend.app.utils.logging_config import log_message, LG, LogLevel
from backend.app.utils.custom_normalizer import persian_normalizer

file_path: str = "backend/data/documents/calture_citis.docx"

extracted_text, metadata = TextExtractor().extract_from_docx( file_path )

# نوشتن متن استخراج شده در فایل
with open( "backend/data/test/extracted_text.txt", "w", encoding="utf-8" ) as f:
    f.write( extracted_text )

# # تست 1: فاصله دوتایی
# text1 = "ساعت 10:30 است"
# result1 = persian_normalizer.normalize( text1 )
# log_message( LG.DataProcessing, f"نتیجه نرمال‌سازی: '{result1}'", LogLevel.INFO )
