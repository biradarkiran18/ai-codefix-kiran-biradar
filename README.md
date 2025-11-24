# AI CodeFix – Secure Code Remediation API (with RAG)

## Overview
This project implements a secure code-fixing API designed to detect and remediate vulnerable code patterns using:

- A lightweight local model 
- Rule-based RAG (Retrieval-Augmented Generation)
- FastAPI backend with structured input/output JSON
- Logged inference metrics
- Assignment-compliant tests (`test_local.py` and `pytest`)

---

## Features

### 1. `/local_fix` API endpoint (FastAPI)
Takes vulnerable code + language + CWE ID and returns:

- `<fixed>` secure code
- `<explanation>` short justification
- No extra text outside the tags

### 2. Small local model
Using:

```
Salesforce/codegen-350M-mono
```

Chosen because:

- It fits CPU-only for my Mac M2 8GB
- It avoids RAM overload
- It satisfies assignment’s “local model” requirement

### 3. RAG Component
- Uses sentence-transformer embeddings
- Uses FAISS vector store
- Retrieves security guidelines based on CWE
- Reads `.txt` files from `recipes/`

### 4. Metrics Logging
Logged to:
```
metrics.csv
```

Includes:
- input tokens
- output tokens
- latency
- model name

### 5. Complete Testing
- `python test_local.py` (assignment script)
- `pytest -q` (API test) → **1 passed**

---

## Input JSON schema

```json
{
  "language": "string",
  "cwe": "string",
  "code": "string"
}
```

---

## Output JSON schema

```json
{
  "fixed_code": "string",
  "explanation": "string",
  "model_used": "string",
  "token_usage": {
    "input_tokens": 0,
    "output_tokens": 0
  },
  "latency_ms": 0
}
```

---

## Project Structure

```
ai-codefix-kiran-biradar/
│
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI app
│   ├── model.py               # Local model loader + inference
│   ├── rag.py                 # RAG retrieval system
│   ├── utils.py               # Metrics + helpers
│
├── recipes/
│   ├── sql_injection.txt
│   └── xss.txt
│
├── tests/
│   └── test_api.py            # API-level pytest
│
├── test_local.py              # Assignment script
├── metrics.csv                # Runtime inference logs
├── requirements.txt
├── README.md
└── Assignment 1.0.pdf
```

---

# Installation

## Clone repo

```bash
git clone https://github.com/biradarkiran18/ai-codefix-kiran-biradar.git
cd ai-codefix-kiran-biradar
```

## Create and activate venv

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Install dependencies

```bash
pip install -r requirements.txt
```

---

# Running the API

## Start server

```bash
uvicorn app.main:app --port 8000
```

## Open docs

```
http://127.0.0.1:8000/docs
```

---

# Example API Usage (curl)

```bash
curl -X POST http://127.0.0.1:8000/local_fix \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "cwe": "CWE-89",
    "code": "def get_user(conn,u): return conn.execute(\"SELECT * FROM users WHERE name='\"+u+\"'\")"
  }'
```

---

# Testing

## Assignment test

```bash
python test_local.py
```

## Unit test

```bash
pytest -q
```

Expected:
```
1 passed
```

---

# Final Submission Checklist

- [x] Uses local small model
- [x] Implements `/local_fix`
- [x] Strict input/output format
- [x] Metrics logged
- [x] RAG implemented
- [x] `test_local.py` passes
- [x] `pytest` passes
- [x] README included
- [x] Folder clean, ready for grading

---

# Notes
- `__init__.py` intentionally left empty (only marks package).
- Model chosen is safe for my Mac M2 8GB without GPU.
- All code follows exact assignment constraints.

