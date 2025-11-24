from fastapi import FastAPI
from pydantic import BaseModel
from app import model as model_module
from app import rag as rag_module
from app import utils
import time

app = FastAPI(title="Local Fix API (assignment-compliant)")

class LocalFixRequest(BaseModel):
    language: str
    cwe: str
    code: str

@app.on_event("startup")
def startup_event():
    model_module.load_model(device=-1)
    rag_module.load_rag(recipes_dir="recipes")

def extract_between_tags(text: str, start_tag: str, end_tag: str):
    try:
        s = text.index(start_tag) + len(start_tag)
        e = text.index(end_tag, s)
        return text[s:e].strip()
    except ValueError:
        return None

def detect_language_in_code(code: str) -> str:
    c = code.lower()
    # simple heuristics
    if "def " in c or "import " in c or "cur.execute" in c or "return " in c and "cur" in c:
        return "python"
    if "function " in c or "console." in c or "document." in c or "const " in c or "let " in c:
        return "javascript"
    return "unknown"

def generate_with_prompt(prompt: str, max_tokens: int = 200):
    return model_module.generate(prompt, max_new_tokens=max_tokens, device=-1)

@app.post("/local_fix")
async def local_fix(req: LocalFixRequest):
    t0 = time.time()

    # RAG retrieval (optional)
    rag_docs = rag_module.retrieve_top_k(req.language + " " + req.cwe + " " + req.code, k=1)
    context = ""
    if rag_docs:
        context = "RelevantGuideline:\n" + rag_docs[0] + "\n\n"

    # language-specific few-shot examples
    lang = req.language.lower().strip()

    examples = {
        "python": (
            "<VULNERABLE>\n"
            "def get_user(conn, username):\n"
            "    query = \"SELECT * FROM users WHERE name = '\" + username + \"'\"\n"
            "    return conn.execute(query)\n"
            "</VULNERABLE>\n"
            "<fixed>\n"
            "# Use parameterized query (sqlite example)\n"
            "def get_user(conn, username):\n"
            "    cur = conn.cursor()\n"
            "    cur.execute(\"SELECT * FROM users WHERE name = ?\", (username,))\n"
            "    return cur.fetchall()\n"
            "</fixed>\n"
            "<explanation>\n"
            "Replaced unsafe string concatenation with a parameterized query to prevent SQL injection.\n"
            "</explanation>\n"
        ),
        "javascript": (
            "<VULNERABLE>\n"
            "function show(msg){ document.body.innerHTML = 'Message: ' + msg; }\n"
            "</VULNERABLE>\n"
            "<fixed>\n"
            "function show(msg){\n"
            "    const text = document.createTextNode(msg);\n"
            "    const div = document.createElement('div');\n"
            "    div.appendChild(text);\n"
            "    document.body.appendChild(div);\n"
            "}\n"
            "</fixed>\n"
            "<explanation>\n"
            "Insert user content as DOM text nodes (not innerHTML) to prevent XSS.\n"
            "</explanation>\n"
        ),
        "default": (
            "<VULNERABLE>\n"
            "// vulnerable example\n"
            "</VULNERABLE>\n"
            "<fixed>\n"
            "// corrected example\n"
            "</fixed>\n"
            "<explanation>\n"
            "Short explanation of fix.\n"
            "</explanation>\n"
        )
    }

    few_shot = examples.get(lang, examples["default"])

    # build prompt safely (concatenate strings)
    base_prompt = (
        "System: You are a secure code remediation assistant. Follow rules exactly.\n\n"
        + few_shot
        + "\n--- Now your input ---\n"
        + context
        + "LANGUAGE: " + req.language + "\n"
        + "CWE: " + req.cwe + "\n"
        + "VULNERABLE_CODE:\n" + req.code + "\n\n"
        + "Rules:\n"
        + "1) Output EXACTLY two sections in this order: <fixed>...</fixed> THEN <explanation>...</explanation>\n"
        + "2) Do NOT repeat the examples, rules, or the vulnerable code outside the <fixed> block.\n"
        + "3) <fixed> must contain ONLY corrected code in the same language as LANGUAGE.\n"
        + "4) <explanation> must be 1–3 sentences.\n"
        + "5) No extra text.\n"
    )

    tokenizer = model_module.get_tokenizer()
    input_tokens = len(tokenizer.encode(base_prompt))

    # First generation
    out = generate_with_prompt(base_prompt, max_tokens=200)
    output_tokens = len(tokenizer.encode(out))
    fixed = extract_between_tags(out, "<fixed>", "</fixed>") or ""
    explanation = extract_between_tags(out, "<explanation>", "</explanation>") or ""

    # Language check: if returned code language mismatches requested language, do one retry with explicit regeneration instruction.
    returned_lang = detect_language_in_code(fixed)
    requested_lang_simple = "python" if "py" in lang else ("javascript" if "js" in lang or "java" in lang else lang)

    if requested_lang_simple and returned_lang != "unknown" and returned_lang != requested_lang_simple:
        # build a stronger regeneration prompt
        regen_prompt = (
            "Regenerate ONLY the <fixed> and <explanation> sections for the vulnerable code below. "
            "CRITICAL: THE <fixed> CODE MUST BE WRITTEN IN " + requested_lang_simple.upper() + " AND ONLY IN THAT LANGUAGE.\n\n"
            + base_prompt
            + "\nREGENERATE: Produce <fixed> with corrected code in " + requested_lang_simple.upper() + " and then <explanation>.\n"
        )
        out2 = generate_with_prompt(regen_prompt, max_tokens=180)
        output_tokens += len(tokenizer.encode(out2))
        fixed2 = extract_between_tags(out2, "<fixed>", "</fixed>") or ""
        explanation2 = extract_between_tags(out2, "<explanation>", "</explanation>") or ""
        # accept second attempt if it looks better (language matches or non-empty)
        if fixed2 and detect_language_in_code(fixed2) == requested_lang_simple:
            fixed = fixed2
            explanation = explanation2
            out = out + "\n\n" + out2

    diff = utils.make_diff(req.code, fixed)
    latency_ms = int((time.time() - t0) * 1000)

    utils.log_metrics({
        "timestamp": int(time.time()),
        "language": req.language,
        "cwe": req.cwe,
        "model_used": model_module.MODEL_NAME,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_ms": latency_ms
    })

    return {
        "fixed_code": fixed,
        "diff": diff,
        "explanation": explanation,
        "model_used": model_module.MODEL_NAME,
        "token_usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        },
        "latency_ms": latency_ms
    }
