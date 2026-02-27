from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.db.models import Document, Chunk
from backend.app.utils.logging_config import log_message, LG, LogLevel


class PostgresManager:
    """
   ‫ مدیریت عملیات CRUD برای PostgreSQL
    """

    def __init__( self, db: Session ):
        self.db = db

    # ==================== Document Operations ====================
    def create_document( self, filename: str, file_path: str, file_hash: str, total_chunks: int = 0 ) -> Document:
        """ایجاد سند جدید"""
        try:
            doc = Document( file_name=filename, file_path=file_path, file_hash=file_hash, total_chunks=total_chunks )
            self.db.add( doc )
            self.db.commit()
            self.db.refresh( doc )

            log_message( LG.Database, f"✅ سند ایجاد شد: {filename}", LogLevel.INFO )
            return doc
        except Exception as e:
            self.db.rollback()
            log_message( LG.Database, f"❌ خطا در ایجاد سند: {str(e)}", LogLevel.ERROR )
            raise

    def get_document_by_hash( self, file_hash: str ) -> Optional[ Document ]:
        """ ‫دریافت سند با hash"""
        return self.db.query( Document ).filter_by( file_hash=file_hash ).first()

    def get_document_by_filename( self, filename: str ) -> Optional[ Document ]:
        """دریافت سند با نام فایل"""
        return self.db.query( Document ).filter_by( file_name=filename ).first()

    def get_all_documents( self ) -> List[ Document ]:
        """دریافت تمام اسناد"""
        return self.db.query( Document ).all()

    def update_document_chunks_count( self, document_id: int, total_chunks: int ) -> bool:
        """ ‫به‌روزرسانی تعداد chunks"""
        try:
            # ‫استفاده از filter_by برای خوانایی بیشتر
            self.db.query( Document ).filter_by( id=document_id ).update( { "total_chunks": total_chunks } )
            self.db.commit()
            log_message( LG.Database, f"✅ chunks count سند {document_id} آپدیت شد", LogLevel.INFO )
            return True
        except Exception as e:
            self.db.rollback()
            log_message( LG.Database, f"❌ خطا در آپدیت سند: {str(e)}", LogLevel.ERROR )
            return False

    def delete_document( self, document_id: int ) -> bool:
        """
        حذف سند 
       ‫ chunks به دلیل Cascade در مدل DB خودکار حذف می‌شوند.
        """
        try:
            doc = self.db.get( Document, document_id )
            if doc:
                self.db.delete( doc )
                self.db.commit()
                log_message( LG.Database, f"🗑️ سند {document_id} حذف شد", LogLevel.INFO )
                return True
            return False
        except Exception as e:
            self.db.rollback()
            log_message( LG.Database, f"❌ خطا در حذف سند: {str(e)}", LogLevel.ERROR )
            return False

    # ==================== Chunk Operations ====================
    def bulk_create_chunks( self, chunks_data: List[ Dict[ str, Any ] ] ) -> bool:
        """ ‫ایجاد چندین chunk به صورت یکجا"""
        try:
            chunks_objects = [ Chunk( **data ) for data in chunks_data ]
            self.db.add_all( chunks_objects )
            self.db.commit()

            log_message( LG.Database, f"✅ {len(chunks_objects)} chunk ایجاد شد", LogLevel.INFO )
            return True
        except Exception as e:
            self.db.rollback()
            log_message( LG.Database, f"❌ خطا در bulk create: {str(e)}", LogLevel.ERROR )
            raise

    def get_chunks_content_bulk( self, chunk_ids: List[ str ] ) -> Dict[ str, str ]:
        """ ‫دریافت محتوای چندین chunk به صورت یکجا"""
        if not chunk_ids:
            return {}

        try:
            # انتخاب فقط دو ستون مورد نیاز برای سرعت بیشتر
            chunks = self.db.query( Chunk.chunk_id, Chunk.content ).filter( Chunk.chunk_id.in_( chunk_ids ) ).all()
            return { cid: content for cid, content in chunks }          # تبدیل لیست تاپل‌ها به دیکشنری

        except Exception as e:
            log_message( LG.Database, f"❌ خطا در bulk get: {str(e)}", LogLevel.ERROR )
            return {}

    def get_chunks_by_document( self, document_id: int ) -> List[ Chunk ]:
        """دریافت تمام ‫ chunks یک سند"""
        return self.db.query( Chunk ).filter_by( document_id=document_id ).order_by( Chunk.chunk_index ).all()

    def get_all_chunks( self ) -> List[ Chunk ]:
        """  ‫دریافت تمام chunks های همه مستندات"""
        return self.db.query( Chunk ).all()

    def get_total_chunks_count( self ) -> int:
        """ ‫تعداد کل chunks"""
        return self.db.query( func.count( Chunk.id ) ).scalar()          # یا self.db.query(Chunk).count()

    def get_total_documents_count( self ) -> int:
        """تعداد کل اسناد"""
        return self.db.query( func.count( Document.id ) ).scalar()
