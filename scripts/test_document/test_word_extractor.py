import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent.parent ) )
from backend.app.services.document.word_extractor import word_extractor

word_path = "backend/data/documents/enghelab.docx"
output_path = "backend/data/test/test_word_extractor.txt"
extract = word_extractor.extract_from_word( word_path )
extracted_text, metadata = extract

# ذخیره متن استخراج‌شده در فایل txt
with open( output_path, "w", encoding="utf-8" ) as f:
    f.write( extracted_text )

print( f"متن با موفقیت در {output_path} ذخیره شد" )
