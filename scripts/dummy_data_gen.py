import csv
import random
from pathlib import Path

ROOT = Path('source') / 'Stat Can' / 'Employment'
ROOT.mkdir(parents=True, exist_ok=True)

(ROOT / '14100287-eng').mkdir(parents=True, exist_ok=True)
with open(ROOT / '14100287-eng' / '14100287.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=['REF_DATE', 'GEO', 'Labour force characteristics', 'Gender', 'Age group', 'Statistics', 'Data type', 'VALUE'])
    writer.writeheader()
    # Performance optimization: extract lists outside loop to avoid re-allocating on every iteration
    labour_force_choices = ['Employment rate', 'Employment', 'Unemployment rate']
    gender_choices_1 = ['Total - Gender', 'Male', 'Female']
    age_group_choices_1 = ['15 years and over', '15 to 24 years', '25 to 54 years']
    statistics_choices = ['Estimate', 'Standard error']
    data_type_choices = ['Seasonally adjusted', 'Unadjusted']
    for i in range(100000):
        writer.writerow({
            'REF_DATE': f'{2000 + (i % 20)}-01',
            'GEO': f'Prov {i % 10}',
            'Labour force characteristics': random.choice(labour_force_choices),
            'Gender': random.choice(gender_choices_1),
            'Age group': random.choice(age_group_choices_1),
            'Statistics': random.choice(statistics_choices),
            'Data type': random.choice(data_type_choices),
            'VALUE': str(random.random() * 100)
        })

(ROOT / '10100015-eng').mkdir(parents=True, exist_ok=True)
with open(ROOT / '10100015-eng' / '10100015.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=['REF_DATE', 'GEO', 'Government sectors', 'Statement of government operations and balance sheet', 'VALUE'])
    writer.writeheader()
    # Performance optimization: extract lists outside loop to avoid re-allocating on every iteration
    geo_choices = ['Canada', 'Prov']
    gov_sector_choices = ['Federal government', 'Provincial']
    gov_ops_choices = ['Liabilities', 'Assets']
    for i in range(100000):
        writer.writerow({
            'REF_DATE': f'{2000 + (i % 20)}-01',
            'GEO': random.choice(geo_choices),
            'Government sectors': random.choice(gov_sector_choices),
            'Statement of government operations and balance sheet': random.choice(gov_ops_choices),
            'VALUE': str(random.random() * 1000000)
        })

(ROOT / '10100017-eng').mkdir(parents=True, exist_ok=True)
with open(ROOT / '10100017-eng' / '10100017.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=['REF_DATE', 'GEO', 'Public sector components', 'Display value', 'Statement of operations and balance sheet', 'VALUE'])
    writer.writeheader()
    # Performance optimization: extract lists outside loop to avoid re-allocating on every iteration
    public_sector_choices = ['Provincial and territorial governments', 'Other']
    display_value_choices = ['Stocks', 'Flows']
    ops_balance_choices = ['Liabilities [63]', 'Assets']
    for i in range(100000):
        writer.writerow({
            'REF_DATE': str(2000 + (i % 20)),
            'GEO': f'Prov {i % 10}',
            'Public sector components': random.choice(public_sector_choices),
            'Display value': random.choice(display_value_choices),
            'Statement of operations and balance sheet': random.choice(ops_balance_choices),
            'VALUE': str(random.random() * 1000000)
        })

(ROOT / '17100005-eng').mkdir(parents=True, exist_ok=True)
with open(ROOT / '17100005-eng' / '17100005.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=['REF_DATE', 'GEO', 'Gender', 'Age group', 'VALUE'])
    writer.writeheader()
    # Performance optimization: extract lists outside loop to avoid re-allocating on every iteration
    gender_choices_2 = ['Total - gender', 'Male', 'Female']
    age_group_choices_2 = ['All ages', '0 to 14 years']
    for i in range(100000):
        writer.writerow({
            'REF_DATE': str(2000 + (i % 20)),
            'GEO': f'Prov {i % 10}',
            'Gender': random.choice(gender_choices_2),
            'Age group': random.choice(age_group_choices_2),
            'VALUE': str(random.randint(100000, 10000000))
        })
