from typing import List, Dict, Any
from backend.app.utils.logging_config import log_message, LG, LogLevel


class PromptBuilder:
    """
    ساخت prompt برای LLM با context از retrieved chunks
    
    ویژگی‌ها:
    - System prompt فارسی
    - فرمت‌بندی chunks
    - محدودیت طول
    """

    def __init__( self, max_context_length: int = 4000 ):
        """
        Args:
            max_context_length: حداکثر طول context (کاراکتر)
        """
        self.max_context_length = max_context_length

        # System prompt
        self.system_prompt = """تو یک دستیار هوشمند متخصص در زمینه انقلاب اسلامی ایران و مباحث مرتبط با آن هستی.

وظیفه تو:
1. پاسخ دقیق و جامع به سوالات کاربر بر اساس اطلاعات ارائه شده
2. استفاده از زبان فارسی رسمی و روان
3. ذکر منابع در صورت امکان
4. اگر جواب در context نیست، صادقانه بگو

قوانین:
- همیشه فارسی پاسخ بده
- از اطلاعات context استفاده کن
- اگر مطمئن نیستی، بگو
- پاسخ کوتاه و مفید باشد (حداکثر 3-4 پاراگراف)
"""

        log_message( LG.LLM, "PromptBuilder آماده شد", LogLevel.INFO )

    def build_prompt(
        self,
        query: str,
        chunks: List[ Dict[ str, Any ] ],
        include_metadata: bool = True,
    ) -> str:
        """
        ساخت prompt کامل
        
        Args:
            query: سوال کاربر
            chunks: لیست retrieved chunks
            include_metadata: شامل metadata (hierarchy) باشه؟
            
        Returns:
            prompt کامل
        """
        try:
            log_message(
                LG.LLM,
                f"📝 ساخت prompt با {len(chunks)} chunk...",
                LogLevel.INFO,
            )

            # ساخت context از chunks
            context_parts = []
            total_length = 0

            for i, chunk in enumerate( chunks, start=1 ):
                # استخراج محتوا
                content = chunk.get( "content", "" )

                # اگه خیلی طولانی شد، قطع کن
                if total_length + len( content ) > self.max_context_length:
                    log_message(
                        LG.LLM,
                        f"⚠️ Context محدود شد به {i-1} chunk (از {len(chunks)})",
                        LogLevel.WARNING,
                    )
                    break

                # فرمت کردن chunk
                chunk_text = f"[مستند {i}]\n{content}\n"

                # اضافه کردن metadata (اختیاری)
                if include_metadata:
                    metadata = chunk.get( "metadata", {} )
                    hierarchy = metadata.get( "hierarchy" )
                    if hierarchy:
                        chunk_text = f"[مستند {i} - {hierarchy}]\n{content}\n"

                context_parts.append( chunk_text )
                total_length += len( content )

            # ترکیب context
            context = "\n".join( context_parts )

            # ساخت prompt نهایی
            prompt = f"""{self.system_prompt}

---

اطلاعات موجود:

{context}

---

سوال کاربر: {query}

پاسخ:"""

            log_message(
                LG.LLM,
                f"✅ Prompt ساخته شد - طول: {len(prompt)} کاراکتر",
                LogLevel.INFO,
            )

            return prompt

        except Exception as e:
            log_message( LG.LLM, f"❌ خطا در ساخت prompt: {str(e)}", LogLevel.ERROR )
            raise

    def build_simple_prompt( self, query: str ) -> str:
        """
        prompt ساده بدون context (برای تست)
        
        Args:
            query: سوال کاربر
            
        Returns:
            prompt ساده
        """
        return f"""{self.system_prompt}

سوال کاربر: {query}

پاسخ:"""
