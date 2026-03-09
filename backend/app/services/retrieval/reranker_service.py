import torch
from typing import List, Dict, Any
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from backend.app.core.config import settings
from backend.app.utils.logging_config import log_message, LG, LogLevel


class RerankerService:
    """
    ‫سرویس Reranking با مدل BAAI/bge-reranker-v2-m3
    
    ‫فرآیند:
    1. ‫دریافت query و لیست chunks از RRF
    2. ‫ساخت جفت (query, chunk) برای هر chunk
    3. ‫محاسبه relevance score با Cross-Encoder
    4. ‫مرتب‌سازی مجدد و برگشت top_k
    """

    def __init__( self ):
        self.model_path = settings.RERANKER_MODEL_PATH or settings.RERANKER_MODEL
        self.device = settings.EMBEDDING_DEVICE
        self.model = None
        self.tokenizer = None
        self._load_model()

    def _load_model( self ) -> None:
        """‫بارگذاری مدل و tokenizer از مسیر local"""
        try:
            log_message( LG.Retrieval, f"⏳ بارگذاری Reranker: {self.model_path}...", LogLevel.INFO )

            # ‫نیازی به set_num_threads نیست — EmbeddingService قبلاً انجام داده
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True,
            )
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_path,
                trust_remote_code=True,
            )
            self.model.eval()

            if self.device == "cuda" and torch.cuda.is_available():
                self.model = self.model.cuda()

            log_message( LG.Retrieval, f"✅ Reranker بارگذاری شد - Device: {self.device}", LogLevel.INFO )

        except Exception as e:
            log_message( LG.Retrieval, f"❌ خطا در بارگذاری Reranker: {str(e)}", LogLevel.ERROR )
            raise

    def rerank(
        self,
        query: str,
        chunks: List[ Dict[ str, Any ] ],
        top_k: int,
    ) -> List[ Dict[ str, Any ] ]:
        """
        ‫rerank کردن chunks بر اساس relevance به query
        
        Args:
            query: سوال کاربر
            chunks: ‫لیست chunks از RRF (هر chunk باید 'content' داشته باشه)
            top_k: ‫تعداد نتایج نهایی
            
        Returns:
            ‫لیست chunks مرتب‌شده با فیلد 'reranker_score' اضافه‌شده
        """
        if not chunks:
            return []

        if self.model is None or self.tokenizer is None:
            log_message( LG.Retrieval, "❌ Reranker آماده نیست", LogLevel.ERROR )
            return chunks[ :top_k ]

        try:
            # ‫ساخت جفت‌های (query, content) برای هر chunk
            pairs = [ [ query, chunk.get( "content", "" ) ] for chunk in chunks ]

            # ‫tokenize همه جفت‌ها یکجا
            inputs = self.tokenizer(
                pairs,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )

            if self.device == "cuda" and torch.cuda.is_available():
                inputs = { k: v.cuda() for k, v in inputs.items() }

            # ‫محاسبه scores بدون gradient (inference mode)
            with torch.no_grad():
                scores = self.model( **inputs ).logits.squeeze( -1 )
                scores = torch.sigmoid( scores ).cpu().tolist()

            # ‫اگه فقط یک chunk بود، scores یه عدد میشه نه لیست
            if isinstance( scores, float ):
                scores = [ scores ]

            # ‫اضافه کردن reranker_score به هر chunk و مرتب‌سازی
            for chunk, score in zip( chunks, scores ):
                chunk[ "reranker_score" ] = float( score )

            reranked = sorted( chunks, key=lambda x: x[ "reranker_score" ], reverse=True )

            log_message( LG.Retrieval, f"✅ Reranking تکمیل شد: {len(chunks)} → {min(top_k, len(reranked))} chunk", LogLevel.INFO )

            return reranked[ :top_k ]

        except Exception as e:
            log_message( LG.Retrieval, f"❌ خطا در reranking: {str(e)}", LogLevel.ERROR )
            # ‫fallback: همون ترتیب RRF رو برگردون
            return chunks[ :top_k ]
