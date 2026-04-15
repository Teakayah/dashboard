#!/usr/bin/env python3
"""
Download latest Stats Canada bulk CSV tables — only when new data exists.

Two-phase approach:
  1. Check  — call the lightweight Stats Canada "changed cubes" API to get the
              list of table IDs published since the last run. No data transfer.
  2. Download — only fetch the ZIP for tables that appear in that list.

On the very first run (no status file) every table is downloaded.
If the API call fails, the script falls back to downloading everything.

Writes source/.update_result.json with the outcome.
Exit code: 0 = nothing new, 1 = one or more tables updated.
"""

import csv
import json
import sys
import urllib.request
import zipfile
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).parent.parent
SOURCE_DIR = ROOT / 'source' / 'Stat Can'
STATUS_FILE = ROOT / 'source' / '.update_result.json'

# Lightweight metadata API — returns JSON list of changed table IDs, no CSV data
_CHANGED_URL = 'https://www150.statcan.gc.ca/t1/tbl1/en/dtbl/getChangedCubeList/{date}'

# Full-table bulk CSV download (ZIP)
_DL_URL = 'https://www150.statcan.gc.ca/t1/tbl1/en/dtbl/downloadTbl/{pid}01'

# Fall back to downloading everything if last check is older than this many days
_MAX_LOOKBACK_DAYS = 60

TABLES = [
    {
        'id': '10100015',
        'path': SOURCE_DIR / 'Employment' / '10100015-eng',
        'desc': 'Government operations & balance sheet (quarterly)',
    },
    {
        'id': '10100017',
        'path': SOURCE_DIR / 'Employment' / '10100017-eng',
        'desc': 'Public sector operations (annual)',
    },
    {
        'id': '14100287',
        'path': SOURCE_DIR / 'Employment' / '14100287-eng',
        'desc': 'Labour force survey (monthly)',
    },
    {
        'id': '17100005',
        'path': SOURCE_DIR / 'Employment' / '17100005-eng',
        'desc': 'Population estimates (annual)',
    },
    {
        'id': '18100205',
        'path': SOURCE_DIR / 'Housing' / '18100205-eng',
        'desc': 'New housing price index (monthly)',
    },
]

# Quick lookup: our 8-digit IDs as a set for O(1) membership tests
_OUR_IDS = {t['id'] for t in TABLES}


# ── Phase 1: check ─────────────────────────────────────────────────────────────

def _load_last_checked() -> date | None:
    """Return the date of the last successful check, or None on first run."""
    if not STATUS_FILE.exists():
        return None
    try:
        status = json.loads(STATUS_FILE.read_text())
        raw = status.get('last_checked_date')
        if raw:
            return date.fromisoformat(raw)
    except Exception:
        pass
    return None


def _normalize_pid(raw: str | int) -> str:
    """Stats Canada API returns 10-digit PIDs (8-digit + '01'). Strip to 8."""
    s = str(raw).strip()
    if len(s) == 10 and s.endswith('01'):
        return s[:8]
    return s


def fetch_changed_since(since: date) -> set[str] | None:
    """
    Call getChangedCubeList and return the set of 8-digit table IDs that changed
    since `since`. Returns None if the API call fails (caller should fall back).
    """
    url = _CHANGED_URL.format(date=since.isoformat())
    print(f'  Checking Stats Canada for tables changed since {since} ...')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'DataDashboard/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read())
    except Exception as exc:
        print(f'  WARNING: changed-cubes API call failed ({exc}) — will download all.')
        return None

    changed = {_normalize_pid(item.get('productId', '')) for item in payload}
    relevant = changed & _OUR_IDS
    print(f'  Stats Canada reports {len(changed)} table(s) changed; '
          f'{len(relevant)} of ours: {sorted(relevant) or "none"}')
    return relevant


# ── Phase 2: download ──────────────────────────────────────────────────────────

def _get_end_period(metadata_path: Path) -> str | None:
    """Read 'End Reference Period' from a Stats Canada metadata CSV."""
    if not metadata_path.exists():
        return None
    try:
        with open(metadata_path, encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            row = next(reader, None)
            if row and 'End Reference Period' in row:
                return row['End Reference Period'].strip()
    except Exception:
        pass
    return None


def download_table(table: dict) -> dict:
    """Download a Stats Canada table ZIP and extract it. Returns a status dict."""
    pid = table['id']
    dest_dir: Path = table['path']
    meta_path = dest_dir / f'{pid}_MetaData.csv'
    prev_end = _get_end_period(meta_path)

    url = _DL_URL.format(pid=pid)
    print(f'  [{pid}] {table["desc"]}')
    print(f'         Downloading ...')

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'DataDashboard/1.0'})
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = resp.read()
    except Exception as exc:
        print(f'         ERROR: {exc}')
        return {'id': pid, 'desc': table['desc'], 'error': str(exc),
                'updated': False, 'prev_end': prev_end, 'new_end': None}

    dest_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(BytesIO(data)) as zf:
            zf.extractall(dest_dir)
    except zipfile.BadZipFile as exc:
        print(f'         ERROR extracting ZIP: {exc}')
        return {'id': pid, 'desc': table['desc'], 'error': str(exc),
                'updated': False, 'prev_end': prev_end, 'new_end': None}

    new_end = _get_end_period(meta_path)
    updated = new_end != prev_end

    if updated:
        print(f'         Updated: {prev_end} → {new_end}')
    else:
        print(f'         No change (end period: {new_end})')

    return {'id': pid, 'desc': table['desc'], 'prev_end': prev_end,
            'new_end': new_end, 'updated': updated}


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    today = date.today()
    now = datetime.now(timezone.utc)

    print('Stats Canada update check\n')

    # ── Phase 1: should we download anything? ─────────────────────────────────
    last_checked = _load_last_checked()

    if last_checked is None:
        print('  First run — downloading all tables.\n')
        tables_to_download = TABLES

    elif (today - last_checked).days > _MAX_LOOKBACK_DAYS:
        print(f'  Last check was {(today - last_checked).days} days ago '
              f'(>{_MAX_LOOKBACK_DAYS}). Downloading all tables to be safe.\n')
        tables_to_download = TABLES

    else:
        changed_ids = fetch_changed_since(last_checked)

        if changed_ids is None:
            # API failure — fall back to downloading everything
            tables_to_download = TABLES

        elif not changed_ids:
            print('\n  No updates for our tables. Nothing to download.')
            _write_status(now, today, any_updated=False, tables=[
                {'id': t['id'], 'desc': t['desc'], 'updated': False,
                 'reason': 'not_in_changed_list'}
                for t in TABLES
            ])
            return 0

        else:
            tables_to_download = [t for t in TABLES if t['id'] in changed_ids]
            skipped = [t for t in TABLES if t['id'] not in changed_ids]
            if skipped:
                print(f'  Skipping unchanged: {[t["id"] for t in skipped]}\n')

    # ── Phase 2: download the tables that changed ─────────────────────────────
    print(f'Downloading {len(tables_to_download)} table(s)...\n')
    downloaded = [download_table(t) for t in tables_to_download]

    # Merge in skipped tables (marked not updated)
    downloaded_ids = {r['id'] for r in downloaded}
    skipped_results = [
        {'id': t['id'], 'desc': t['desc'], 'updated': False, 'reason': 'not_in_changed_list'}
        for t in TABLES if t['id'] not in downloaded_ids
    ]
    all_results = downloaded + skipped_results

    any_updated = any(r.get('updated') for r in downloaded)
    errors = [r for r in downloaded if 'error' in r]

    _write_status(now, today, any_updated=any_updated, tables=all_results)

    if errors:
        print(f'\n  Errors ({len(errors)}): {[e["id"] for e in errors]}')
    print(f'\n  Any data updated: {any_updated}')

    return 1 if any_updated else 0


def _write_status(now: datetime, today: date, any_updated: bool, tables: list[dict]) -> None:
    status = {
        'timestamp': now.isoformat(),
        'last_checked_date': today.isoformat(),
        'any_updated': any_updated,
        'tables': tables,
    }
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(status, indent=2))
    print(f'\n  Status written → {STATUS_FILE.relative_to(ROOT)}')


if __name__ == '__main__':
    sys.exit(main())
