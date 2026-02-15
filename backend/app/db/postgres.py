from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.db.models import Document, Chunk
from backend.app.utils.logging_config import log_message, LG, LogLevel


class PostgresManager:
    """
    مدیریت عملیات CRUD برای PostgreSQL
    """

    def __init__( self, db: Session ):
        self.db = db

    # ==================== Document Operations ====================

    def create_document(
        self,
        filename: str,
        file_path: str,
        file_hash: str,
        total_chunks: int = 0,
    ) -> Document:
        """ایجاد سند جدید"""
        try:
            doc = Document(
                file_name=filename,
                file_path=file_path,
                file_hash=file_hash,
                total_chunks=total_chunks,
            )
            self.db.add( doc )
            self.db.commit()
            self.db.refresh( doc )
            log_message( LG.Database, f"✅ سند ایجاد شد: {filename}", LogLevel.INFO )
            return doc
        except Exception as e:
            self.db.rollback()
            log_message( LG.Database, f"❌ خطا در ایجاد سند: {str(e)}", LogLevel.ERROR )
            raise

    def get_document_by_id( self, document_id: int ) -> Optional[ Document ]:
        """دریافت سند با ID (بسیار سریع با استفاده از Session.get)"""
        return self.db.get( Document, document_id )

    def get_document_by_hash( self, file_hash: str ) -> Optional[ Document ]:
        """دریافت سند با hash"""
        return self.db.query( Document ).filter_by( file_hash=file_hash ).first()

    def get_document_by_filename( self, filename: str ) -> Optional[ Document ]:
        """دریافت سند با نام فایل"""
        return self.db.query( Document ).filter_by( file_name=filename ).first()

    def get_all_documents( self ) -> List[ Document ]:
        """دریافت تمام اسناد"""
        return self.db.query( Document ).all()

    def update_document_chunks_count( self, document_id: int, total_chunks: int ) -> bool:
        """به‌روزرسانی تعداد chunks"""
        try:
            # استفاده از filter_by برای خوانایی بیشتر
            self.db.query( Document ).filter_by( id=document_id ).update( { Document.total_chunks: total_chunks } )
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            log_message( LG.Database, f"❌ خطا در آپدیت سند: {str(e)}", LogLevel.ERROR )
            return False

    def delete_document( self, document_id: int ) -> bool:
        """
        حذف سند 
        chunks به دلیل Cascade در مدل DB خودکار حذف می‌شوند.
        """
        try:
            result = self.db.query( Document ).filter_by( id=document_id ).delete()
            self.db.commit()
            if result:
                log_message( LG.Database, f"🗑️ سند {document_id} حذف شد", LogLevel.INFO )
            return result > 0
        except Exception as e:
            self.db.rollback()
            log_message( LG.Database, f"❌ خطا در حذف سند: {str(e)}", LogLevel.ERROR )
            return False

    # ==================== Chunk Operations ====================

    def create_chunk(
        self,
        document_id: int,
        chunk_id: str,
        content: str,
        chunk_index: int,
        token_count: int,
    ) -> Chunk:
        """ایجاد chunk جدید"""
        try:
            chunk = Chunk( document_id=document_id,
                           chunk_id=chunk_id,
                           content=content,
                           chunk_index=chunk_index,
                           token_count=token_count )
            self.db.add( chunk )
            self.db.commit()
            self.db.refresh( chunk )
            return chunk
        except Exception as e:
            self.db.rollback()
            log_message( LG.Database, f"❌ خطا در ایجاد chunk: {str(e)}", LogLevel.ERROR )
            raise

    def get_chunk_content( self, chunk_id: str ) -> Optional[ str ]:
        """
        این متد حافظه و پهنای باند بسیار کمتری مصرف می‌کند چون کل آبجکت را لود نمی‌کند.
        """
        return self.db.query( Chunk.content ).filter_by( chunk_id=chunk_id ).scalar()

    def get_chunks_content_bulk( self, chunk_ids: List[ str ] ) -> Dict[ str, str ]:
        """دریافت محتوای چندین chunk به صورت یکجا"""
        if not chunk_ids:
            return {}

        try:
            # انتخاب فقط دو ستون مورد نیاز برای سرعت بیشتر
            chunks = self.db.query( Chunk.chunk_id, Chunk.content ).filter( Chunk.chunk_id.in_( chunk_ids ) ).all()

            # تبدیل لیست تاپل‌ها به دیکشنری
            return { cid: content for cid, content in chunks }
        except Exception as e:
            log_message( LG.Database, f"❌ خطا در bulk get: {str(e)}", LogLevel.ERROR )
            return {}

    def bulk_create_chunks( self, chunks_data: List[ Dict[ str, Any ] ] ) -> bool:
        try:
            chunks_objects = [ Chunk( **data ) for data in chunks_data ]
            self.db.add_all( chunks_objects )
            self.db.commit()
            log_message( LG.Database, f"✅ {len(chunks_objects)} chunk ایجاد شد", LogLevel.INFO )
            return True
        except Exception as e:
            self.db.rollback()
            log_message( LG.Database, f"❌ خطا در bulk create: {str(e)}", LogLevel.ERROR )
            return False

    def get_chunk_by_id( self, chunk_id: str ) -> Optional[ Chunk ]:
        """دریافت chunk با chunk_id"""
        return self.db.query( Chunk ).filter_by( chunk_id=chunk_id ).first()

    def get_chunks_by_document( self, document_id: int ) -> List[ Chunk ]:
        """دریافت تمام chunks یک سند"""
        return self.db.query( Chunk ).filter_by( document_id=document_id ).order_by( Chunk.chunk_index ).all()

    def delete_chunks_by_document( self, document_id: int ) -> bool:
        """حذف تمام chunks یک سند"""
        try:
            count = self.db.query( Chunk ).filter_by( document_id=document_id ).delete()
            self.db.commit()
            log_message( LG.Database, f"🗑️ {count} chunk حذف شد", LogLevel.INFO )
            return True
        except Exception as e:
            self.db.rollback()
            log_message( LG.Database, f"❌ خطا در حذف chunks: {str(e)}", LogLevel.ERROR )
            return False

    def get_total_chunks_count( self ) -> int:
        """تعداد کل chunks"""
        return self.db.query( func.count( Chunk.id ) ).scalar()          # یا self.db.query(Chunk).count()

    def get_total_documents_count( self ) -> int:
        """تعداد کل اسناد"""
        return self.db.query( func.count( Document.id ) ).scalar()

    def get_all_chunks( self ) -> List[ Chunk ]:
        return self.db.query( Chunk ).all()
