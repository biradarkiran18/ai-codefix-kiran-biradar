
import difflib
import time
import csv
from pathlib import Path

METRICS_FILE = Path("metrics.csv")


def make_diff(original: str, fixed: str) -> str:
    return "\n".join(difflib.unified_diff(
        original.splitlines(), fixed.splitlines(),
        fromfile="vulnerable", tofile="fixed", lineterm=""
    ))


def log_metrics(row: dict):
    header = ["timestamp", "language", "cwe", "model_used", "input_tokens", "output_tokens", "latency_ms"]
    write_header = not METRICS_FILE.exists()
    with METRICS_FILE.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=header)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def now_ms():
    return int(time.time() * 1000)
