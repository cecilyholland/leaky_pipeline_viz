"""
IPEDS Completions Preprocessing — Act 1: The Pipeline
Project: Leaky Pipeline — Women in Tech Visualization
Course: CPSC 5530 Data Visualization and Exploration

Loads C_A completions files for 6 years (2010, 2013, 2016, 2019, 2022, 2024),
maps CIP codes to named computing/engineering tracks, and produces clean
analysis-ready dataframes for Plotly multi-line and choropleth visualizations.

Expected input files (place in same directory as this script):
    c2010_a.csv, c2013_a.csv, c2016_a.csv,
    c2019_a.csv, c2022_a.csv, c2024_a.csv

Key IPEDS columns (consistent across 2010-2024):
    UNITID    — institution identifier
    CIPCODE   — 6-digit CIP code as string e.g. "11.0701"
    AWLEVEL   — award level (3=Associate's, 5=Bachelor's, 7=Master's, 17=Doctorate)
    CTOTALT   — total completers (all genders, all races)
    CTOTALW   — total women completers
    CTOTALM   — total men completers
"""

import pandas as pd
import os

# ── Configuration ──────────────────────────────────────────────────────────────

DATA_DIR = ".\\ipeds datasets"

YEARS = {
    2010: "c2010_a.csv",
    2013: "c2013_a.csv",
    2016: "c2016_a.csv",
    2019: "c2019_a.csv",
    2022: "c2022_a.csv",
    2024: "c2024_a.csv",
}

AWARD_LEVELS = {
    3:  "Associate's",
    5:  "Bachelor's",
    7:  "Master's",
    17: "Doctorate",
}

# ── CIP track mapping ──────────────────────────────────────────────────────────
# Maps 4-digit CIP prefix to a human-readable track name.
# Based on actual data volumes from your ipeds_filtered_raw.csv exploration:
#   11.01  354,446  IT & General Computing       (largest, entry-level)
#   11.07  256,485  Computer Science             (core)
#   11.10  127,695  Cybersecurity                (fast-growing, low women %)
#   11.04   91,594  Information & Data Science
#   11.08   52,626  Software & Media Applications
#   11.09   47,785  Networking & Systems
#   11.02   33,176  Computer Programming
#   11.05+  <12k    Other Computing (grouped)
#   14.09           Computer Engineering
#   14.10           Electrical Engineering

CIP_TRACK_MAP = {
    # Computing tracks — CIP 11
    "11.07": "Computer Science",
    "11.10": "Cybersecurity",
    "11.04": "Information & Data Science",
    "11.01": "IT & General Computing",
    "11.08": "Software & Media Applications",
    "11.09": "Networking & Systems",
    "11.02": "Computer Programming",
    "11.05": "Other Computing",
    "11.03": "Other Computing",
    "11.06": "Other Computing",
    "11.99": "Other Computing",
    # Engineering tracks — CIP 14
    "14.09": "Computer Engineering",
    "14.10": "Electrical Engineering",
}

# CIP 2-digit families to include (pre-filter before track mapping)
CIP2_INCLUDE = {"11", "14"}

# Tracks shown in multi-line chart — excludes noise categories
TRACKS_FOR_CHART = {
    "Computer Science",
    "Cybersecurity",
    "Information & Data Science",
    "IT & General Computing",
    "Software & Media Applications",
    "Networking & Systems",
    "Computer Engineering",
    "Electrical Engineering",
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def cip4(cipcode):
    """Extract 4-char CIP prefix: '11.0701' → '11.07'"""
    parts = str(cipcode).strip().split(".")
    if len(parts) < 2:
        return parts[0].zfill(2)
    return parts[0].zfill(2) + "." + parts[1][:2]


def assign_track(cipcode):
    """Map a full CIP code string to a named track."""
    prefix = cip4(cipcode)
    if prefix in CIP_TRACK_MAP:
        return CIP_TRACK_MAP[prefix]
    if str(cipcode).startswith("14"):
        return "Engineering (Other)"
    return "Other Computing"


# ── Load & filter ──────────────────────────────────────────────────────────────

def load_year(year, filename):
    """Load one year's C_A file and return filtered, annotated rows."""
    path = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(path, dtype={"CIPCODE": str})
    df.columns = df.columns.str.upper()

    # Ensure required columns exist
    needed = ["UNITID", "CIPCODE", "AWLEVEL", "CTOTALT", "CTOTALW", "CTOTALM"]
    for col in needed:
        if col not in df.columns:
            print(f"  Warning {year}: column {col} missing — filling with 0")
            df[col] = 0
    df = df[needed].copy()

    # Force CIPCODE to clean string
    df["CIPCODE"] = df["CIPCODE"].astype(str).str.strip()

    # Extract 2-digit CIP family and filter to computing + engineering only
    df["CIP2"] = df["CIPCODE"].str.split(".").str[0].str.zfill(2)
    df = df[df["CIP2"].isin(CIP2_INCLUDE)].copy()

    # Filter to target award levels
    df = df[df["AWLEVEL"].isin(AWARD_LEVELS.keys())].copy()
    df["award_label"] = df["AWLEVEL"].map(AWARD_LEVELS)

    # Assign track names and 4-digit CIP prefix
    df["track"] = df["CIPCODE"].apply(assign_track)
    df["cip4"]  = df["CIPCODE"].apply(cip4)
    df["year"]  = year

    # Clean numerics
    for col in ["CTOTALT", "CTOTALW", "CTOTALM"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    print(f"  {year}: {len(df):,} rows after filtering")
    return df


# ── Main ───────────────────────────────────────────────────────────────────────

print("=" * 60)
print("Loading IPEDS C_A files...")
print("=" * 60)

frames = []
for year, fname in YEARS.items():
    try:
        frames.append(load_year(year, fname))
    except FileNotFoundError:
        print(f"  ERROR: {fname} not found in {DATA_DIR} — skipping")

df_raw = pd.concat(frames, ignore_index=True)
print(f"\nCombined raw rows: {len(df_raw):,}")

# ── National aggregation by track ──────────────────────────────────────────────

national = (
    df_raw.groupby(["year", "track", "cip4", "AWLEVEL", "award_label"])[
        ["CTOTALT", "CTOTALW", "CTOTALM"]
    ]
    .sum()
    .reset_index()
)

national["pct_women"] = (
    national["CTOTALW"]
    .div(national["CTOTALT"].replace(0, float("nan")))
    .mul(100)
    .round(1)
)

# ── Chart-ready: bachelor's only, named tracks ─────────────────────────────────

bachelors_by_track = national[
    (national["AWLEVEL"] == 5) &
    (national["track"].isin(TRACKS_FOR_CHART))
].copy().sort_values(["track", "year"])

print("\n── Bachelor's women % by track and year ──")
pivot = bachelors_by_track.pivot_table(
    index="track", columns="year", values="pct_women"
)
print(pivot.to_string())

# ── Degree ladder: CS + Cybersecurity across award levels ─────────────────────

cs_cyber_ladder = national[
    national["track"].isin(["Computer Science", "Cybersecurity"])
].copy().sort_values(["track", "award_label", "year"])

print("\n── CS & Cybersecurity — women % by award level (2024) ──")
ladder_2024 = cs_cyber_ladder[cs_cyber_ladder["year"] == 2024][
    ["track", "award_label", "CTOTALT", "CTOTALW", "pct_women"]
]
print(ladder_2024.to_string(index=False))

# ── State-level data for choropleth ───────────────────────────────────────────
# Requires HD2024.csv — download from IPEDS Complete Data Files,
# survey = "Institutional Characteristics", year = 2024, file = HD2024

def add_state(df_inst, hd_path):
    """Join institution state abbreviation from HD file."""
    hd = pd.read_csv(hd_path, dtype=str)
    hd.columns = hd.columns.str.upper()
    hd = hd[["UNITID", "STABBR"]].drop_duplicates()
    return df_inst.merge(hd, on="UNITID", how="left")

# Uncomment once you have HD2024.csv:
# df_with_state = add_state(df_raw, os.path.join(DATA_DIR, "hd2024.csv"))
# state_agg = (
#     df_with_state[
#         (df_with_state["track"].isin(TRACKS_FOR_CHART)) &
#         (df_with_state["AWLEVEL"] == 5)
#     ]
#     .groupby(["year", "STABBR", "track"])[["CTOTALT", "CTOTALW", "CTOTALM"]]
#     .sum()
#     .reset_index()
# )
# state_agg["pct_women"] = (
#     state_agg["CTOTALW"] / state_agg["CTOTALT"].replace(0, pd.NA) * 100
# ).round(1)
# state_agg.to_csv("ipeds_state_by_track.csv", index=False)
# print("  ipeds_state_by_track.csv      — state x track x year (choropleth)")

# ── Save outputs ───────────────────────────────────────────────────────────────

national.to_csv("ipeds_national_by_track.csv", index=False)
bachelors_by_track.to_csv("ipeds_bachelors_by_track.csv", index=False)
cs_cyber_ladder.to_csv("ipeds_cs_cyber_ladder.csv", index=False)
df_raw.to_csv("ipeds_filtered_raw.csv", index=False)

print("\n" + "=" * 60)
print("Saved outputs:")
print("  ipeds_national_by_track.csv    — all tracks, all award levels, national")
print("  ipeds_bachelors_by_track.csv   — bachelor's by track, chart-ready (primary)")
print("  ipeds_cs_cyber_ladder.csv      — CS + Cybersecurity across degree levels")
print("  ipeds_filtered_raw.csv         — institution-level rows (for choropleth)")
print("=" * 60)
print("\nNext step: download HD2024.csv (Institutional Characteristics)")
print("  → Same Complete Data Files page")
print("  → Survey = 'Institutional Characteristics', year = 2024, file = HD2024")
print("  → Drop in same folder, then uncomment the add_state() block above")