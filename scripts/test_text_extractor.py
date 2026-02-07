import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent ) )

from backend.app.services.text_extractor import TextExtractor
from backend.app.utils.logging_config import log_message, LG, LogLevel

is_valid: str = "backend/data/documents/calture_citis.docx"

# متد extract_from_docx یک tuple برمی‌گرداند: (text, metadata)
extracted_text, metadata = TextExtractor().extract_from_docx( is_valid )

# نوشتن متن استخراج شده در فایل
with open( "extracted_text.txt", "w", encoding="utf-8" ) as f:
    f.write( extracted_text )

# نمایش اطلاعات
print( f"\n{'='*60}" )
print( f"📄 فایل: {metadata.filename}" )
print( f"📏 حجم: {metadata.file_size:,} بایت" )
print( f"📝 تعداد پاراگراف: {metadata.total_paragraphs}" )
print( f"📊 تعداد جدول: {metadata.total_tables}" )
print( f"📑 تعداد عنوان: {metadata.total_headings}" )
print( f"✅ متن استخراج شده: {len(extracted_text):,} کاراکتر" )
print( f"{'='*60}\n" )
