from pathlib import Path
from typing import Optional
from docx import Document as DocxDocument
from backend.app.utils.logging_config import log_message, LG, LogLevel


class TextExtractor:
    """
    استخراج متن از فایل‌های Word (.docx)
    """

    @staticmethod
    def extract_from_docx( file_path: str ) -> str:
        """
        استخراج متن از فایل .docx
        
        Args:
            file_path: مسیر فایل
            
        Returns:
            (متن کامل, تعداد صفحات تقریبی)
        """
        try:
            doc = DocxDocument( file_path )

            # استخراج تمام پاراگراف‌ها
            paragraphs = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:          # فقط پاراگراف‌های غیرخالی
                    paragraphs.append( text )

            # ترکیب پاراگراف‌ها
            full_text = "\n\n".join( paragraphs )

            # محاسبه تقریبی تعداد صفحات
            # فرض: هر صفحه حدود 500 کلمه
            word_count = len( full_text.split() )
            estimated_pages = max( 1, word_count // 500 )

            log_message(
                LG.DataProcessing,
                f"متن استخراج شد از {Path(file_path).name}: {len(paragraphs)} پاراگراف، ~{estimated_pages} صفحه",
                LogLevel.INFO )

            return full_text

        except Exception as e:
            log_message( LG.DataProcessing, f"خطا در استخراج متن از {file_path}: {str(e)}", LogLevel.ERROR )
            raise

    @staticmethod
    def validate_docx( file_path: str ) -> bool:
        """
        بررسی معتبر بودن فایل .docx
        
        Args:
            file_path: مسیر فایل
            
        Returns:
            True اگر فایل معتبر باشد
        """
        try:
            path = Path( file_path )

            # چک کردن وجود فایل
            if not path.exists():
                log_message( LG.DataProcessing, f"فایل وجود ندارد: {file_path}", LogLevel.ERROR )
                return False

            # چک کردن پسوند
            if path.suffix.lower() != ".docx":
                log_message( LG.DataProcessing, f"فرمت فایل باید .docx باشد: {file_path}", LogLevel.ERROR )
                return False

            # تست باز کردن فایل
            DocxDocument( file_path )
            return True

        except Exception as e:
            log_message( LG.DataProcessing, f"فایل معتبر نیست {file_path}: {str(e)}", LogLevel.ERROR )
            return False


# Instance سراسری
text_extractor = TextExtractor()
