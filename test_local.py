
# test_local.py
import requests, time

URL = "http://localhost:8000/local_fix"
samples = [
    {
        "language": "python",
        "cwe": "CWE-89",
        "code": """def get_user(conn, username):
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    return conn.execute(query)
"""
    },
    {
        "language": "javascript",
        "cwe": "CWE-79",
        "code": "function show(msg){ document.body.innerHTML = 'Message: ' + msg; }"
    }
]


def run():
    for s in samples:
        t0 = time.time()
        r = requests.post(URL, json=s, timeout=120)
        t1 = time.time()
        print("Sample:", s["language"], s["cwe"])
        if r.status_code == 200:
            j = r.json()
            print("model_used:", j.get("model_used"))
            print("token_usage:", j.get("token_usage"))
            print("latency_ms (reported):", j.get("latency_ms"))
            print("measured latency (ms):", int((t1 - t0) * 1000))
            print("diff:\n", j.get("diff")[:1000])
            print("-" * 60)
        else:
            print("STATUS", r.status_code, r.text)


if __name__ == "__main__":
    run()

