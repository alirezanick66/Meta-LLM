import re
from hazm import Normalizer as HazmNormalizer
from backend.app.utils.logging_config import log_message, LG, LogLevel


class PersianNormalizer:
    """
    نرمال‌سازی پیشرفته متن فارسی
    شامل fix کردن باگ‌های Hazm و بهینه‌سازی با str.translate
    """

    # جدول نگاشت یکپارچه برای سرعت بیشتر (str.translate)
    # شامل حروف عربی، اعداد فارسی و عربی
    _CHAR_MAP = {
          # حروف عربی به فارسی
        'ي': 'ی',
        'ك': 'ک',
        'ى': 'ی',
        'ہ': 'ه',
        'ۀ': 'ه',
        'ة': 'ه',
          # اعداد فارسی به انگلیسی
        '۰': '0',
        '۱': '1',
        '۲': '2',
        '۳': '3',
        '۴': '4',
        '۵': '5',
        '۶': '6',
        '۷': '7',
        '۸': '8',
        '۹': '9',
          # اعداد عربی به انگلیسی
        '٠': '0',
        '١': '1',
        '٢': '2',
        '٣': '3',
        '٤': '4',
        '٥': '5',
        '٦': '6',
        '٧': '7',
        '٨': '8',
        '٩': '9',
          # علائم نگارشی (اختیاری: تبدیل کوتیشن انگلیسی به فارسی)
        '"': '«',
          # نکته: برای بسته شدن کوتیشن نیاز به لاجیک پیچیده‌تر است،
          # اما اینجا ساده‌سازی می‌کنیم. یا می‌توانید این خط را حذف کنید.
    }

    # ساخت جدول ترجمه برای استفاده در متد translate
    _TRANS_TABLE = str.maketrans( _CHAR_MAP )

    def __init__( self, use_hazm: bool = True ):
        """
        Args:
            use_hazm: استفاده از Hazm به عنوان لایه اول
        """
        self.use_hazm = use_hazm
        self.hazm_normalizer = HazmNormalizer() if use_hazm else None
        log_message( LG.DataProcessing, f"Custom Persian Normalizer آماده شد (Hazm: {use_hazm})", LogLevel.INFO )

    def _fix_chars_and_numbers( self, text: str ) -> str:
        """تبدیل یکپارچه حروف و اعداد با استفاده از translate (بسیار سریع)"""
        return text.translate( self._TRANS_TABLE )

    def _fix_zwnj( self, text: str ) -> str:
        """
        اصلاح نیم‌فاصله (ZWNJ)
        حذف نیم‌فاصله‌های اضافی
        """
        # حذف چند نیم‌فاصله پشت سر هم
        text = re.sub( r'‌+', '‌', text )
        # حذف فاصله قبل و بعد از نیم‌فاصله (اگر اشتباهی تایپ شده باشد)
        text = text.replace( ' ‌', '‌' )
        text = text.replace( '‌ ', '‌' )
        return text

    def _remove_extra_spaces( self, text: str ) -> str:
        """حذف فاصله‌های اضافی"""
        # چند فاصله → یک فاصله
        text = re.sub( r' +', ' ', text )
        text = text.strip()

        # لیست علائم نگارشی که نباید قبل از آن‌ها فاصله باشد
        # یادتان ن باشد که « و » را هم اضافه کنیم (اگر Hazم انجام نداده باشد)
        punctuations = r'([.,;:!?،؛ـ\)\]}"\'»«])'

        # حذف فاصله قبل از علائم نگارشی
        text = re.sub( rf'\s+{punctuations}', r'\1', text )

        # حذف فاصله بعد از علائم باز (پرانتز باز، کوتیشن باز)
        text = re.sub( r'([(\["\'«])\s+', r'\1', text )

        return text

    def _remove_diacritics( self, text: str ) -> str:
        """حذف اعراب"""
        # استفاده از کلاس کاراکتری برای سرعت بیشتر
        return re.sub( r'[ًٌٍَُِّْ]', '', text )

    def _remove_kashida( self, text: str ) -> str:
        """حذف کشیده"""
        return text.replace( 'ـ', '' )

    def _fix_number_punctuation( self, text: str ) -> str:
        """اصلاح علائم در اعداد و مخفف‌ها"""
        # مخفف‌ها: U . S . A -> U.S.A
        text = re.sub( r'(\w)\s*\.\s*(\w)', r'\1.\2', text )

        # اعشار: 0 ٫ 5 -> 0.5
        text = re.sub( r'(\d)\s*٫\s*(\d)', r'\1.\2', text )

        # جدا کننده هزارگان: 10، 000 -> 10,000 (اگر هدف تبدیل به فرمت انگلیسی است)
        text = re.sub( r'(\d)\s*،\s*(\d)', r'\1,\2', text )

        # درصد: 60 ٪ -> 60%
        text = re.sub( r'(\d)\s+٪', r'\1%', text )
        text = re.sub( r'(\d)\s+%', r'\1%', text )

        return text

    def _fix_punctuation_spaces( self, text: str ) -> str:
        """اضافه کردن فاصله بعد از علائم نگارشی"""
        # نقطه، ویرگول، علامت سوال، تعجب
        text = re.sub( r'([.،؛:!?])([^\s\d])', r'\1 \2', text )
        return text

    def normalize( self, text: str, remove_diacritics: bool = True, remove_kashida: bool = True ) -> str:
        """
        نرمال‌سازی کامل متن فارسی
        """
        try:
            if not text or not isinstance( text, str ):
                return ""

            # 1. Hazm (اگر فعال باشه) - معمولاً Hazm ابتدا کاراکترها را مرتب می‌کند
            if self.use_hazm and self.hazm_normalizer:
                text = self.hazm_normalizer.normalize( text )

            # 2. تبدیل حروف عربی و اعداد (جایگزین حلقه‌های کند)
            text = self._fix_chars_and_numbers( text )

            # 3. اصلاح نیم‌فاصله
            text = self._fix_zwnj( text )

            # 4. حذف اعراب
            if remove_diacritics:
                text = self._remove_diacritics( text )

            # 5. حذف کشیده
            if remove_kashida:
                text = self._remove_kashida( text )

            # 6. اصلاح علائم در اعداد
            text = self._fix_number_punctuation( text )

            # 7. اضافه کردن فاصله بعد از علائم نگارشی
            text = self._fix_punctuation_spaces( text )

            # 8. حذف فاصله‌های اضافی و اصلاح علائم نگارشی
            text = self._remove_extra_spaces( text )

            return text

        except Exception as e:
            log_message( LG.DataProcessing, f"خطا در نرمال‌سازی متن: {str(e)}", LogLevel.WARNING )
            # بازگشت حداقلی متن تمیز شده در صورت خطا
            return " ".join( text.split() )

    def normalize_query( self, query: str ) -> str:
        """نرمال‌سازی مخصوص جستجو (احتمالاً سخت‌گیرانه‌تر)"""
        return self.normalize( query, remove_diacritics=True, remove_kashida=True )


# Instance سراسری
persian_normalizer = PersianNormalizer( use_hazm=True )
