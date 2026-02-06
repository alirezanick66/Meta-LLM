from sqlalchemy import Column, DateTime, ForeignKey, Index, Index, Integer, String, String, Text, func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Document( Base ):
    __tablename__ = "documents"

    #فیلدهای جدول
    id = Column( Integer, primary_key=True, index=True )
    file_name = Column( String, unique=True, nullable=False, index=True )
    file_path = Column( Text, nullable=False )
    total_pages = Column( Integer, nullable=True )
    total_chunks = Column( Integer, nullable=False, default=0 )
    file_hash = Column( String( 64 ), unique=True, nullable=False, index=True )
    indexed_at = Column( DateTime( timezone=True ), server_default=func.now(), nullable=False )

    #ارتباط با جدول چانک ها
    chunks = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__( self ):
        return f"<Document(id={self.id}, filename='{self.file_name}', chunks={self.total_chunks})>"


class Chunk( Base ):
    """جدول چانک ها که هر چانک مربوط به یک سند است"""
    __tablename__ = "chunks"

    id = Column( Integer, primary_key=True, index=True )
    document_id = Column( Integer, ForeignKey( "documents.id", ondelete="CASCADE" ), nullable=False, index=True )
    chunk_id = Column( String( 100 ), unique=True, nullable=False, index=True )
    content = Column( Text, nullable=False )
    chunk_index = Column( Integer, nullable=False )          # موقعیت چانک در سند
    token_count = Column( Integer, nullable=False )
    page_range = Column( String( 20 ), nullable=True )          # مثلاً "5-7"
    created_at = Column( DateTime( timezone=True ), server_default=func.now(), nullable=False )

    document = relationship( "Document", back_populates="chunks" )

    def __repr__( self ):
        return f"<Chunk(id={self.id}, chunk_index='{self.chunk_index}', tokens={self.token_count})>"


# Indexes برای بهبود performance
Index( 'idx_chunks_document_id', Chunk.document_id )
Index( 'idx_chunks_chunk_index', Chunk.chunk_index )
Index( 'idx_documents_filename', Document.file_name )
Index( 'idx_documents_file_hash', Document.file_hash )
