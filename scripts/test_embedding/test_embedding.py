import sys
import time
import numpy as np
from pathlib import Path

sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent.parent ) )

from backend.app.api.dependencies import get_embedding_service
from backend.app.utils.logging_config import log_message, LG, LogLevel

embedding_service = get_embedding_service()

# ==================== تست 1: Single Text Embedding ====================
log_message( LG.DataProcessing, "\n📝 تست 1: embed_single - متن عادی", LogLevel.INFO )
try:
    start_time = time.time()

    text = "این یک جمله تست است"
    embedding = embedding_service.embed_single( text )

    elapsed = time.time() - start_time

    log_message( LG.DataProcessing, f"✅ Embedding ساخته شد:", LogLevel.INFO )
    log_message( LG.DataProcessing, f"  - متن: '{text}'", LogLevel.INFO )
    log_message( LG.DataProcessing, f"  - Shape: {embedding.shape}", LogLevel.INFO )
    log_message( LG.DataProcessing, f"  - Type: {type(embedding)}", LogLevel.DEBUG )
    log_message( LG.DataProcessing, f"  - زمان اجرا: {elapsed:.3f}s", LogLevel.INFO )

    # چک نرمال بودن
    norm = np.linalg.norm( embedding )
    log_message( LG.DataProcessing, f"  - Norm: {norm:.6f} (باید ~1.0 باشد)", LogLevel.DEBUG )

except Exception as e:
    log_message( LG.DataProcessing, f"❌ خطا: {e}", LogLevel.ERROR )

# ==================== تست 2: Empty Text ====================
log_message( LG.DataProcessing, "\n📝 تست 2: embed_single - متن خالی", LogLevel.INFO )
try:
    empty_texts = [ "", "   ", "\n\t", None ]

    for i, text in enumerate( empty_texts ):
        embedding = embedding_service.embed_single( text if text else "" )
        is_zero = np.allclose( embedding, 0 )

        log_message( LG.DataProcessing, f"  - متن {i+1} ('{repr(text)}'): {'✅ Zero vector' if is_zero else '❌ غیرمنتظره!'}",
                     LogLevel.INFO )

except Exception as e:
    log_message( LG.DataProcessing, f"❌ خطا: {e}", LogLevel.ERROR )

# ==================== تست 3: Batch Embedding ====================
log_message( LG.DataProcessing, "\n📝 تست 3: embed_batch", LogLevel.INFO )
try:
    texts = [
        "جمله اول",
        "جمله دوم",
        "",          # متن خالی
        "جمله سوم",
        "   ",          # whitespace
        "جمله چهارم"
    ]

    start_time = time.time()
    embeddings = embedding_service.embed_batch( texts )
    elapsed = time.time() - start_time

    log_message( LG.DataProcessing, f"✅ Batch embedding انجام شد:", LogLevel.INFO )
    log_message( LG.DataProcessing, f"  - تعداد ورودی: {len(texts)}", LogLevel.INFO )
    log_message( LG.DataProcessing, f"  - Shape خروجی: {embeddings.shape}", LogLevel.INFO )
    log_message( LG.DataProcessing, f"  - زمان اجرا: {elapsed:.3f}s ({elapsed/len(texts):.3f}s per text)", LogLevel.INFO )

    # چک zero vectors
    for i, text in enumerate( texts ):
        is_zero = np.allclose( embeddings[ i ], 0 )
        if not text or not text.strip():
            status = "✅" if is_zero else "❌"
            log_message( LG.DataProcessing, f"  - Index {i} (متن خالی): {status} {'Zero vector' if is_zero else 'غیرمنتظره!'}",
                         LogLevel.DEBUG )

except Exception as e:
    log_message( LG.DataProcessing, f"❌ خطا: {e}", LogLevel.ERROR )

# ==================== تست 4: Embed Chunks ====================
log_message( LG.DataProcessing, "\n📝 تست 4: embed_chunks", LogLevel.INFO )
chunks = [
    {
        "chunk_id": "chunk_001",
        "content": "انقلاب یه حرکت رادیکالی محسوب میشه"
    },
    {
        "chunk_id": "chunk_002",
        "content": "مردم ایران در انقلاب نقش اساسی داشتند"
    },
    {
        "chunk_id": "chunk_003",
        "content": ""          # متن خالی
    },
    {
        "chunk_id": "chunk_004",
        "content": "امام خمینی رهبری انقلاب را بر عهده داشت"
    },
]

try:
    start_time = time.time()
    chunks_with_embeddings = embedding_service.embed_chunks( chunks )
    elapsed = time.time() - start_time

    log_message( LG.DataProcessing, f"✅ embeddings به {len(chunks_with_embeddings)} chunk اضافه شد", LogLevel.INFO )
    log_message( LG.DataProcessing, f"  - زمان اجرا: {elapsed:.3f}s", LogLevel.INFO )

    for i, chunk in enumerate( chunks_with_embeddings ):
        emb = chunk[ 'embedding' ]
        emb_len = len( emb )
        is_list = isinstance( emb, list )
        is_zero = all( x == 0 for x in emb ) if is_list else np.allclose( emb, 0 )

        log_message(
            LG.DataProcessing,
            f"  - Chunk {i+1}: {chunk['chunk_id']} | dim: {emb_len} | type: {'list' if is_list else 'array'} | zero: {is_zero}",
            LogLevel.INFO )

        # چک که همه embeddings لیست باشن (نه numpy array)
        assert is_list, f"Chunk {i+1} embedding باید list باشه نه {type(emb)}"

    log_message( LG.DataProcessing, "  ✅ همه embeddings به صورت list هستند (memory leak نداریم)", LogLevel.INFO )

except AssertionError as e:
    log_message( LG.DataProcessing, f"❌ Assertion failed: {e}", LogLevel.ERROR )
except Exception as e:
    log_message( LG.DataProcessing, f"❌ خطا: {e}", LogLevel.ERROR )

# ==================== تست 5: Performance - Large Batch ====================
log_message( LG.DataProcessing, "\n📝 تست 5: Performance - Large Batch", LogLevel.INFO )
try:
    large_texts = [ f"این متن شماره {i} برای تست performance است" for i in range( 100 ) ]

    start_time = time.time()
    large_embeddings = embedding_service.embed_batch( large_texts, show_progress=False )
    elapsed = time.time() - start_time

    log_message( LG.DataProcessing, f"✅ Large batch پردازش شد:", LogLevel.INFO )
    log_message( LG.DataProcessing, f"  - تعداد: {len(large_texts)}", LogLevel.INFO )
    log_message( LG.DataProcessing, f"  - زمان کل: {elapsed:.3f}s", LogLevel.INFO )
    log_message( LG.DataProcessing, f"  - میانگین: {elapsed/len(large_texts)*1000:.2f}ms per text", LogLevel.INFO )
    log_message( LG.DataProcessing, f"  - Throughput: {len(large_texts)/elapsed:.1f} texts/second", LogLevel.INFO )

except Exception as e:
    log_message( LG.DataProcessing, f"❌ خطا: {e}", LogLevel.ERROR )
