## What is included
- FastAPI service exposing POST /local_fix
- RAG support using SentenceTransformers + FAISS; place guideline .txt files in `recipes/`
- Metrics logged to `metrics.csv`
- Test script `test_local.py` and unit test `tests/test_api.py`
- Small default model: Salesforce/codegen-350M-mono (I used this because its safe for Mac M2 with 8GB)


## Input JSON schema (request)
```json
{
"language": "<string>",
"cwe": "<string>",
"code": "<string>"
}