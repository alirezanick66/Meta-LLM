import hashlib
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import ( Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue )
from backend.app.core.config import settings
from backend.app.utils.logging_config import log_message, LG, LogLevel


class QdrantManager:
    """
   ‫ مدیریت عملیات Qdrant Vector Store
    """

    def __init__( self ):
        self.client: Optional[ QdrantClient ] = None
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.vector_size = settings.EMBEDDING_VECTOR_DIM
        self._connect()

    def _connect( self ):
        """
       ‫ اتصال به Qdrant 
        """
        try:
            log_message( LG.Database, f"تلاش برای اتصال به Qdrant...", LogLevel.INFO )

            self.client = QdrantClient( host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=60 )

            # ✅ تست اتصال با فراخوانی یک متد ساده
            self.client.get_collections()

            log_message( LG.Database, "✅ اتصال به Qdrant با موفقیت برقرار شد", LogLevel.INFO )
            self._create_collection_if_not_exists()
            return          # موفقیت

        except Exception as e:
            log_message( LG.Database, f"❌ خطا در اتصال به Qdrant بعد از تلاش: {str(e)}", LogLevel.ERROR )
            raise ConnectionError( f"امکان اتصال به Qdrant وجود ندارد: {str(e)}" )

    @staticmethod
    def _generate_point_id( chunk_id: str ) -> int:
        """ ‫تبدیل chunk_id به یک عدد یکتا بدون collision"""
        hash_bytes = hashlib.sha256( chunk_id.encode() ).digest()[ :8 ]
        return int.from_bytes( hash_bytes, byteorder='big' )

    def _create_collection_if_not_exists( self ):
        """ایجاد کالکشن اگر وجود نداشته باشد"""
        try:

            if self.client is not None:          #اگه اتصال برقرار شده بود
                collections = self.client.get_collections().collections          #لیست کالکشن های موجود در ‫ Qdrant
                collection_names = [ col.name for col in collections ]

                if self.collection_name not in collection_names:          #اگه کالکشن وجود نداشت، ایجادش کن
                    self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(
                            size=self.vector_size,
                            distance=Distance.COSINE          #‫ استفاده از cosine similarity
                        ) )
                    log_message( LG.Database, f"کالکشن '{self.collection_name}' ایجاد شد", LogLevel.INFO )
                else:
                    log_message( LG.Database, f"کالکشن '{self.collection_name}' از قبل وجود دارد", LogLevel.INFO )
        except Exception as e:
            log_message( LG.Database, f"خطا در ایجاد کالکشن: {str(e)}", LogLevel.ERROR )
            raise

    def insert_vectors( self, chunk_ids: List[ str ], embeddings: List[ List[ float ] ],
                        metadata: List[ Dict[ str, Any ] ] ) -> bool:
        """
        ‫ درج دسته‌جمعی vectors
            """
        if self.client is None:
            log_message( LG.Database, "❌ Qdrant client اتصال برقرار نشده است", LogLevel.ERROR )
            return False
        try:
            points = []
            for chunk_id, embedding, meta in zip( chunk_ids, embeddings, metadata ):
                point = PointStruct( id=self._generate_point_id( chunk_id ),
                                     vector=embedding,
                                     payload={
                                         "chunk_id": chunk_id,
                                         **meta
                                     } )
                points.append( point )

            self.client.upsert( collection_name=self.collection_name, points=points )
            log_message( LG.Database, f"{len(points)} vector به Qdrant اضافه شد", LogLevel.INFO )
            return True
        except Exception as e:
            log_message( LG.Database, f"خطا در درج vectors: {str(e)}", LogLevel.ERROR )
            return False

    def search_vectors( self,
                        query_vector: List[ float ],
                        top_k: int = 20,
                        document_id: Optional[ int ] = None ) -> List[ Dict[ str, Any ] ]:
        """
           ‫ جستجوی semantic با vector
            
            Args:
                query_vector: embedding سوال
                top_k: تعداد نتایج
                document_id: فیلتر بر اساس document_id (اختیاری)
            """
        if self.client is None:
            return []
        try:
            query_filter = None
            if document_id:
                query_filter = Filter( must=[ FieldCondition( key="document_id", match=MatchValue( value=document_id ) ) ] )

            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
                query_filter=query_filter,
                with_payload=True,          # ← اضافه کن
            ).points          # خروجی این متد یک شیء است که فیلد points دارد

            # تبدیل نتایج به format مناسب
            formatted_results = []
            for result in results:
                payload = result.payload or {}
                formatted_results.append( {
                    "chunk_id": payload.get( "chunk_id" ),
                    "score": result.score,
                    "metadata": payload
                } )

            log_message( LG.Retrieval, f"{len(formatted_results)} نتیجه از Qdrant بازگردانده شد", LogLevel.DEBUG )
            return formatted_results
        except Exception as e:
            log_message( LG.Retrieval, f"خطا در جستجوی vectors: {str(e)}", LogLevel.ERROR )
            return []

    def delete_by_document( self, document_id: int ) -> bool:
        """ ‫حذف تمام vectors مربوط به یک document"""
        try:
            self.client.delete(          # type: ignore
                collection_name=self.collection_name,
                points_selector=Filter( must=[ FieldCondition( key="document_id", match=MatchValue( value=document_id ) ) ] ) )
            log_message( LG.Database, f"Vectors مربوط به document {document_id} حذف شد", LogLevel.INFO )
            return True
        except Exception as e:
            log_message( LG.Database, f"خطا در حذف vectors: {str(e)}", LogLevel.ERROR )
            return False

    def get_collection_info( self ) -> Dict[ str, Any ]:
        """ ‫دریافت اطلاعات collection"""
        try:
            info = self.client.get_collection( self.collection_name )          # type: ignore
            return {
                "points_count": info.points_count,          # ✅ این وجود داره
                "vectors_count": info.points_count,          # ‫ همون points_count هست
                "status": info.status
            }
        except Exception as e:
            log_message( LG.Database, f"خطا در دریافت اطلاعات کالکشن: {str(e)}", LogLevel.ERROR )
            return {}


# Instance سراسری
def get_qdrant_manager():
    return QdrantManager()
