import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent.parent ) )
from backend.app.api.dependencies import get_reranker_service
from backend.app.utils.logging_config import log_message, LG, LogLevel

reranker = get_reranker_service()
query = "یه کارمند یا کارگر چند درصد از بیمه رو باید پرداخت کنه؟"

chunks = [
    {
        "chunk_id":
        "doc_5_chunk_009",
        "content":
        "ماده 28: منابع درآمد سازمان به شرح زیر میباشد: 1- حق بیمه از اول مهر ماه تا پایان سال 1354 به میزان بیست و هشت درصد مزد یا حقوق است که هفت درصد آن به عهده بیمه شده و هجده درصد به عهده کارفرما و سه درصد به وسیله دولت تأمین خواهد شد."
    },
]

results = reranker.rerank( query, chunks, top_k=1 )
log_message( LG.Retrieval, f"score: {results[0]['reranker_score'] if results else 'فیلتر شد!'}'", LogLevel.INFO )
