from typing import List, Optional
from sqlalchemy.orm import Session
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
            document = Document(
                file_name=filename,
                file_path=file_path,
                file_hash=file_hash,
                total_chunks=total_chunks,
            )
            self.db.add( document )
            self.db.commit()
            self.db.refresh( document )
            log_message( LG.Database, f"سند جدید ایجاد شد: {filename}", LogLevel.INFO )
            return document
        except Exception as e:
            self.db.rollback()
            log_message( LG.Database, f"خطا در ایجاد سند: {str(e)}", LogLevel.ERROR )
            raise

    def get_document_by_id( self, document_id: int ) -> Optional[ Document ]:
        """دریافت سند با ID"""
        return self.db.query( Document ).filter( Document.id == document_id ).first()

    def get_document_by_filename( self, filename: str ) -> Optional[ Document ]:
        """دریافت سند با نام فایل"""
        return self.db.query( Document ).filter( Document.file_name == filename ).first()

    def get_document_by_hash( self, file_hash: str ) -> Optional[ Document ]:
        """دریافت سند با hash"""
        return self.db.query( Document ).filter( Document.file_hash == file_hash ).first()

    def get_all_documents( self ) -> List[ Document ]:
        """دریافت تمام اسناد"""
        return self.db.query( Document ).all()

    def update_document_chunks_count( self, document_id: int, total_chunks: int ) -> bool:
        """به‌روزرسانی تعداد chunks یک سند"""
        try:
            self.db.query( Document ).filter( Document.id == document_id ).update(
                { Document.total_chunks: total_chunks } )
            self.db.commit()
            log_message( LG.Database, f"تعداد chunks سند {document_id} به‌روز شد", LogLevel.INFO )
            return True

        except Exception as e:
            self.db.rollback()
            log_message( LG.Database, f"خطا در به‌روزرسانی سند: {str(e)}", LogLevel.ERROR )
            return False

    def delete_document( self, document_id: int ) -> bool:
        """حذف سند (chunks هم به صورت خودکار حذف می‌شن)"""
        try:
            document = self.get_document_by_id( document_id )
            if document:
                self.db.delete( document )
                self.db.commit()
                log_message( LG.Database, f"سند {document_id} حذف شد", LogLevel.INFO )
                return True
            return False
        except Exception as e:
            self.db.rollback()
            log_message( LG.Database, f"خطا در حذف سند: {str(e)}", LogLevel.ERROR )
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
            log_message( LG.Database, f"خطا در ایجاد chunk: {str(e)}", LogLevel.ERROR )
            raise

    def bulk_create_chunks( self, chunks_data: List[ dict ] ) -> bool:
        """ایجاد دسته‌جمعی chunks"""
        try:
            chunks = [ Chunk( **data ) for data in chunks_data ]
            self.db.bulk_save_objects( chunks )
            self.db.commit()
            log_message( LG.Database, f"{len(chunks)} chunk ایجاد شد", LogLevel.INFO )
            return True

        except Exception as e:
            self.db.rollback()
            log_message( LG.Database, f"خطا در ایجاد دسته‌جمعی chunks: {str(e)}", LogLevel.ERROR )
            return False

    def get_chunk_by_id( self, chunk_id: str ) -> Optional[ Chunk ]:
        """دریافت chunk با chunk_id"""
        return self.db.query( Chunk ).filter( Chunk.chunk_id == chunk_id ).first()

    def get_chunks_by_document( self, document_id: int ) -> List[ Chunk ]:
        """دریافت تمام chunks یک سند"""
        return self.db.query( Chunk ).filter( Chunk.document_id == document_id ).order_by( Chunk.chunk_index ).all()

    def delete_chunks_by_document( self, document_id: int ) -> bool:
        """حذف تمام chunks یک سند"""
        try:
            deleted = self.db.query( Chunk ).filter( Chunk.document_id == document_id ).delete()
            self.db.commit()
            log_message( LG.Database, f"{deleted} chunk از سند {document_id} حذف شد", LogLevel.INFO )
            return True
        except Exception as e:
            self.db.rollback()
            log_message( LG.Database, f"خطا در حذف chunks: {str(e)}", LogLevel.ERROR )
            return False

    def get_chunk_content( self, chunk_id: str ) -> Optional[ str ]:
        """دریافت محتوای یک chunk"""
        chunk = self.get_chunk_by_id( chunk_id )
        return str( chunk.content ) if chunk else None

    def get_total_chunks_count( self ) -> int:
        """تعداد کل chunks در دیتابیس"""
        return self.db.query( Chunk ).count()

    def get_total_documents_count( self ) -> int:
        """تعداد کل اسناد در دیتابیس"""
        return self.db.query( Document ).count()

    def get_all_chunks( self ) -> List[ Chunk ]:
        """دریافت تمام chunks از دیتابیس"""
        try:
            return self.db.query( Chunk ).all()
        except Exception as e:
            log_message( LG.Database, f"خطا در دریافت تمام chunks: {str(e)}", LogLevel.ERROR )
            return []
