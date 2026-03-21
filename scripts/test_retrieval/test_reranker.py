# scripts/test_reranker_direct.py
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_PATH = r"E:\A-Golchin program\Ai\Models\bge-reranker-v2-m3"

tokenizer = AutoTokenizer.from_pretrained( MODEL_PATH, trust_remote_code=True )
model = AutoModelForSequenceClassification.from_pretrained( MODEL_PATH, trust_remote_code=True )
model.eval()

pairs = [
    [ "حداقل مزد کارگر در سال 1404 چقدر است؟", "حداقل مزد روزانه: 3,463,656 ریال - حداقل مزد ماهانه: 103,909,680 ریال" ],
    [ "حداقل مزد کارگر در سال 1404 چقدر است؟", "ماده 79: به کار گماردن افراد کمتر از 15 سال کامل ممنوع است." ],
]

inputs = tokenizer( pairs, padding=True, truncation=True, max_length=512, return_tensors="pt" )

with torch.no_grad():
    logits = model( **inputs ).logits.squeeze( -1 )
    scores = torch.sigmoid( logits )

print( f"Raw logits: {logits.tolist()}" )
print( f"Sigmoid scores: {scores.tolist()}" )
