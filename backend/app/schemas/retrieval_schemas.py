from enum import StrEnum


class RetrievalMethod( StrEnum ):
    """‫روش‌های بازیابی"""
    BM25 = "bm25"
    VECTOR = "vector"


class ResultKeys( StrEnum ):
    """‫کلیدهای استاندارد نتایج retrieval"""
    CHUNK_ID = "chunk_id"
    SCORE = "score"
    RETRIEVAL_METHOD = "retrieval_method"
    METADATA = "metadata"
    CONTENT = "content"


class RRFKeys( StrEnum ):
    """‫کلیدهای مربوط به RRF score و رتبه‌ها"""
    BM25_SCORE = "bm25_score"
    VECTOR_SCORE = "vector_score"
    BM25_RANK = "bm25_rank"
    VECTOR_RANK = "vector_rank"
    RRF_SCORE = "rrf_score"


class RRFStats( StrEnum ):
    """‫کلیدهای آمار RRF"""
    BOTH = "both"
    ONLY_BM25 = "only_bm25"
    ONLY_VECTOR = "only_vector"
