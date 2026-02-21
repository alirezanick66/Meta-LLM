import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent ) )
from backend.app.services.document.word_extractor import word_extractor

extract = word_extractor.extract_from_word( "backend/data/documents/enghelab.docx" )
extracted_text, metadata = extract
print( "متن استخراج‌شده:\n", extracted_text[ :500 ], "..." )          # نمایش ۵۰۰ کاراکتر اول
print( "\nMetadata:\n", metadata )
