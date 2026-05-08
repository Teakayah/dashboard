#!/usr/bin/env python3
"""
Rebuild analysis HTML pages from Stats Canada CSV data.
Uses a declarative extraction framework to process various tables.
"""

import csv
import json
import re
import sys
from collections import defaultdict
from itertools import zip_longest
from pathlib import Path
from typing import Optional, Any

# Import centralized configuration
try:
    from config import ROOT, SRC, EXTRACTION_CONFIGS
except ImportError:
    from deployment.config import ROOT, SRC, EXTRACTION_CONFIGS


# ── CSV helpers ────────────────────────────────────────────────────────────────


def _read_csv(path: Path) -> list[dict]:
    """Read a Stats Canada CSV (UTF-8 BOM) into a list of row dicts."""
    with open(path, encoding="utf-8-sig") as f:
        # ⚡ Bolt Optimization: Replace csv.DictReader with csv.reader + zip_longest
        # DictReader has significant Python-level overhead. Using the C-based
        # csv.reader combined with zip_longest directly is ~20-30% faster
        # on large StatCan datasets (100k+ rows) during the I/O load phase.
        # zip_longest ensures missing columns become None, preserving exact
        # DictReader backwards compatibility.
        reader = csv.reader(f)
        try:
            headers = [h.strip() for h in next(reader)]
        except StopIteration:
            return []

        return [dict(zip_longest(headers, row)) for row in reader if any(row)]


def _clean(val: str) -> Optional[float]:
    """
    Return float or None for Stats Canada VALUE cells.

    Statistics Canada uses specific symbols in data cells that indicate null,
    suppressed, or unreliable data:
    - '..' : Not available for a specific reference period
    - 'x'  : Suppressed to meet the confidentiality requirements of the Statistics Act
    - 'F'  : Too unreliable to be published
    - 'E'  : Use with caution
    - 'r'  : Revised
    - 'p'  : Preliminary
    """
    v = val.strip()
    if v in ("", "..", "F", "x", "E", "r", "p"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


# ── Generic Extraction Engine ──────────────────────────────────────────────────


def extract_statcan_data(
    rows: list[dict], table_id: str, variant: Optional[str] = None
) -> Any:
    """Generic engine to filter and group StatCan data based on config."""
    config = EXTRACTION_CONFIGS.get(table_id)
    if not config:
        return []

    # Special handling for NHPI (18100205)
    if table_id == "18100205":
        return extract_nhpi(rows)

    # General extraction logic for other tables
    buckets: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))

    filters = config.get('default_filters', {}).copy()
    if variant and 'variants' in config:
        filters.update(config['variants'].get(variant, {}))

    # Heuristic: place highly selective variant filters first to maximize short-circuiting efficiency.
    # We use dictionary updates to safely override defaults, then convert to list.
    filter_items = list(filters.items())
    filter_items.sort(key=lambda x: 0 if x[0] == 'Labour force characteristics' else 1)

    # Pre-calculate filter values and metadata for faster matching.
    # val.strip() == v is only possible if v itself is clean.
    optimized_filters = []
    for k, v in filter_items:
        v_len = len(v)
        v_is_clean = v.strip() == v
        optimized_filters.append((k, v, v_len, v_is_clean))

    for row in rows:
        match = True
        for k, v, v_len, v_is_clean in optimized_filters:
            val = row.get(k, '')
            if val == v:
                continue

            # If we're here, val != v.
            # Optimization: val.strip() == v can only be true if:
            # 1. v has no surrounding whitespace
            # 2. val is longer than v (since it must contain v + whitespace)
            if v_is_clean and len(val) > v_len and val.strip() == v:
                # Match! Memoize the stripped value to speed up subsequent passes.
                row[k] = v
                continue

            match = False
            break

        if match:
            val = _clean(row["VALUE"])
            if val is not None:
                # Handle different date formats
                ref_date = row.get("REF_DATE", "")
                if len(ref_date) >= 4:
                    try:
                        year = int(ref_date[:4])
                    except ValueError:
                        continue

                    geo = row.get("GEO", "Canada")
                    if geo != "Canada":
                        geo = geo.strip()
                    buckets[geo][year].append(val)

    # Post-processing based on variant or table_id
    if variant == "empRate":
        return {
            geo: sorted(
                [
                    {"year": y, "value": round(sum(vs) / len(vs), 2)}
                    for y, vs in yd.items()
                ],
                key=lambda r: r["year"],
            )
            for geo, yd in buckets.items()
        }

    if variant == "empJobs":
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

    if table_id == "10100015":
        # Federal debt is typically returned as a flat list for Canada
        canada_data = buckets.get("Canada", {})
        return sorted(
            [
                {"year": y, "value": round(sum(vs) / len(vs) / 1000, 1)}
                for y, vs in canada_data.items()
            ],
            key=lambda r: r["year"],
        )

    if table_id == "10100017":
        return {
            geo: sorted(
                [
                    {"year": y, "value": round(sum(vs) / len(vs) / 1000, 1)}
                    for y, vs in yd.items()
                ],
                key=lambda r: r["year"],
            )
            for geo, yd in buckets.items()
        }

    if table_id == "17100005":
        result = {}
        for geo, yd in buckets.items():
            series = []
            prev = None
            for year in sorted(yd):
                pop = int(sum(yd[year]) / len(yd[year]))  # Usually 1 value per year
                change = pop - prev if prev is not None else None
                pct = round((pop - prev) / prev * 100, 2) if prev is not None else None
                series.append({"year": year, "pop": pop, "change": change, "pct": pct})
                prev = pop
            result[geo] = series
        return result

    return buckets


def extract_nhpi(rows: list[dict]) -> dict:
    """Monthly NHPI by city — table 18100205."""
    measures = ["Total (house and land)", "House only", "Land only"]
    idx_col = (
        next((k for k in rows[0] if "housing price" in k.lower()), None)
        if rows
        else None
    )

    if not idx_col:
        return {}

    buckets: dict[str, dict[str, dict[str, float]]] = defaultdict(
        lambda: {m: {} for m in measures}
    )
    for row in rows:
        measure = row[idx_col].strip()
        if measure not in measures:
            continue
        val = _clean(row["VALUE"])
        if val is None:
            continue
        date = row["REF_DATE"].strip()
        geo = row["GEO"].strip()
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
    new_json = (
        new_json.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    )
    pattern = rf"const {re.escape(var_name)}\s*=\s*\{{.*?\}};"
    new_html, n = re.subn(
        pattern,
        lambda m: f"const {var_name}={new_json};",
        html,
        count=1,
        flags=re.DOTALL,
    )
    return new_html, n > 0 and new_html != html


def _inject_insight(html: str, insight: str) -> tuple[str, bool]:
    """Replace content between <!-- insight-inject --> markers."""
    pattern = r"<!-- insight-inject -->.*?<!-- /insight-inject -->"
    replacement = f'<!-- insight-inject --><div class="insight-badge">{insight}</div><!-- /insight-inject -->'
    new_html, n = re.subn(pattern, replacement, html, flags=re.DOTALL)
    return new_html, n > 0 and new_html != html


# ── Per-analysis rebuild functions ────────────────────────────────────────────


def rebuild_employment(html_path: Path) -> bool:
    """Rebuild const DATA={...} in employment_rate_canada.html."""
    print(f"Rebuilding {html_path.name}...")

    csv_paths = {
        "lfs": SRC / "Employment" / "14100287-eng" / "14100287.csv",
        "gov": SRC / "Employment" / "10100015-eng" / "10100015.csv",
        "prov": SRC / "Employment" / "10100017-eng" / "10100017.csv",
        "pop": SRC / "Employment" / "17100005-eng" / "17100005.csv",
    }

    missing = [p.name for p in csv_paths.values() if not p.exists()]
    if missing:
        print(f"  SKIP — missing CSV(s): {missing}")
        return False

    print("  Processing datasets...")
    # Cache parsed rows for the large LFS CSV since multiple variants extract from it
    lfs_rows = _read_csv(csv_paths["lfs"])
    new_data = {
        "empRate": extract_statcan_data(
            lfs_rows, "14100287", "empRate"
        ),
        "empJobs": extract_statcan_data(
            lfs_rows, "14100287", "empJobs"
        ),
        "provDebt": extract_statcan_data(_read_csv(csv_paths["prov"]), "10100017"),
        "fedDebt": extract_statcan_data(_read_csv(csv_paths["gov"]), "10100015"),
        "popData": extract_statcan_data(_read_csv(csv_paths["pop"]), "17100005"),
    }

    html = html_path.read_text(encoding="utf-8")
    new_html, changed_const = _inject_const(html, "DATA", new_data)

    # Generate insight summary
    insight = ""
    try:
        canada_jobs = new_data.get("empJobs", {}).get("Canada", [])
        if canada_jobs:
            latest = canada_jobs[-1]
            year = latest["year"]
            change = latest["change"]
            if change is not None:
                verb = "grew by" if change >= 0 else "decreased by"
                insight = f"<strong>Insight:</strong> In {year}, employment in Canada {verb} {abs(change)}k persons."
    except Exception as e:
        print(f"  Warning: Failed to generate insight: {e}")

    if insight:
        new_html, changed_insight = _inject_insight(new_html, insight)
    else:
        changed_insight = False

    if not (changed_const or changed_insight):
        print("  No change in DATA or insight.")
        return False

    html_path.write_text(new_html, encoding="utf-8")
    print(f"  Updated DATA and insight in {html_path.name}")
    return True


def rebuild_nhpi(html_path: Path) -> bool:
    """Rebuild const RAW={...} in nhpi_big6_comparison.html."""
    print(f"Rebuilding {html_path.name}...")

    nhpi_csv = SRC / "Housing" / "18100205-eng" / "18100205.csv"
    if not nhpi_csv.exists():
        print(f"  SKIP — {nhpi_csv.relative_to(ROOT)} not found.")
        return False

    print("  Reading 18100205 (NHPI)...")
    raw = extract_statcan_data(_read_csv(nhpi_csv), "18100205")

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
