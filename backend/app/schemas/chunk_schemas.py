from pydantic import BaseModel


class ChunkMetadata( BaseModel ):
    """متادیتای chunk برای Qdrant"""
    chunk_id: str
    document_id: int
    source: str
    chunk_index: int
    title: str | None = None
    section: str | None = None
    subsection: str | None = None
    hierarchy: str | None = None
    has_list: bool = False
    heading_level: int = 0

    class Config:
        extra = 'ignore'
