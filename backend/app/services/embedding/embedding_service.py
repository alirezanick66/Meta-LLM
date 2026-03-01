import torch
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from backend.app.core.config import settings
from backend.app.utils.logging_config import log_message, LG, LogLevel


class EmbeddingService:
    """
  ‫سرویس Embedding با ‫gte-multilingual
    -‫ پشتیبانی از batch processing
    - ‫بهینه‌سازی برای CPU
    """

    def __init__( self ):
        """
        مقداردهی اولیه مدل
        """
        self.model_name = settings.EMBEDDING_MODEL
        self.device = settings.EMBEDDING_DEVICE
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
        self.model = None
        self.vector_dim: int = settings.EMBEDDING_VECTOR_DIM
        self._load_model()

    def _load_model( self ):
        """‫بارگذاری مدل embedding"""
        try:
            log_message( LG.DataProcessing, f"در حال بارگذاری مدل {self.model_name}...", LogLevel.INFO )

            #‫ بهینه‌سازی برای CPU
            if self.device == "cpu":
                torch.set_num_threads( settings.EMBEDDING_CPU_THREADS )
                log_message( LG.DataProcessing, "تنظیمات CPU optimization اعمال شد", LogLevel.DEBUG )

            self.model = SentenceTransformer(
                settings.EMBEDDING_MODEL_PATH,
                device=self.device,
                token=settings.EMBEDDING_MODEL_TOKEN,
                trust_remote_code=True,
            )

            # تست مدل
            actual_dim = self.model.get_sentence_embedding_dimension() or settings.EMBEDDING_VECTOR_DIM

            if actual_dim != self.vector_dim:
                log_message( LG.DataProcessing, f"⚠️ تغییر dimension: انتظار {self.vector_dim}، دریافت {actual_dim}",
                             LogLevel.WARNING )
                self.vector_dim = actual_dim

            log_message( LG.DataProcessing, f"✅ مدل بارگذاری شد - Device: {self.device}, Dimension: {self.vector_dim}", LogLevel.INFO )

        except Exception as e:
            log_message( LG.DataProcessing, f"❌ خطا در بارگذاری مدل: {str(e)}", LogLevel.ERROR )
            raise

    def embed_single( self, text: str, normalize: bool = True ) -> np.ndarray:
        """
        ساخت embedding برای یک متن
        
        Args:
            text: متن ورودی
            normalize: نرمال‌سازی vector (برای cosine similarity)
            
        Returns:
            numpy array با dimension 768
        """
        try:
            if not text or not text.strip():
                log_message( LG.DataProcessing, "متن خالی برای embedding", LogLevel.WARNING )
                return np.zeros( self.vector_dim )

            if self.model is None:
                raise RuntimeError( "مدل بارگذاری نشده است" )

            embedding = self.model.encode( text, normalize_embeddings=normalize, convert_to_numpy=True )

            return embedding

        except Exception as e:
            log_message( LG.DataProcessing, f"خطا در ساخت embedding: {str(e)}", LogLevel.ERROR )
            raise

    def embed_batch( self, texts: List[ str ], normalize: bool = True, show_progress: bool = False ) -> np.ndarray:
        """
       ‫ ساخت embedding برای چندین متن (batch)
        
        Args:
            texts: لیست متن‌ها
            normalize: نرمال‌سازی vectors
            show_progress: نمایش progress bar
            
        Returns:
            numpy array با shape (len(texts), vector_dim)
        """
        if not texts:
            log_message( LG.DataProcessing, "لیست متن‌ها خالی است", LogLevel.WARNING )
            return np.zeros( ( 0, self.vector_dim ) )

        try:
            # شناسایی متن‌های معتبر
            valid_indices = [ i for i, t in enumerate( texts ) if t and t.strip() ]
            valid_texts = [ texts[ i ] for i in valid_indices ]
            # اگه هیچ متن معتبری نبود
            if not valid_texts:
                log_message( LG.DataProcessing, "هیچ متن معتبری برای embedding وجود ندارد", LogLevel.WARNING )
                return np.zeros( ( len( texts ), self.vector_dim ) )

            log_message( LG.DataProcessing, f"شروع embedding برای {len(valid_texts)} متن...", LogLevel.INFO )

            if self.model is None:
                log_message( LG.DataProcessing, "مدل بارگذاری نشده است", LogLevel.ERROR )
                raise RuntimeError( "مدل بارگذاری نشده است" )

            #‫ ساخت embeddings با batch
            embeddings_valid = self.model.encode( valid_texts,
                                                  batch_size=self.batch_size,
                                                  normalize_embeddings=normalize,
                                                  convert_to_numpy=True,
                                                  show_progress_bar=show_progress )

            # ‫ساخت آرایه نهایی با zero vectors برای متن‌های خالی
            embeddings = np.zeros( ( len( texts ), self.vector_dim ) )
            for idx, valid_idx in enumerate( valid_indices ):
                embeddings[ valid_idx ] = embeddings_valid[ idx ]

            log_message(
                LG.DataProcessing,
                f"✅ {len(embeddings)} embedding ساخته شد ({len(valid_texts)} معتبر، {len(texts) - len(valid_texts)} خالی)",
                LogLevel.INFO,
            )
            return embeddings

        except Exception as e:
            log_message( LG.DataProcessing, f"❌ خطا در batch embedding: {str(e)}", LogLevel.ERROR )
            raise

    def embed_chunks( self, chunks: List[ dict ], content_field: str = "content" ) -> List[ dict ]:
        """
        ‫ساخت embedding برای لیست chunks و اضافه کردن به هر chunk

        Args:
            chunks: لیست chunks با فیلد content
            content_field: نام فیلد محتوا
        Returns:
            همان chunks با فیلد 'embedding' اضافه‌شده
        """
        try:
            if not chunks:
                return []

            texts = [ chunk.get( content_field, "" ) for chunk in chunks ]
            embeddings = self.embed_batch( texts, normalize=True )

            for chunk, embedding in zip( chunks, embeddings ):
                chunk[ 'embedding' ] = embedding.tolist()

            log_message( LG.DataProcessing, f"✅ embeddings به {len(chunks)} chunk اضافه شد", LogLevel.INFO )
            return chunks

        except Exception as e:
            log_message( LG.DataProcessing, f"❌ خطا در embed_chunks: {str(e)}", LogLevel.ERROR )
            raise

    def get_embedding_dimension( self ) -> int:
        """ ‫‫ بازگشت dimension مدل"""
        return self.vector_dim
