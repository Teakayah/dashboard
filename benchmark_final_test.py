import time
import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path('source') / 'Stat Can' / 'Employment'
lfs_csv = ROOT / '14100287-eng' / '14100287.csv'
gov_csv = ROOT / '10100015-eng' / '10100015.csv'
prov_csv = ROOT / '10100017-eng' / '10100017.csv'
pop_csv = ROOT / '17100005-eng' / '17100005.csv'

def _clean(val: str) -> float | None:
    v = val.strip()
    if v in ('', '..', 'F', 'x', 'E', 'r', 'p'):
        return None
    try:
        return float(v)
    except ValueError:
        return None

def _read_csv_orig(path):
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def _read_csv_stripped(path: Path) -> list[dict]:
    with open(path, encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        try:
            headers = [h.strip() for h in next(reader)]
        except StopIteration:
            return []
        return [dict(zip(headers, (v.strip() for v in row))) for row in reader]

def extract_emp_rate_reordered(rows):
    buckets = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if (row['Gender'].strip() == 'Total - Gender'
                and row['Age group'].strip() == '15 years and over'
                and row['Labour force characteristics'].strip() == 'Employment rate'
                and row['Data type'].strip() == 'Seasonally adjusted'
                and row['Statistics'].strip() == 'Estimate'):
            val = _clean(row['VALUE'])
            if val is not None:
                year = int(row['REF_DATE'][:4])
                buckets[row['GEO'].strip()][year].append(val)
    return buckets

def extract_emp_rate_opt(rows):
    buckets = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if (row['Gender'] == 'Total - Gender'
                and row['Age group'] == '15 years and over'
                and row['Labour force characteristics'] == 'Employment rate'
                and row['Data type'] == 'Seasonally adjusted'
                and row['Statistics'] == 'Estimate'):
            val = _clean(row['VALUE'])
            if val is not None:
                year = int(row['REF_DATE'][:4])
                buckets[row['GEO']][year].append(val)
    return buckets

start = time.time()
for _ in range(10):
    rows = _read_csv_orig(lfs_csv)
    extract_emp_rate_reordered(rows)
print("Orig Read + Reordered Loop:", time.time() - start)

start = time.time()
for _ in range(10):
    rows = _read_csv_stripped(lfs_csv)
    extract_emp_rate_opt(rows)
print("Stripped Read + Opt Loop:", time.time() - start)
