import gc
import threading
import torch
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from backend.app.core.config import settings
from backend.app.utils.logging_config import log_message, LG, LogLevel


class EmbeddingService:
    """
    سرویس Embedding با BGE-M3
    - پشتیبانی از batch processing
    - بهینه‌سازی برای CPU
    - مدیریت حافظه
    """

    def __init__( self ):
        """
        مقداردهی اولیه مدل
        """
        self.model_name = settings.EMBEDDING_MODEL
        self.device = settings.EMBEDDING_DEVICE
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
        self.model = None
        self.vector_dim = settings.EMBEDDING_VECTOR_DIM
        self._load_model()

    def _load_model( self ):
        """بارگذاری مدل BGE-M3"""
        try:
            log_message( LG.DataProcessing, f"در حال بارگذاری مدل {self.model_name}...", LogLevel.INFO )

            self.model = SentenceTransformer( settings.EMBEDDING_MODEL_PATH,
                                              device=self.device,
                                              token=settings.EMBEDDING_MODEL_TOKEN,
                                              trust_remote_code=True )

            # بهینه‌سازی برای CPU
            if self.device == "cpu":
                torch.set_num_threads( settings.CPU_THREADS )
                log_message( LG.DataProcessing, "تنظیمات CPU optimization اعمال شد", LogLevel.DEBUG )

            # تست مدل
            test_embedding = self.model.encode( "تست" )
            actual_dim = len( test_embedding )

            if actual_dim != self.vector_dim:
                log_message( LG.DataProcessing, f"⚠️ تغییر dimension: انتظار {self.vector_dim}، دریافت {actual_dim}",
                             LogLevel.WARNING )
                self.vector_dim = actual_dim

            log_message( LG.DataProcessing, f"✅ مدل بارگذاری شد - Device: {self.device}, Dimension: {self.vector_dim}",
                         LogLevel.INFO )

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
            numpy array با dimension 1024
        """
        try:
            if not text or not text.strip():
                log_message( LG.DataProcessing, "متن خالی برای embedding", LogLevel.WARNING )
                return np.zeros( self.vector_dim )

            if self.model is None:
                raise RuntimeError( "مدل بارگذاری نشده است" )

            embedding = self.model.encode( text, normalize_embeddings=normalize, show_progress_bar=False )

            # Convert to numpy array if it's a tensor
            if isinstance( embedding, torch.Tensor ):
                embedding = embedding.cpu().numpy()
            elif not isinstance( embedding, np.ndarray ):
                embedding = np.array( embedding )

            return embedding

        except Exception as e:
            log_message( LG.DataProcessing, f"خطا در ساخت embedding: {str(e)}", LogLevel.ERROR )
            raise

    def embed_batch( self, texts: List[ str ], normalize: bool = True, show_progress: bool = False ) -> np.ndarray:
        """
        ساخت embedding برای چندین متن (batch)
        
        Args:
            texts: لیست متن‌ها
            normalize: نرمال‌سازی vectors
            show_progress: نمایش progress bar
            
        Returns:
            numpy array
        """
        if not texts:
            log_message( LG.DataProcessing, "لیست متن‌ها خالی است", LogLevel.WARNING )
            return np.zeros( ( 0, self.vector_dim ) )

        try:
            # شناسایی متن‌های معتبر
            valid_indices = []
            valid_texts = []

            for i, text in enumerate( texts ):
                if text and text.strip():
                    valid_indices.append( i )
                    valid_texts.append( text )
            # اگه هیچ متن معتبری نبود
            if not valid_texts:
                log_message( LG.DataProcessing, "هیچ متن معتبری برای embedding وجود ندارد", LogLevel.WARNING )
                return np.zeros( ( len( texts ), self.vector_dim ) )

            log_message( LG.DataProcessing, f"شروع embedding برای {len(valid_texts)} متن...", LogLevel.INFO )

            if self.model is None:
                log_message( LG.DataProcessing, "مدل بارگذاری نشده است", LogLevel.ERROR )
                raise RuntimeError( "مدل بارگذاری نشده است" )

            # ساخت embeddings با batch
            embeddings_valid = self.model.encode( valid_texts,
                                                  batch_size=self.batch_size,
                                                  normalize_embeddings=normalize,
                                                  show_progress_bar=show_progress )

            # ساخت آرایه نهایی با zero vectors برای متن‌های خالی
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
        ساخت embedding برای لیست chunks
        
        Args:
            chunks: لیست chunks (هر chunk یک dict)
            content_field: نام فیلد محتوا در chunk
            
        Returns:
            همان chunks با اضافه شدن فیلد 'embedding'
        """
        try:
            if not chunks:
                log_message( LG.DataProcessing, "لیست chunks خالی است", LogLevel.WARNING )
                return []

            # استخراج محتواها
            texts = [ chunk.get( content_field, "" ) for chunk in chunks ]

            log_message( LG.DataProcessing, f"ساخت embeddings برای {len(texts)} chunk...", LogLevel.INFO )

            # ساخت embeddings
            embeddings = self.embed_batch( texts, normalize=True, show_progress=False )

            # اضافه کردن به chunks
            for chunk, embedding in zip( chunks, embeddings ):
                # تبدیل به list برای قطع reference
                chunk[ 'embedding' ] = embedding.tolist()

            log_message( LG.DataProcessing, f"✅ embeddings به chunks اضافه شد", LogLevel.INFO )

            return chunks

        except Exception as e:
            log_message( LG.DataProcessing, f"❌ خطا در embed_chunks: {str(e)}", LogLevel.ERROR )
            raise

    def get_embedding_dimension( self ) -> int:
        """بازگشت dimension مدل"""
        return self.vector_dim

    def calculate_similarity( self, embedding1: np.ndarray, embedding2: np.ndarray, are_normalized: bool = True ) -> float:
        """
        محاسبه cosine similarity بین دو embedding
        
        Args:
            embedding1: اولین embedding
            embedding2: دومین embedding
            are_normalized: آیا embeddings از قبل normalized هستند؟ (default: True)
            
        Returns:
            similarity score (-1 تا 1، هرچه نزدیک‌تر به 1 باشد شباهت بیشتر است)
        """

        try:
            # تبدیل به numpy اگه list بود
            if isinstance( embedding1, list ):
                embedding1 = np.array( embedding1 )
            if isinstance( embedding2, list ):
                embedding2 = np.array( embedding2 )

            # چک ابعاد
            if embedding1.shape != embedding2.shape:
                raise ValueError( f"ابعاد embeddings یکسان نیست: {embedding1.shape} vs {embedding2.shape}" )

            if are_normalized:
                # برای normalized embeddings فقط dot product کافیه
                return float( np.dot( embedding1, embedding2 ) )
            else:
                # محاسبه کامل cosine similarity
                norm1 = np.linalg.norm( embedding1 )
                norm2 = np.linalg.norm( embedding2 )

                if norm1 == 0 or norm2 == 0:
                    log_message( LG.DataProcessing, "⚠️ یکی از embeddings برابر صفر است", LogLevel.WARNING )
                    return 0.0

                return float( np.dot( embedding1, embedding2 ) / ( norm1 * norm2 ) )

        except Exception as e:
            log_message( LG.DataProcessing, f"خطا در محاسبه similarity: {str(e)}", LogLevel.ERROR )
            return 0.0

    def cleanup( self ):
        """آزادسازی حافظه مدل (فقط در حالت single-thread یا بعد از اتمام کارها)"""
        if self.model is not None:
            try:
                del self.model
                self.model = None

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

                gc.collect()

                log_message( LG.DataProcessing, "🧹 حافظه مدل تخلیه شد", LogLevel.INFO )
            except Exception as e:
                log_message( LG.DataProcessing, f"خطا در cleanup: {e}", LogLevel.ERROR )


_embedding_service_instance = None
_lock = threading.Lock()


def get_embedding_service() -> EmbeddingService:
    """
    Singleton pattern با thread safety
    """
    global _embedding_service_instance

    if _embedding_service_instance is None:
        with _lock:
            # Double-check locking
            if _embedding_service_instance is None:
                _embedding_service_instance = EmbeddingService()

    return _embedding_service_instance


def reset_embedding_service():
    """
    ریست کامل سرویس و آزادسازی حافظه
    """
    global _embedding_service_instance

    with _lock:          # حتماً قفل بگیرید تا در حین حذف کسی درخواست ندهد
        if _embedding_service_instance is not None:
            _embedding_service_instance.cleanup()          # فراخوانی متد جدید
            _embedding_service_instance = None
