import sys
from pathlib import Path

sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent.parent ) )

from backend.app.services.retrieval.bm25_indexer import BM25Indexer
from backend.app.utils.logging_config import log_message, LG, LogLevel

# محتوای BM25
bm25 = BM25Indexer()
bm25.load_index()
results = bm25.search( "کارمند کارگر درصد بیمه پرداخت", top_k=20 )
for i, r in enumerate( results ):
    log_message( LG.Retrieval, f"rank {i+1}: {r['chunk_id']} — score: {r['score']:.2f}", LogLevel.INFO )
