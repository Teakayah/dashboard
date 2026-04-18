import csv
import random
from pathlib import Path

ROOT = Path('source') / 'Stat Can' / 'Employment'
ROOT.mkdir(parents=True, exist_ok=True)

(ROOT / '14100287-eng').mkdir(parents=True, exist_ok=True)
with open(ROOT / '14100287-eng' / '14100287.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=['REF_DATE', 'GEO', 'Labour force characteristics', 'Gender', 'Age group', 'Statistics', 'Data type', 'VALUE'])
    writer.writeheader()
    for i in range(100000):
        writer.writerow({
            'REF_DATE': f'{2000 + (i % 20)}-01',
            'GEO': f'Prov {i % 10}',
            'Labour force characteristics': random.choice(['Employment rate', 'Employment', 'Unemployment rate']),
            'Gender': random.choice(['Total - Gender', 'Male', 'Female']),
            'Age group': random.choice(['15 years and over', '15 to 24 years', '25 to 54 years']),
            'Statistics': random.choice(['Estimate', 'Standard error']),
            'Data type': random.choice(['Seasonally adjusted', 'Unadjusted']),
            'VALUE': str(random.random() * 100)
        })

(ROOT / '10100015-eng').mkdir(parents=True, exist_ok=True)
with open(ROOT / '10100015-eng' / '10100015.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=['REF_DATE', 'GEO', 'Government sectors', 'Statement of government operations and balance sheet', 'VALUE'])
    writer.writeheader()
    for i in range(100000):
        writer.writerow({
            'REF_DATE': f'{2000 + (i % 20)}-01',
            'GEO': random.choice(['Canada', 'Prov']),
            'Government sectors': random.choice(['Federal government', 'Provincial']),
            'Statement of government operations and balance sheet': random.choice(['Liabilities', 'Assets']),
            'VALUE': str(random.random() * 1000000)
        })

(ROOT / '10100017-eng').mkdir(parents=True, exist_ok=True)
with open(ROOT / '10100017-eng' / '10100017.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=['REF_DATE', 'GEO', 'Public sector components', 'Display value', 'Statement of operations and balance sheet', 'VALUE'])
    writer.writeheader()
    for i in range(100000):
        writer.writerow({
            'REF_DATE': str(2000 + (i % 20)),
            'GEO': f'Prov {i % 10}',
            'Public sector components': random.choice(['Provincial and territorial governments', 'Other']),
            'Display value': random.choice(['Stocks', 'Flows']),
            'Statement of operations and balance sheet': random.choice(['Liabilities [63]', 'Assets']),
            'VALUE': str(random.random() * 1000000)
        })

(ROOT / '17100005-eng').mkdir(parents=True, exist_ok=True)
with open(ROOT / '17100005-eng' / '17100005.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=['REF_DATE', 'GEO', 'Gender', 'Age group', 'VALUE'])
    writer.writeheader()
    for i in range(100000):
        writer.writerow({
            'REF_DATE': str(2000 + (i % 20)),
            'GEO': f'Prov {i % 10}',
            'Gender': random.choice(['Total - gender', 'Male', 'Female']),
            'Age group': random.choice(['All ages', '0 to 14 years']),
            'VALUE': str(random.randint(100000, 10000000))
        })
