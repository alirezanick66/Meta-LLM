import re
from typing import List, Dict, Any
from transformers import AutoTokenizer
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from backend.app.core.config import settings
from backend.app.utils.logging_config import log_message, LG, LogLevel

# ==========================================
# توکنایزر BGE-M3
# ==========================================
log_message( LG.DataProcessing, "Initializing tokenizer for chunking...", LogLevel.INFO )
tokenizer = AutoTokenizer.from_pretrained( settings.EMBEDDING_MODEL )
log_message( LG.DataProcessing, "Tokenizer loaded.", LogLevel.INFO )


def count_tokens( text: str ) -> int:
    if not text: return 0
    return len( tokenizer.encode( text, add_special_tokens=False ) )


def count_words( text: str ) -> int:
    """شمارش کلمات بر اساس فاصله (سریع و کافی برای فارسی)"""
    if not text: return 0
    return len( text.split() )


# ==========================================
#  Chunker
# ==========================================
class MarkdownChunker:

    def __init__( self ):
        # 1. تقسیم بر اساس هدرها
        self.md_splitter = MarkdownHeaderTextSplitter( headers_to_split_on=[
            ( "#", "Header 1" ),
            ( "##", "Header 2" ),
            ( "###", "Header 3" ),
            ( "####", "Header 4" ),
        ] )

        # 2. تقسیم بر اساس طول توکن
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=count_tokens,
            separators=[ "\n\n", "\n", "،", ".", " ", "" ],
        )

    def _get_header_string( self, metadata: Dict ) -> str:
        """ساخت هدر تمیز برای تزریق"""
        h1 = metadata.get( "Header 1", "" )
        h2 = metadata.get( "Header 2", "" )
        h3 = metadata.get( "Header 3", "" )
        parts = [ p for p in [ h1, h2, h3 ] if p ]
        return " > ".join( parts )

    def _detect_list( self, text: str ) -> bool:
        return bool( re.search( r'^[\-\*\+]\s+', text, re.MULTILINE ) )

    def create_chunks( self, markdown_text: str, doc_id: int, source_file: str ) -> List[ Dict[ str, Any ] ]:

        md_docs = self.md_splitter.split_text( markdown_text )
        final_chunks = []

        # استفاده از شمارنده سراسری در متد
        global_chunk_index = 0

        for doc in md_docs:
            content_raw = doc.page_content
            md_metadata = doc.metadata

            if not content_raw.strip():
                continue

            # تقسیم متن طولانی
            if count_tokens( content_raw ) > settings.CHUNK_SIZE:
                sub_chunks = self.text_splitter.split_text( content_raw )
            else:
                sub_chunks = [ content_raw ]

            header_str = self._get_header_string( md_metadata )
            title = md_metadata.get( "Header 1" )
            section = md_metadata.get( "Header 2" )
            subsection = md_metadata.get( "Header 3" )
            hierarchy = header_str

            heading_level = 0
            if subsection: heading_level = 3
            elif section: heading_level = 2
            elif title: heading_level = 1

            # اصلاح حلقه:
            for sub_text in sub_chunks:
                final_content = f"{header_str}\n\n{sub_text}" if header_str else sub_text

                chunk_data = {
                    "chunk_id": f"doc_{doc_id}_chunk_{global_chunk_index:03d}",          # ✅ ID یکتا
                    "content": final_content,
                    "token_count": count_tokens( final_content ),
                    "word_count": count_words( final_content ),
                    "metadata": {
                        "document_id": doc_id,
                        "source": source_file,
                        "title": title,
                        "section": section,
                        "subsection": subsection,
                        "hierarchy": hierarchy,
                        "chunk_index": global_chunk_index,
                        "has_list": self._detect_list( sub_text ),
                        "heading_level": heading_level
                # total_chunks حذف شد (بهتر است در دیتابیس محاسبه شود)
                    }
                }
                final_chunks.append( chunk_data )
                global_chunk_index += 1          # ⭐ افزایش شمارنده سراسری

        return final_chunks
