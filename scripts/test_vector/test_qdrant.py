import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent.parent ) )

from backend.app.api.dependencies import get_hybrid_retriever
from backend.app.utils.logging_config import log_message, LG, LogLevel

import sys
from pathlib import Path

sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent.parent ) )

retriever = get_hybrid_retriever()
query = "یه کارمند یا کارگر چند درصد از بیمه رو باید پرداخت کنه؟"
results = retriever.retrieve( query )

for i, r in enumerate( results ):
    log_message( LG.Retrieval, f"rank {i+1}: {r['chunk_id']} — rrf_score: {r['rrf_score']:.4f}", LogLevel.INFO )
