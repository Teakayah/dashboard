import time
import random
import csv
from collections import defaultdict
from pathlib import Path

# Let's see if we can create a more real-ish benchmark
# Real stats can data has ~100k rows.
# Employment rate is a tiny fraction.
# Let's test the current "Gender" first approach.

def _clean(val: str) -> float | None:
    if val in ("", "..", "F", "x", "E", "r", "p"):
        return None
    try:
        return float(val)
    except ValueError:
        return None

# We can mock a reader function that creates data
def create_dummy_rows():
    genders = ["Total - Gender"] * 5 + ["Male"] * 2 + ["Female"] * 2 # Bias towards total
    age_groups = ["15 years and over"] * 5 + [f"Age {i}" for i in range(15)]
    # LFC has MANY options. Empl and Empl Rate are just 2 out of ~50 in real tables
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

def agent_order(rows):
    count = 0
    for row in rows:
        if (
            row["Gender"] == "Total - Gender"
            and row["Age group"] == "15 years and over"
            and row["Labour force characteristics"] == "Employment rate"
            and row["Data type"] == "Seasonally adjusted"
            and row["Statistics"] == "Estimate"
        ):
            count += 1
    return count

start = time.time()
for _ in range(10): orig_order(rows)
print("Original order (LFC first):", time.time() - start)

start = time.time()
for _ in range(10): agent_order(rows)
print("Agent order (Gender first):", time.time() - start)
