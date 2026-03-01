from typing import List, Dict, Any
from pydantic import ValidationError
from backend.app.services.vector.qdrant_client import QdrantManager
from backend.app.schemas.chunk_schemas import ChunkMetadata
from backend.app.utils.logging_config import log_message, LG, LogLevel


class QdrantIndexer:
    """
   ‫ مدیریت indexing در Qdrant
    - ‫ذخیره embeddings با metadata
    - ‫حذف documents
    - آمارگیری
    """

    def __init__( self, qdrant_manager: QdrantManager ):
        self.qdrant = qdrant_manager
        log_message( LG.Database, "QdrantIndexer آماده شد", LogLevel.INFO )

    def index_chunks( self, chunks: List[ Dict[ str, Any ] ] ) -> bool:
        """
       ‫ ایجاد index برای chunks در Qdrant
        
        Args:
            ‫chunks: لیست chunks که هر کدام باید 'embedding' داشته باشند
            
        Returns:
            True در صورت موفقیت
        """
        try:

            log_message( LG.Database, f"شروع indexing {len(chunks)} chunk در Qdrant...", LogLevel.INFO )

            valid_ids = []
            valid_embeddings = []
            valid_metadata = []

            # ‫شمارش خطاها برای batch logging
            error_counts = { 'missing_embedding': 0, 'validation_error': 0 }
            first_validation_error: str | None = None

            for chunk in chunks:
                try:
                    #‫بررسی وجود embedding
                    if 'embedding' not in chunk:
                        error_counts[ 'missing_embedding' ] += 1
                        continue

                    # ‫ترکیب metadata با chunk_id برای validation
                    raw_metadata = { **chunk.get( 'metadata', {} ), 'chunk_id': chunk.get( 'chunk_id' ) }

                    # ‫Validation با Pydantic
                    validated = ChunkMetadata.model_validate( raw_metadata )

                    # اضافه به لیست‌های معتبر
                    valid_ids.append( validated.chunk_id )
                    valid_embeddings.append( chunk[ 'embedding' ] )
                    valid_metadata.append( validated.model_dump() )

                except ValidationError as e:
                    error_counts[ 'validation_error' ] += 1
                    #‫ فقط اولین خطا رو log کن برای debug
                    if first_validation_error is None:
                        first_validation_error = e.json()

            # Batch logging برای خطاها
            total_errors = sum( error_counts.values() )
            if total_errors > 0:
                log_message(
                    LG.Database, f"⚠️ {total_errors} chunk رد شد - "
                    f"فاقد embedding: {error_counts['missing_embedding']}, "
                    f"خطای validation: {error_counts['validation_error']}", LogLevel.WARNING )

            if first_validation_error:
                log_message( LG.Database, f"نمونه اول خطای validation: {first_validation_error}", LogLevel.DEBUG )

            # ‫اگه هیچ chunk معتبری نبود، fail کن
            if not valid_ids:
                log_message( LG.Database, "❌ هیچ chunk معتبری برای indexing وجود ندارد", LogLevel.ERROR )
                return False

            # ‫ذخیره در Qdrant
            success = self.qdrant.insert_vectors( chunk_ids=valid_ids, embeddings=valid_embeddings, metadata=valid_metadata )

            if success:
                log_message( LG.Database, f"✅ {len(valid_ids)} chunk در Qdrant ذخیره شد", LogLevel.INFO )
            else:
                log_message( LG.Database, "❌ خطا در ذخیره chunks در Qdrant", LogLevel.ERROR )

            return success

        except Exception as e:
            log_message( LG.Database, f"❌ خطا در QdrantIndexer.index_chunks: {str(e)}", LogLevel.ERROR )
            return False

    def delete_document_vectors( self, document_id: int ) -> bool:
        """
       ‫ حذف تمام vectors مربوط به یک document
        
        Args:
            document_id: شناسه document
            
        Returns:
            True در صورت موفقیت
        """
        try:
            success = self.qdrant.delete_by_document( document_id )

            if success:
                log_message( LG.Database, f"✅ Vectors document {document_id} حذف شد", LogLevel.INFO )
            else:
                log_message( LG.Database, f"⚠️ خطا در حذف vectors document {document_id}", LogLevel.WARNING )

            return success

        except Exception as e:
            log_message( LG.Database, f"❌ خطا در حذف vectors: {str(e)}", LogLevel.ERROR )
            return False

    def get_stats( self ) -> Dict[ str, Any ]:
        """
        دریافت آمار Qdrant collection
        
        Returns:
            دیکشنری حاوی آمار
        """
        try:
            info = self.qdrant.get_collection_info()

            stats = {
                'total_vectors': info.get( 'vectors_count', 0 ),
                'status': info.get( 'status', 'unknown' ),
                'collection_name': self.qdrant.collection_name
            }

            log_message( LG.Database, f"آمار Qdrant: {stats['total_vectors']} vectors", LogLevel.DEBUG )
            return stats

        except Exception as e:
            log_message( LG.Database, f"خطا در دریافت آمار Qdrant: {str(e)}", LogLevel.ERROR )
            return { 'total_vectors': 0, 'status': 'error' }
