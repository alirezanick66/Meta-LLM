import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent.parent ) )

from backend.app.services.document.markdown_extractor import MarkdownExtractor
import sys
from pathlib import Path

sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent.parent ) )

from backend.app.utils.custom_normalizer import persian_normalizer

# ‫تست normalize روی یه header نمونه
test = "### فصل اول: اصول و تعاریف کلی"
result = persian_normalizer.normalize( test )
print( f"قبل: {test}" )
print( f"بعد: {result}" )
print( f"آیا # حفظ شد: {'#' in result}" )
