import sys

from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent.parent ) )

from transformers import AutoTokenizer

gte = AutoTokenizer.from_pretrained( "Alibaba-NLP/gte-multilingual-base" )

texts = [ "سلام دنیا", "This is English", "ترکیب Mixed 123 !@#", "متن خیلی طولانی " * 100 ]

for text in texts:
    gte_tokens = len( gte.encode( text ) )

    print( f"{text[:20]:20} | GTE: {gte_tokens:3}" )
