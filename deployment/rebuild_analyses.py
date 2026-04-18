#!/usr/bin/env python3
"""
Rebuild analysis HTML pages from Stats Canada CSV data.

Reads the downloaded CSVs in source/Stat Can/ and injects updated
data constants (const DATA / const RAW) into the analysis HTML files.

Exit code: 0 = no HTML changed, 1 = one or more files updated.
"""

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "source" / "Stat Can"


# ── CSV helpers ────────────────────────────────────────────────────────────────


def _read_csv(path: Path) -> list[dict]:
    """Read a Stats Canada CSV (UTF-8 BOM) into a list of row dicts with pre-stripped keys/values."""
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        try:
            headers = [h.strip() for h in next(reader)]
        except StopIteration:
            return []
        return [dict(zip(headers, (v.strip() for v in row))) for row in reader]


def _clean(val: str) -> float | None:
    """Return float or None for Stats Canada VALUE cells. Assumes `val` is pre-stripped."""
    v = val
    if v in ("", "..", "F", "x", "E", "r", "p"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


# ── Extractors for employment_rate_canada.html ────────────────────────────────


def extract_emp_rate(rows: list[dict]) -> dict:
    """Annual average employment rate (%) by province — table 14100287."""
    buckets: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if (
            row["Labour force characteristics"] == "Employment rate"
            and row["Gender"] == "Total - Gender"
            and row["Age group"] == "15 years and over"
            and row["Statistics"] == "Estimate"
            and row["Data type"] == "Seasonally adjusted"
        ):
            val = _clean(row["VALUE"])
            if val is not None:
                year = int(row["REF_DATE"][:4])
                buckets[row["GEO"]][year].append(val)

    return {
        geo: sorted(
            [{"year": y, "value": round(sum(vs) / len(vs), 2)} for y, vs in yd.items()],
            key=lambda r: r["year"],
        )
        for geo, yd in buckets.items()
    }


def extract_emp_jobs(rows: list[dict]) -> dict:
    """Annual avg employed persons (thousands) + year-over-year change — table 14100287."""
    buckets: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if (
            row["Labour force characteristics"] == "Employment"
            and row["Gender"] == "Total - Gender"
            and row["Age group"] == "15 years and over"
            and row["Statistics"] == "Estimate"
            and row["Data type"] == "Seasonally adjusted"
        ):
            val = _clean(row["VALUE"])
            if val is not None:
                year = int(row["REF_DATE"][:4])
                buckets[row["GEO"]][year].append(val)

    result = {}
    for geo, yd in buckets.items():
        series = []
        prev = None
        for year in sorted(yd):
            level = round(sum(yd[year]) / len(yd[year]), 1)
            change = round(level - prev, 1) if prev is not None else None
            series.append({"year": year, "level": level, "change": change})
            prev = level
        result[geo] = series
    return result


def extract_fed_debt(rows: list[dict]) -> list[dict]:
    """Annual average Federal government liabilities (billions $) — table 10100015."""
    buckets: dict[int, list[float]] = defaultdict(list)
    for row in rows:
        if (
            row["GEO"] == "Canada"
            and row["Government sectors"] == "Federal government"
            and row["Statement of government operations and balance sheet"]
            == "Liabilities"
        ):
            val = _clean(row["VALUE"])
            if val is not None:
                year = int(row["REF_DATE"][:4])
                buckets[year].append(val)

    return sorted(
        [
            {"year": y, "value": round(sum(vs) / len(vs) / 1000, 1)}
            for y, vs in buckets.items()
        ],
        key=lambda r: r["year"],
    )


def extract_prov_debt(rows: list[dict]) -> dict:
    """Provincial liabilities (billions $) — table 10100017, stocks."""
    data: dict[str, dict[int, float]] = defaultdict(dict)
    for row in rows:
        if (
            row["Public sector components"] == "Provincial and territorial governments"
            and row["Display value"] == "Stocks"
            and row["Statement of operations and balance sheet"] == "Liabilities [63]"
        ):
            val = _clean(row["VALUE"])
            if val is not None:
                geo = row["GEO"]
                year = int(row["REF_DATE"])
                data[geo][year] = val

    return {
        geo: sorted(
            [{"year": y, "value": round(v / 1000, 1)} for y, v in yd.items()],
            key=lambda r: r["year"],
        )
        for geo, yd in data.items()
    }


def extract_pop_data(rows: list[dict]) -> dict:
    """Annual population by province + year-over-year change — table 17100005."""
    data: dict[str, dict[int, int]] = defaultdict(dict)
    for row in rows:
        if row["Gender"] == "Total - gender" and row["Age group"] == "All ages":
            val = _clean(row["VALUE"])
            if val is not None:
                geo = row["GEO"]
                year = int(row["REF_DATE"])
                data[geo][year] = int(val)

    result = {}
    for geo, yd in data.items():
        series = []
        prev = None
        for year in sorted(yd):
            pop = yd[year]
            change = pop - prev if prev is not None else None
            pct = round((pop - prev) / prev * 100, 2) if prev is not None else None
            series.append({"year": year, "pop": pop, "change": change, "pct": pct})
            prev = pop
        result[geo] = series
    return result


# ── Extractor for nhpi_big6_comparison.html ───────────────────────────────────


def extract_nhpi(rows: list[dict]) -> dict:
    """Monthly NHPI by city — table 18100205."""
    measures = ["Total (house and land)", "House only", "Land only"]

    # Locate the index column (name varies slightly across releases)
    idx_col = (
        next(
            (k for k in rows[0] if "housing price" in k.lower()),
            None,
        )
        if rows
        else None
    )
    if not idx_col:
        print("  WARNING: could not find housing price index column in 18100205.")
        return {}

    buckets: dict[str, dict[str, dict[str, float]]] = defaultdict(
        lambda: {m: {} for m in measures}
    )
    for row in rows:
        measure = row[idx_col]
        if measure not in measures:
            continue
        val = _clean(row["VALUE"])
        if val is None:
            continue
        date = row["REF_DATE"]  # "1981-01"
        geo = row["GEO"]
        buckets[geo][measure][date] = val

    result = {}
    for geo, mdata in buckets.items():
        result[geo] = {}
        for m, dates in mdata.items():
            result[geo][m] = sorted(
                [{"date": d, "value": v} for d, v in dates.items()],
                key=lambda r: r["date"],
            )
    return result


# ── HTML injection helpers ────────────────────────────────────────────────────


def _inject_const(html: str, var_name: str, new_value: object) -> tuple[str, bool]:
    """Replace `const VAR = {...};` (single-line or multiline) with new JSON value."""
    new_json = json.dumps(new_value, separators=(",", ":"), ensure_ascii=False)
    pattern = rf"const {re.escape(var_name)}\s*=\s*\{{.*?\}};"
    replacement = f"const {var_name}={new_json};"
    new_html, n = re.subn(pattern, replacement, html, count=1, flags=re.DOTALL)
    return new_html, n > 0 and new_html != html


# ── Per-analysis rebuild functions ────────────────────────────────────────────


def rebuild_employment(html_path: Path) -> bool:
    """Rebuild const DATA={...} in employment_rate_canada.html."""
    print(f"Rebuilding {html_path.name}...")

    lfs_csv = SRC / "Employment" / "14100287-eng" / "14100287.csv"
    gov_csv = SRC / "Employment" / "10100015-eng" / "10100015.csv"
    prov_csv = SRC / "Employment" / "10100017-eng" / "10100017.csv"
    pop_csv = SRC / "Employment" / "17100005-eng" / "17100005.csv"

    missing = [p for p in [lfs_csv, gov_csv, prov_csv, pop_csv] if not p.exists()]
    if missing:
        print(f"  SKIP — missing CSV(s): {[p.name for p in missing]}")
        return False

    print("  Reading 14100287 (labour force)...")
    lfs_rows = _read_csv(lfs_csv)

    print("  Reading 10100015 (government finance)...")
    gov_rows = _read_csv(gov_csv)

    print("  Reading 10100017 (provincial operations)...")
    prov_rows = _read_csv(prov_csv)

    print("  Reading 17100005 (population)...")
    pop_rows = _read_csv(pop_csv)

    new_data = {
        "empRate": extract_emp_rate(lfs_rows),
        "empJobs": extract_emp_jobs(lfs_rows),
        "provDebt": extract_prov_debt(prov_rows),
        "fedDebt": extract_fed_debt(gov_rows),
        "popData": extract_pop_data(pop_rows),
    }

    html = html_path.read_text(encoding="utf-8")
    new_html, changed = _inject_const(html, "DATA", new_data)

    if not changed:
        print("  No change in DATA.")
        return False

    html_path.write_text(new_html, encoding="utf-8")
    print(f"  DATA updated in {html_path.name}")
    return True


def rebuild_nhpi(html_path: Path) -> bool:
    """Rebuild const RAW={...} in nhpi_big6_comparison.html."""
    print(f"Rebuilding {html_path.name}...")

    nhpi_csv = SRC / "Housing" / "18100205-eng" / "18100205.csv"
    if not nhpi_csv.exists():
        print(f"  SKIP — {nhpi_csv.relative_to(ROOT)} not found.")
        print("         Run update_statcan_data.py first to download table 18100205.")
        return False

    print("  Reading 18100205 (NHPI)...")
    rows = _read_csv(nhpi_csv)
    raw = extract_nhpi(rows)

    html = html_path.read_text(encoding="utf-8")
    new_html, changed = _inject_const(html, "RAW", raw)

    if not changed:
        print("  No change in RAW.")
        return False

    html_path.write_text(new_html, encoding="utf-8")
    print(f"  RAW updated in {html_path.name}")
    return True


def rebuild_flood(html_path: Path) -> bool:
    """Rebuild const DATA={...} in flood_risk_gatineau_ottawa.html."""
    print(f"Rebuilding {html_path.name}...")

    flood_json = ROOT / "source" / ".flood_data.json"
    if not flood_json.exists():
        print(f"  SKIP — {flood_json.name} not found.")
        return False

    data = json.loads(flood_json.read_text(encoding="utf-8"))

    html = html_path.read_text(encoding="utf-8")
    new_html, changed = _inject_const(html, "DATA", data)

    if not changed:
        print("  No change in DATA.")
        return False

    html_path.write_text(new_html, encoding="utf-8")
    print(f"  DATA updated in {html_path.name}")
    return True


# ── Registry: HTML file → rebuild function ────────────────────────────────────

REBUILDERS = {
    "employment_rate_canada.html": rebuild_employment,
    "nhpi_big6_comparison.html": rebuild_nhpi,
    "flood_risk_gatineau_ottawa.html": rebuild_flood,
}


def main() -> int:
    print("Rebuilding analysis pages from Stats Canada data...\n")
    any_changed = False

    for filename, rebuild_fn in REBUILDERS.items():
        html_path = ROOT / filename
        if not html_path.exists():
            print(f"SKIP {filename} — file not found in repo root.\n")
            continue
        try:
            changed = rebuild_fn(html_path)
            any_changed = any_changed or changed
        except Exception as exc:
            print(f"  ERROR rebuilding {filename}: {exc}")
        print()

    print(f"Done. Files changed: {any_changed}")
    return 1 if any_changed else 0


if __name__ == "__main__":
    sys.exit(main())
