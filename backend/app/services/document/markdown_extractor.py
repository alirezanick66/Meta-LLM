import re
from pathlib import Path
from typing import Dict, Tuple
from backend.app.utils.custom_normalizer import persian_normalizer
from backend.app.utils.logging_config import log_message, LG, LogLevel


class MarkdownExtractor:
    """
   ‫ استخراج و پردازش فایل‌های Markdown
    - ‫حذف syntax های markdown
    - ‫استخراج ساختار headings
    -‫ الحاق لیست‌ها به heading مربوطه
    - نرمال‌سازی متن فارسی
    """

    def __init__( self ):
        self.normalizer = persian_normalizer

    def extract_from_markdown( self, file_path: str ) -> Tuple[ str, Dict ]:
        """
       ‫ استخراج متن و metadata از فایل Markdown
        
        Args:
            file_path: مسیر فایل .md
            
        Returns:
            (متن پردازش شده, metadata)
        """
        try:
            # خواندن فایل
            with open( file_path, 'r', encoding='utf-8' ) as f:
                raw_content = f.read()

            # پردازش محتوا
            processed_content = self._process_markdown( raw_content )

            # ‫استخراج metadata
            metadata = self._extract_metadata( file_path, raw_content )

            # نرمال‌سازی متن نهایی
            normalized_content = self.normalizer.normalize( processed_content )

            log_message( LG.DataProcessing, f"متن نرمال‌سازی شد - طول: {len(normalized_content)} کاراکتر", LogLevel.INFO )

            return normalized_content, metadata

        except Exception as e:
            log_message( LG.DataProcessing, f"خطا در استخراج Markdown از {file_path}: {str(e)}", LogLevel.ERROR )
            raise

    def _process_markdown( self, content: str ) -> str:
        """
       ‫ پردازش و تمیزسازی markdown
        - ‫حذف syntax ها
        - ‫الحاق لیست‌ها به headings
        """
        # ‫1. حذف front matter (اگه وجود داشت)
        content = self._remove_front_matter( content )

        # ‫2. الحاق لیست‌ها به heading مربوطه
        content = self._attach_lists_to_headings( content )

        # ‫3. حذف markdown syntax ها
        content = self._clean_markdown_syntax( content )

        # ‫4. تمیزسازی فاصله‌ها و خطوط خالی
        content = self._clean_whitespace( content )

        return content

    def _remove_front_matter( self, content: str ) -> str:
        """ ‫حذف YAML front matter از ابتدای فایل"""
        # Front matter معمولاً بین --- قرار داره
        pattern = r'^---\s*\n.*?\n---\s*\n'
        content = re.sub( pattern, '', content, flags=re.DOTALL )
        return content

    def _attach_lists_to_headings( self, content: str ) -> str:
        """
       ‫ الحاق لیست‌ها به heading قبلی
        مثال:
        ## مزایای انقلاب
        - استقلال
        - آزادی
        
        تبدیل میشه به:
        ## مزایای انقلاب:
        - استقلال
        - آزادی
        """
        lines = content.split( '\n' )
        processed_lines = []
        i = 0

        while i < len( lines ):
            line = lines[ i ]

            # ‫اگه heading بود
            if re.match( r'^#{1,6}\s+.+', line ):
                heading_index = len( processed_lines )
                processed_lines.append( line )

                #‫ جستجوی اولین خط غیرخالی بعد از heading
                j = i + 1
                found_list = False

                while j < len( lines ):
                    next_line = lines[ j ].strip()

                    # اگه خط خالی بود، ادامه بده
                    if not next_line:
                        j += 1
                        continue

                    # اگه لیست پیدا شد
                    if re.match( r'^[\-\*\+]\s+', next_line ):
                        found_list = True
                        break

                    # ‫اگه heading یا محتوای دیگه‌ای پیدا شد، break
                    break

                # اگه لیست پیدا شد، `:` اضافه کن
                if found_list:
                    if not processed_lines[ heading_index ].rstrip().endswith( ':' ):
                        processed_lines[ heading_index ] = processed_lines[ heading_index ].rstrip() + ':'

            else:
                processed_lines.append( line )

            i += 1

        return '\n'.join( processed_lines )

    def _clean_markdown_syntax( self, content: str ) -> str:
        """ ‫حذف syntax های markdown"""

        # ‫1. حذف bold (**text** یا __text__)
        content = re.sub( r'\*\*(.+?)\*\*', r'\1', content )
        content = re.sub( r'__(.+?)__', r'\1', content )

        # ‫2. حذف italic (*text* یا _text_)
        content = re.sub( r'\*(.+?)\*', r'\1', content )
        content = re.sub( r'_(.+?)_', r'\1', content )

        # ‫3. حذف inline code (`code`)
        content = re.sub( r'`(.+?)`', r'\1', content )

        # ‫4. حذف links [text](url) → text
        content = re.sub( r'\[(.+?)\]\(.+?\)', r'\1', content )

        # ‫5. حذف images ![alt](url)
        content = re.sub( r'!\[.*?\]\(.+?\)', '', content )

        # ‫6. حذف horizontal rules (---, ___, ***)
        content = re.sub( r'^[\-\_\*]{3,}\s*$', '', content, flags=re.MULTILINE )

        # ‫7. حذف block quotes (> text) - فقط علامت > حذف میشه
        content = re.sub( r'^>\s+', '', content, flags=re.MULTILINE )

        # ‫8. حذف code blocks (```code```)
        content = re.sub( r'```[\s\S]*?```', '', content )

        return content

    def _clean_whitespace( self, content: str ) -> str:
        """تمیزسازی فاصله‌ها و خطوط خالی"""

        # حذف فاصله‌های اضافی در انتهای خطوط
        content = re.sub( r'[ \t]+$', '', content, flags=re.MULTILINE )

        # تبدیل چند خط خالی به یک خط خالی
        content = re.sub( r'\n{3,}', '\n\n', content )

        # حذف فاصله‌های اضافه در ابتدا و انتها
        content = content.strip()

        return content

    def _extract_metadata( self, file_path: str, raw_content: str ) -> Dict:
        """ ‫استخراج metadata از فایل"""

        # ‫استخراج اولین heading به عنوان title
        title_match = re.search( r'^#\s+(.+)$', raw_content, re.MULTILINE )
        title = title_match.group( 1 ) if title_match else Path( file_path ).stem

        # ‫شمارش headings
        headings = re.findall( r'^#{1,6}\s+.+$', raw_content, re.MULTILINE )

        # شمارش لیست‌ها
        lists = re.findall( r'^[\-\*\+]\s+.+$', raw_content, re.MULTILINE )

        # ‫شمارش code blocks
        code_blocks = re.findall( r'```[\s\S]*?```', raw_content )

        metadata = {
            "file_name": Path( file_path ).name,
            "file_path": str( file_path ),
            "title": title,
            "heading_count": len( headings ),
            "list_count": len( lists ),
            "code_block_count": len( code_blocks ),
            "has_lists": len( lists ) > 0,
            "has_code": len( code_blocks ) > 0,
        }

        log_message( LG.DataProcessing, f"Metadata استخراج شد: {metadata['file_name']}", LogLevel.DEBUG )

        return metadata


# Instance سراسری
markdown_extractor = MarkdownExtractor()
