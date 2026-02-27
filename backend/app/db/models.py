from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base


# ==================== SQL Models ====================
class Document( Base ):
    #اطلاعات کلی سند
    __tablename__ = "documents"

    #فیلدهای جدول
    id: Mapped[ int ] = mapped_column( Integer, primary_key=True, index=True )
    file_name: Mapped[ str ] = mapped_column( String( 255 ), unique=True, nullable=False, index=True )
    file_path: Mapped[ str ] = mapped_column( Text, nullable=False )
    total_chunks: Mapped[ int ] = mapped_column( Integer, nullable=False, default=0 )
    file_hash: Mapped[ str ] = mapped_column( String( 64 ), unique=True, nullable=False, index=True )
    indexed_at: Mapped[ datetime ] = mapped_column( DateTime( timezone=True ), server_default=func.now(), nullable=False )

    #ارتباط با جدول چانک ها
    chunks = relationship( "Chunk", back_populates="document", cascade="all, delete-orphan" )

    def __repr__( self ):
        return f"<Document(id={self.id}, file='{self.file_name}', chunks={self.total_chunks})>"


class Chunk( Base ):
    """جدول چانک ها که هر چانک مربوط به یک سند است"""
    __tablename__ = "chunks"

    id: Mapped[ int ] = mapped_column( Integer, primary_key=True, index=True )
    document_id: Mapped[ int ] = mapped_column( Integer, ForeignKey( "documents.id", ondelete="CASCADE" ), nullable=False, index=True )
    chunk_id: Mapped[ str ] = mapped_column( String( 100 ), unique=True, nullable=False, index=True )
    content: Mapped[ str ] = mapped_column( Text, nullable=False )
    chunk_index: Mapped[ int ] = mapped_column( Integer, nullable=False, index=True )          # موقعیت چانک در سند
    token_count: Mapped[ int ] = mapped_column( Integer, nullable=False )

    document = relationship( "Document", back_populates="chunks", passive_deletes=True )

    def __repr__( self ):
        return f"<Chunk(id={self.id}, chunk_index='{self.chunk_index}', tokens={self.token_count})>"
