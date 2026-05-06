import time
import random
from collections import defaultdict

def create_dummy_rows():
    genders = ["Total - Gender"] * 5 + ["Male"] * 2 + ["Female"] * 2
    age_groups = ["15 years and over"] * 5 + [f"Age {i}" for i in range(15)]
    characteristics = ["Employment rate", "Employment", "Unemployment rate", "Population"] + [f"Char {i}" for i in range(50)]
    data_types = ["Seasonally adjusted", "Unadjusted"]
    statistics = ["Estimate", "Standard error", "Variance"]

    rows = []
    for _ in range(300000):
        rows.append({
            "Gender": random.choice(genders),
            "Age group": random.choice(age_groups),
            "Labour force characteristics": random.choice(characteristics),
            "Data type": random.choice(data_types),
            "Statistics": random.choice(statistics),
            "VALUE": "1.0",
            "REF_DATE": "2020-01",
            "GEO": "Canada"
        })
    return rows

rows = create_dummy_rows()

def orig_order(rows):
    count = 0
    for row in rows:
        if (
            row["Labour force characteristics"] == "Employment rate"
            and row["Gender"] == "Total - Gender"
            and row["Age group"] == "15 years and over"
            and row["Statistics"] == "Estimate"
            and row["Data type"] == "Seasonally adjusted"
        ):
            count += 1
    return count

def opt_shortcircuit(rows):
    count = 0
    for row in rows:
        if row["Labour force characteristics"] != "Employment rate": continue
        if row["Gender"] != "Total - Gender": continue
        if row["Age group"] != "15 years and over": continue
        if row["Statistics"] != "Estimate": continue
        if row["Data type"] != "Seasonally adjusted": continue
        count += 1
    return count

def opt_var_extract(rows):
    count = 0
    for row in rows:
        lfc = row["Labour force characteristics"]
        if lfc != "Employment rate": continue
        if row["Gender"] != "Total - Gender": continue
        if row["Age group"] != "15 years and over": continue
        if row["Statistics"] != "Estimate": continue
        if row["Data type"] != "Seasonally adjusted": continue
        count += 1
    return count

start = time.time()
for _ in range(10): orig_order(rows)
print("Original order (LFC first):", time.time() - start)

start = time.time()
for _ in range(10): opt_shortcircuit(rows)
print("Shortcircuit (LFC first):", time.time() - start)

start = time.time()
for _ in range(10): opt_var_extract(rows)
print("Var Extract (LFC first):", time.time() - start)
