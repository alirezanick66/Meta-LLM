import json
import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent ) )
from backend.app.utils.logging_config import log_message, LG, LogLevel
from backend.app.services.document.chunker import MarkdownChunker

# ==========================================
# تنظیمات تست
# ==========================================
REAL_FILE_PATH = "backend/data/test/extracted_text.txt"
OUTPUT_JSON_PATH = "backend/data/test/output_chunks.json"


def run_real_test():
    log_message( LG.DataProcessing, "شروع تست Chunker روی فایل استخراج شده...", LogLevel.INFO )

    # 1. ساخت Chunker
    chunker = MarkdownChunker()

    # 2. خواندن فایل متنی استخراج شده
    if not Path( REAL_FILE_PATH ).exists():
        log_message( LG.DataProcessing, f"❌ فایل پیدا نشد: {REAL_FILE_PATH}", LogLevel.ERROR )
        return

    with open( REAL_FILE_PATH, 'r', encoding='utf-8' ) as f:
        normalized_text = f.read()

    log_message( LG.DataProcessing, f"✅ فایل استخراج شده خوانده شد. طول متن: {len(normalized_text)} کاراکتر",
                 LogLevel.INFO )

    # 3. مدیریت متادیتا (روش دستی برای تست)
    # چون فایل خام .md را نداریم، نمی‌توانیم از متد extract_metadata استفاده کنیم
    # (چون آن متد به علامت‌های خام مثل # نیاز دارد).
    # برای تست chunker، متادیتای ساده کافی است:
    doc_metadata = {
        "file_name": Path( REAL_FILE_PATH ).name,
        "title": "تست دستی - انقلاب اسلامی",          # عنوان فرضی
    }
    log_message( LG.DataProcessing, "⚠️  نکته: از متادیتای دستی استفاده شد (چون فایل خام اصلی در دسترس نیست).",
                 LogLevel.WARNING )

    # 5. ارسال متن به Chunker
    log_message( LG.DataProcessing, "🧩 در حال پردازش و Chunk کردن...", LogLevel.INFO )
    try:
        chunks = chunker.create_chunks(
            markdown_text=normalized_text,          # متن فایل txt
            doc_id=999,          # شناسه فرضی برای تست
            source_file=doc_metadata.get( "file_name", "test_file.txt" ) )

        with open( OUTPUT_JSON_PATH, 'w', encoding='utf-8' ) as f:
            json.dump( chunks, f, ensure_ascii=False, indent=4 )

        log_message( LG.DataProcessing, f"✅ چانک‌ها در فایل JSON ذخیره شدند: {OUTPUT_JSON_PATH}", LogLevel.INFO )
    except Exception as e:
        log_message( LG.DataProcessing, f"❌ خطا در مرحله Chunker: {e}", LogLevel.ERROR )
        return

    # 6. نمایش نتایج
    log_message( LG.DataProcessing, f"🎉 موفقیت‌آمیز! تعداد کل چانک‌های تولید شده: {len(chunks)}", LogLevel.INFO )
    log_message( LG.DataProcessing, "-" * 60, LogLevel.INFO )

    # نمایش جزئیات ۲ چانک اول
    for i, chunk in enumerate( chunks[ :2 ] ):
        log_message( LG.DataProcessing, f"\n🔹 Chunk #{i + 1}", LogLevel.INFO )
        log_message( LG.DataProcessing, f"   ID          : {chunk['chunk_id']}", LogLevel.INFO )
        log_message( LG.DataProcessing, f"   Tokens      : {chunk['token_count']}", LogLevel.INFO )
        log_message( LG.DataProcessing, f"   Words       : {chunk['word_count']}", LogLevel.INFO )

        # بررسی اینکه آیا hierarchy پر شده است یا خیر
        hierarchy = chunk[ 'metadata' ][ 'hierarchy' ]
        section = chunk[ 'metadata' ][ 'section' ]

        log_message( LG.DataProcessing, f"   Hierarchy   : {hierarchy if hierarchy else '(خالی - هدر یافت نشد)'}",
                     LogLevel.INFO )
        log_message( LG.DataProcessing, f"   Section     : {section if section else '(خالی)'}", LogLevel.INFO )
        log_message( LG.DataProcessing, f"   Has List?   : {chunk['metadata']['has_list']}", LogLevel.INFO )
        log_message( LG.DataProcessing, "-" * 60, LogLevel.INFO )


if __name__ == "__main__":
    run_real_test()
