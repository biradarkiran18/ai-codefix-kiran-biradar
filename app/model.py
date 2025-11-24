
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import threading
import os

MODEL_NAME = os.getenv("MODEL_NAME", "Salesforce/codegen-350M-mono")
_lock = threading.Lock()
_model = None
_tokenizer = None
_pipeline = None


def load_model(device=-1):
    global _model, _tokenizer, _pipeline
    with _lock:
        if _pipeline is not None:
            return _pipeline
        # load tokenizer and model (may be slow on first run)
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
        _model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
        _pipeline = pipeline(
            "text-generation",
            model=_model,
            tokenizer=_tokenizer,
            device=device,  # device=-1 for CPU, 0 for GPU
        )
        return _pipeline


def get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        load_model()
    return _tokenizer


def generate(prompt, max_new_tokens=512, device=-1):
    gen = load_model(device=device)
    out = gen(prompt, max_new_tokens=max_new_tokens, do_sample=False)[0]["generated_text"]
    return out

