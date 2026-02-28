from pathlib import Path
from typing import Dict, List, Tuple

from backend.app.services.document.markdown_extractor import markdown_extractor
from backend.app.services.document.word_extractor import word_extractor
from backend.app.utils.logging_config import LG, LogLevel, log_message

# فرمت‌های پشتیبانی‌شده
SUPPORTED_EXTENSIONS = {
    '.md': 'markdown',
    '.markdown': 'markdown',
    '.docx': 'word',
}


class DocumentProcessor:
    """
    پردازش یکپارچه انواع فرمت‌های سند
    """

    def __init__( self ):
        self._extract_methods = {
            'markdown': lambda path: markdown_extractor.extract_from_markdown( path ),
            'word': lambda path: word_extractor.extract_from_word( path ),
        }
        log_message( LG.DataProcessing, "DocumentProcessor آماده شد", LogLevel.INFO )

    def extract( self, file_path: str ) -> Tuple[ str, Dict ]:
        """
        استخراج متن با فرمت پشتیبانی‌شده

        Args:
            file_path: مسیر فایل

        Returns:
            (متن نرمال‌شده, metadata)

        Raises:
            ValueError: اگه فرمت پشتیبانی نشه
            FileNotFoundError: اگه فایل وجود نداشته باشه
        """
        path = Path( file_path )

        if not path.exists():
            raise FileNotFoundError( f"فایل پیدا نشد: {file_path}" )

        file_type = self.get_file_type( file_path )

        if not file_type:
            raise ValueError( f"فرمت '{path.suffix}' پشتیبانی نمی‌شود. "
                              f"فرمت‌های مجاز: {list(SUPPORTED_EXTENSIONS.keys())}" )

        log_message( LG.DataProcessing, f"پردازش فایل {path.name} (نوع: {file_type})", LogLevel.INFO )

        return self._extract_methods[ file_type ]( file_path )

    def get_file_type( self, file_path: str ) -> str | None:
        """تشخیص نوع فایل بر اساس پسوند"""
        suffix = Path( file_path ).suffix.lower()
        return SUPPORTED_EXTENSIONS.get( suffix )

    def is_supported( self, file_path: str ) -> bool:
        """بررسی پشتیبانی از فرمت فایل"""
        return self.get_file_type( file_path ) is not None

    def scan_folder( self, folder_path: str ) -> List[ Dict ]:
        """
        اسکن کامل یک پوشه و برگرداندن لیست فایل‌های قابل پردازش

        Args:
            folder_path: مسیر پوشه

        Returns:
            لیست دیکشنری‌ها با اطلاعات هر فایل:
            [{'path': str, 'name': str, 'type': str, 'size_kb': float}, ...]
        """
        folder = Path( folder_path )

        if not folder.exists():
            log_message( LG.DataProcessing, f"پوشه وجود ندارد: {folder_path}", LogLevel.ERROR )
            return []

        if not folder.is_dir():
            log_message( LG.DataProcessing, f"مسیر داده‌شده پوشه نیست: {folder_path}", LogLevel.ERROR )
            return []

        files = []
        for file_path in folder.iterdir():
            # Skip غیر فایل‌ها
            if not file_path.is_file():
                continue

            suffix = file_path.suffix.lower()
            file_type = SUPPORTED_EXTENSIONS.get( suffix )

            if not file_type:
                continue          # فرمت پشتیبانی‌نشده را نادیده بگیر

            files.append( {
                'path': str( file_path ),
                'name': file_path.name,
                'type': file_type,
                'size_kb': round( file_path.stat().st_size / 1024, 2 ),
            } )

        log_message( LG.DataProcessing, f"✅ {len(files)} فایل قابل پردازش در پوشه یافت شد: {folder_path}", LogLevel.INFO )
        return files


# Instance سراسری
document_processor = DocumentProcessor()
