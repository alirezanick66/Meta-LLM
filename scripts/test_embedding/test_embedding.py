import sys
from pathlib import Path

sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent.parent ) )

from backend.app.services.embedding.embedding_service import EmbeddingService
import numpy as np

emb = EmbeddingService()

# ‫تست با دو جمله مشابه و یه جمله نامربوط
t1 = "سهم کارگر از حق بیمه چند درصد است"
t2 = "کارمند چه مقدار بیمه پرداخت میکند"
t3 = "آب و هوای تهران چطور است"

v1 = emb.embed_single( t1 )
v2 = emb.embed_single( t2 )
v3 = emb.embed_single( t3 )

sim12 = np.dot( v1, v2 )
sim13 = np.dot( v1, v3 )

print( f"شباهت جمله ۱ و ۲ (مشابه): {sim12:.4f}" )
print( f"شباهت جمله ۱ و ۳ (نامربوط): {sim13:.4f}" )
print( f"آیا sim12 > sim13: {sim12 > sim13}" )
