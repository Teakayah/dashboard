import time
from typing import Optional

def _clean_set(val: str) -> Optional[float]:
    v = val.strip()
    if v in {"", "..", "F", "x", "E", "r", "p"}:
        return None
    try:
        return float(v)
    except ValueError:
        return None

def _clean_tuple(val: str) -> Optional[float]:
    v = val.strip()
    if v in ("", "..", "F", "x", "E", "r", "p"):
        return None
    try:
        return float(v)
    except ValueError:
        return None

start = time.time()
for _ in range(1000000):
    _clean_set("x")
    _clean_set("1.2")
print("Set:", time.time() - start)

start = time.time()
for _ in range(1000000):
    _clean_tuple("x")
    _clean_tuple("1.2")
print("Tuple:", time.time() - start)
