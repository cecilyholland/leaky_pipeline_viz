"""
BLS CPS Preprocessing — Act 2: The Workforce
Project: Leaky Pipeline — Women in Tech Visualization
Course: CPSC 5530 Data Visualization and Exploration

Extracts tech occupation data from BLS CPS annual average files:
  - cpsaat11  → occupation × sex (% women by tech role)
  - cpsaat11b → occupation × age bracket (headcount for age-35 attrition story)

Expected input files (place in DATA_DIR):
    cpsa2015.xlsx, cpsa2016.xlsx, cpsa2017.xlsx, cpsa2018.xlsx,
    cpsa2019.xlsx, cpsa2020.xlsx, cpsa2021.xlsx, cpsa2022.xlsx,
    cpsa2023.xlsx, cpsa2024.xlsx

Outputs:
    bls_tech_by_sex.csv      — % women by occupation and year (Act 2 line chart)
    bls_tech_by_age.csv      — headcount by age bracket and year (age-35 story)
    bls_combined_clean.csv   — merged view for linked visualizations
"""

import pandas as pd
import os
import re

# ── Configuration ──────────────────────────────────────────────────────────────

DATA_DIR = "bls_datasets"
OUTPUT_DIR = "processed_bls_data"

import pathlib
pathlib.Path(OUTPUT_DIR).mkdir(exist_ok=True)

YEARS = {
    2015: "cpsa2015.xlsx",
    2016: "cpsa2016.xlsx",
    2017: "cpsa2017.xlsx",
    2018: "cpsa2018.xlsx",
    2019: "cpsa2019.xlsx",
    2020: "cpsa2020.xlsx",
    2021: "cpsa2021.xlsx",
    2022: "cpsa2022.xlsx",
    2023: "cpsa2023.xlsx",
    2024: "cpsa2024.xlsx",
}

# Tech occupations to track — matched against row labels in cpsaat11
# Keys are short labels used in charts, values are regex patterns to match
TECH_OCCUPATIONS = {
    "CS & Math (all)"              : r"computer and mathematical",
    "CS Managers"                  : r"computer and information systems managers",
    "Software Developers"          : r"software developers",
    "Information Security Analysts": r"information security analysts",
    "Computer Systems Analysts"    : r"computer systems analysts",
    "Computer Programmers"         : r"computer programmers",
    "Database Administrators"      : r"database administrators",
    "Network & Systems Admins"     : r"network and computer systems administrators",
    "Computer Network Architects"  : r"computer network architects",
    "Computer Support Specialists" : r"computer support specialists",
    "Computer Hardware Engineers"  : r"computer hardware engineers",
}

# Age bracket columns in cpsaat11b (after the occupation name column)
# Structure: col0=occupation, col1=total, col2=16-19, col3=20-24,
#            col4=25-34, col5=35-44, col6=45-54, col7=55-64, col8=65+
AGE_BRACKET_COLS = {
    1: "total",
    2: "age_16_19",
    3: "age_20_24",
    4: "age_25_34",
    5: "age_35_44",
    6: "age_45_54",
    7: "age_55_64",
    8: "age_65_plus",
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def clean_value(val):
    """Convert BLS cell values to float. Returns None for suppressed (–) values."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s in ("–", "-", "–", ""):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def match_occupation(label, patterns):
    """Return the short label for the first pattern that matches, or None."""
    label_lower = str(label).lower().strip()
    for short_label, pattern in patterns.items():
        if re.search(pattern, label_lower):
            return short_label
    return None


# ── Table 11 parser: occupation × sex ─────────────────────────────────────────

def parse_table11(path, year):
    """
    Extract % women for each target tech occupation from cpsaat11.
    Returns a list of dicts: {year, occupation, total_employed_k, pct_women}
    """
    df = pd.read_excel(path, sheet_name="cpsaat11", header=None)
    rows = []

    for _, row in df.iterrows():
        label = str(row[0]) if not pd.isna(row[0]) else ""
        short = match_occupation(label, TECH_OCCUPATIONS)
        if short is None:
            continue

        total = clean_value(row[1])   # total employed (thousands)
        pct_w = clean_value(row[2])   # % women

        rows.append({
            "year"              : year,
            "occupation"        : short,
            "occupation_full"   : label.strip(),
            "total_employed_k"  : total,
            "pct_women"         : pct_w,
            "pct_men"           : round(100 - pct_w, 1) if pct_w is not None else None,
        })

    print(f"  {year} Table 11: {len(rows)} tech occupation rows found")
    return rows


# ── Table 11b parser: occupation × age ────────────────────────────────────────

def parse_table11b(path, year):
    """
    Extract age-bracket headcounts for each target tech occupation from cpsaat11b.
    Returns a list of dicts: {year, occupation, age_bracket, count_k}
    """
    df = pd.read_excel(path, sheet_name="cpsaat11b", header=None)

    # Detect actual age bracket columns dynamically from header rows
    # Default to AGE_BRACKET_COLS mapping, override if file has different layout
    rows = []

    for _, row in df.iterrows():
        label = str(row[0]) if not pd.isna(row[0]) else ""
        short = match_occupation(label, TECH_OCCUPATIONS)
        if short is None:
            continue

        for col_idx, age_label in AGE_BRACKET_COLS.items():
            val = clean_value(row[col_idx]) if col_idx < len(row) else None
            rows.append({
                "year"       : year,
                "occupation" : short,
                "age_bracket": age_label,
                "count_k"    : val,
            })

    occ_count = len(set(r["occupation"] for r in rows))
    print(f"  {year} Table 11b: {occ_count} tech occupations × {len(AGE_BRACKET_COLS)} age brackets")
    return rows


# ── Main ───────────────────────────────────────────────────────────────────────

print("=" * 60)
print("Processing BLS CPS annual average files...")
print("=" * 60)

sex_rows = []
age_rows = []

for year, fname in YEARS.items():
    path = os.path.join(DATA_DIR, fname)
    if not os.path.exists(path):
        print(f"  MISSING: {fname} — skipping")
        continue
    print(f"\n{year}:")
    try:
        sex_rows.extend(parse_table11(path, year))
    except Exception as e:
        print(f"  ERROR Table 11: {e}")
    try:
        age_rows.extend(parse_table11b(path, year))
    except Exception as e:
        print(f"  ERROR Table 11b: {e}")

# ── Build dataframes ───────────────────────────────────────────────────────────

df_sex = pd.DataFrame(sex_rows).sort_values(["occupation", "year"]).reset_index(drop=True)
df_age = pd.DataFrame(age_rows).sort_values(["occupation", "year", "age_bracket"]).reset_index(drop=True)

# ── Sanity check printouts ─────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("── Women % by occupation and year (pivot) ──")
pivot_sex = df_sex.pivot_table(index="occupation", columns="year", values="pct_women")
print(pivot_sex.to_string())

print("\n── Software Developers — age distribution 2024 ──")
sw_2024 = df_age[
    (df_age["occupation"] == "Software Developers") &
    (df_age["year"] == max(df_age["year"])) &
    (df_age["age_bracket"] != "total")
][["age_bracket", "count_k"]]
print(sw_2024.to_string(index=False))

print("\n── Information Security Analysts — women % trend ──")
sec = df_sex[df_sex["occupation"] == "Information Security Analysts"][["year", "pct_women", "total_employed_k"]]
print(sec.to_string(index=False))

# ── Merged view for linked visualizations ─────────────────────────────────────
# Join sex % onto age data so we can compute approximate women count by age
# (BLS doesn't publish women × age × occupation directly, so we use total × pct_women
#  as an approximation at the occupation level)

df_combined = df_age.merge(
    df_sex[["year", "occupation", "pct_women", "total_employed_k"]],
    on=["year", "occupation"],
    how="left"
)
# Approximate women in each age bracket:
# women_in_bracket ≈ count_k × (pct_women / 100)
# NOTE: this is an approximation — BLS doesn't publish age × sex × occupation
df_combined["women_count_k_approx"] = (
    df_combined["count_k"] * (df_combined["pct_women"] / 100)
).round(1)
df_combined["data_note"] = "women_count estimated from occupation-level pct_women × age_bracket_total"

# ── Save outputs ───────────────────────────────────────────────────────────────

df_sex.to_csv(os.path.join(OUTPUT_DIR, "bls_tech_by_sex.csv"), index=False)
df_age.to_csv(os.path.join(OUTPUT_DIR, "bls_tech_by_age.csv"), index=False)
df_combined.to_csv(os.path.join(OUTPUT_DIR, "bls_combined_clean.csv"), index=False)

print("\n" + "=" * 60)
print("Saved:")
print(f"  {OUTPUT_DIR}/bls_tech_by_sex.csv      — % women by occupation × year (Act 2 primary)")
print(f"  {OUTPUT_DIR}/bls_tech_by_age.csv      — headcount by age bracket × occupation × year")
print(f"  {OUTPUT_DIR}/bls_combined_clean.csv   — merged view with estimated women by age bracket")
print("\nIMPORTANT NOTE on bls_combined_clean.csv:")
print("  women_count_k_approx = total_in_bracket × pct_women (occupation-level)")
print("  This is an approximation. BLS does not publish age × sex × occupation.")
print("  Flag this in your report's data limitations section.")
print("=" * 60)