import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent.parent ) )

from backend.app.utils.custom_normalizer import PersianNormalizer
from backend.app.utils.logging_config import log_message, LG, LogLevel

normalizer_value = PersianNormalizer()

words = "كتاب‌هاي جديد من ، بسیار زیباااااا هستند . مي توانيد آنها را در ويکي‌پدیا مشاهده كنيد . مي خواهم برویم به خانه‌ي مادربزرگ (که در خيابان پیروزی است) ولی می‌ترسم دیر بشه ! آيا بنظر شما 30% تخفیف كافيست؟؟؟"
log_message( LG.DataProcessing, normalizer_value.normalize( words ), LogLevel.INFO )
