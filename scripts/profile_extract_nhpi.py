import time
from collections import defaultdict

def extract_nhpi_list(rows: list[dict]) -> dict:
    measures = ["Total (house and land)", "House only", "Land only"]
    idx_col = "measure"
    buckets: dict[str, dict[str, dict[str, float]]] = defaultdict(
        lambda: {m: {} for m in measures}
    )
    for row in rows:
        measure = row[idx_col].strip()
        if measure not in measures:
            continue
        val = row["VALUE"]
        date = row["REF_DATE"]
        geo = row["GEO"]
        buckets[geo][measure][date] = val
    return buckets

def extract_nhpi_set(rows: list[dict]) -> dict:
    measures = ["Total (house and land)", "House only", "Land only"]
    idx_col = "measure"
    buckets: dict[str, dict[str, dict[str, float]]] = defaultdict(
        lambda: {m: {} for m in measures}
    )
    for row in rows:
        measure = row[idx_col].strip()
        if measure not in {"Total (house and land)", "House only", "Land only"}:
            continue
        val = row["VALUE"]
        date = row["REF_DATE"]
        geo = row["GEO"]
        buckets[geo][measure][date] = val
    return buckets

rows = [
    {"measure": "Total (house and land)", "VALUE": 100.0, "REF_DATE": "2020-01", "GEO": "Canada"},
    {"measure": "House only", "VALUE": 100.0, "REF_DATE": "2020-01", "GEO": "Canada"},
    {"measure": "Land only", "VALUE": 100.0, "REF_DATE": "2020-01", "GEO": "Canada"},
    {"measure": "Other", "VALUE": 100.0, "REF_DATE": "2020-01", "GEO": "Canada"},
] * 100000

start = time.time()
extract_nhpi_list(rows)
print("List:", time.time() - start)

start = time.time()
extract_nhpi_set(rows)
print("Set:", time.time() - start)
