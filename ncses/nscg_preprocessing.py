"""
nscg_preprocessing.py
National Survey of College Graduates (NSCG)
NSF NCSES Public Use Files — Act 3: The Data Gap

IMPORTANT — NSCG data structure:
  Unit of observation: INDIVIDUAL survey respondent (person-level microdata)
  Each row = one college graduate
  Key variables: occupation, field of bachelor's degree, sex, age, race/ethnicity

This is what the WMPD 2023 report's employment tables are built from.
It gives us the age cliff directly from microdata — much richer than BLS CPS.

Put all College_Grads_YYYY.zip files in /ncses_datasets/
Script will unzip, find the CSV/Stata file, and process across years.

Run from repo root:
  conda activate plda2
  python nscg_preprocessing.py

NOTE ON VARIABLE NAMES:
  The NSCG variable names differ by year. This script handles both the
  current (2017+) naming and the prior-years naming using the codebook mappings.
  After first run, check nscg_variable_audit.txt to confirm column names.
"""

import os
import zipfile
import glob
import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR  = Path("ncses/ncses_datasets")
GSS_DIR  = RAW_DIR / "gss"    # Graduate Students Survey CSVs
NSCG_DIR = RAW_DIR / "nscg"   # National Survey of College Graduates (epcg19, epcg23)
SDR_DIR  = RAW_DIR / "sdr"    # Survey of Doctorate Recipients
OUT_DIR  = Path("ncses/processed_nscg_data")
OUT_DIR.mkdir(exist_ok=True)

# ── Variable name candidates (NSCG uses different names across years) ─────────
# We try each alias in order and use the first one found
VAR_ALIASES = {
    # Confirmed from epcg19.csv — consistent across 2019, 2021, 2023
    "sex":        ["SEX", "SEX_2023", "GENDER", "sex", "gender"],
    "age":        ["AGE", "age"],
    "age_group":  ["AGEGR", "agegr"],        # 5-year groups: 20,25,30,35...
    "occupation": ["N2OCPRMG", "NOCPRMG"],   # occupation major group (1=computing)
    "occ_detail": ["N2OCBLST", "NOCPR"],     # detailed occupation
    "field_ba":   ["NBAMEMG", "nbamemg"],    # BA field major group (1=CS/math)
    "field_hd":   ["NDGMEMG", "ndgmemg"],   # highest degree field
    "race_eth":   ["RACETHM", "racethm"],    # 1=Hispanic,2=AmInd,3=Asian,
                                              # 4=Black,5=White,6=NatHaw,7=Multi
    "weight":     ["WTSURVY", "wtsurvy"],
    "salary":     ["SALARY", "salary"],
    "empl_stat":  ["LFSTAT", "lfstat"],      # 1=employed
    "sector":     ["EMSECDT", "emsecdt"],
    "work_act":   ["WAPRI", "wapri"],        # primary work activity
}

# N2OCPRMG codes confirmed from epcg19.csv (2019–2023 consistent):
#   1 = Computer & mathematical scientists  (27.1% women) ← PRIMARY
#   2 = Biological/life scientists          (48.5% women)
#   3 = Physical scientists                 (34.5% women)
#   4 = Social scientists                   (59.9% women)
#   5 = Engineers                           (16.5% women)
#   6 = S&E-related occupations             (53.1% women)
#   7 = Non-S&E occupations                 (52.6% women)
#   8 = Non-S&E occupations (mgmt/other)    (52.6% women)
COMPUTING_OCC_CODES = {"1", 1}  # N2OCPRMG == 1

ALL_OCC_LABELS = {
    1: "Computer & math scientists",
    2: "Biological/life scientists",
    3: "Physical scientists",
    4: "Social scientists",
    5: "Engineers",
    6: "S&E-related",
    7: "Non-S&E",
    8: "Non-S&E (mgmt/other)",
}

# NBAMEMG codes (BA field) confirmed from epcg19.csv:
#   1 = Computer science & math  ← PRIMARY
#   2 = Biological sciences
#   3 = Physical sciences
#   4 = Social sciences
#   5 = Engineering
#   6 = S&E-related
#   7 = Non-S&E
#   8 = Unknown
COMPUTING_FIELD_CODES = {"1", 1}

# RACETHM codes confirmed from epcg19.csv:
RACE_LABELS = {
    "1": "Hispanic", "2": "Am. Indian/AK Native", "3": "Asian",
    "4": "Black", "5": "White", "6": "Native Hawaiian/Pac. Isl.", "7": "Multiracial",
    1: "Hispanic", 2: "Am. Indian/AK Native", 3: "Asian",
    4: "Black", 5: "White", 6: "Native Hawaiian/Pac. Isl.", 7: "Multiracial",
}

# Sex codes (confirmed: M/F strings in 2019+)
SEX_FEMALE = {"F", "f", "2", 2}
SEX_MALE   = {"M", "m", "1", 1}

# Age group bins matching AGEGR values (5-yr groups starting at 20,25,30...)
AGE_GROUP_LABELS = {
    20: "Under 25", 25: "25-34", 30: "25-34",
    35: "35-44", 40: "35-44",
    45: "45-54", 50: "45-54",
    55: "55-64", 60: "55-64",
    65: "65+", 70: "65+",
}


def find_col(df: pd.DataFrame, varname: str) -> str | None:
    """Find the actual column name for a logical variable."""
    aliases = VAR_ALIASES.get(varname, [varname])
    for alias in aliases:
        if alias in df.columns:
            return alias
        # case-insensitive
        matches = [c for c in df.columns if c.upper() == alias.upper()]
        if matches:
            return matches[0]
    return None


def unzip_nscg_files():
    zips = list(RAW_DIR.glob("College_Grads_*.zip")) + \
           list(RAW_DIR.glob("college_grads_*.zip"))
    if not zips:
        print(f"WARNING: No NSCG zip files found in {RAW_DIR}/")
        print("  Download from: https://ncsesdata.nsf.gov/datadownload/")
        return []
    extracted = []
    for z in sorted(zips):
        year_str = z.stem.split("_")[-1]
        dest = RAW_DIR / year_str
        dest.mkdir(exist_ok=True)
        if not any(dest.iterdir()):
            print(f"  Unzipping {z.name} -> {dest}/")
            with zipfile.ZipFile(z, "r") as zf:
                zf.extractall(dest)
        extracted.append((year_str, dest))
    return extracted


def find_data_file(directory: Path) -> Path | None:
    for pattern in ["*.csv", "*.CSV", "*.dta", "*.sas7bdat"]:
        matches = list(directory.rglob(pattern))
        data_files = [f for f in matches if not any(
            x in f.name.lower() for x in
            ["codebook", "appendix", "readme", "guide", "doc", "layout", "format"]
        )]
        if data_files:
            return max(data_files, key=lambda f: f.stat().st_size)
    return None


def load_nscg_file(filepath: Path, year: str) -> pd.DataFrame | None:
    """Load NSCG file, reading only the columns we need."""
    suffix = filepath.suffix.lower()
    size_mb = filepath.stat().st_size // 1024 // 1024
    print(f"    Loading {filepath.name} ({size_mb} MB)...")

    try:
        if suffix == ".csv":
            # Peek at header
            header_df = pd.read_csv(filepath, nrows=0)
            all_cols = list(header_df.columns)

            # Find which columns we actually want
            wanted = []
            found_map = {}
            for varname in VAR_ALIASES:
                col = find_col(header_df, varname)
                if col:
                    wanted.append(col)
                    found_map[varname] = col

            print(f"    Variable mapping: {found_map}")

            if not wanted:
                print("    WARNING: Could not identify any key variables!")
                print(f"    Available columns: {all_cols[:20]}")
                return None

            df = pd.read_csv(filepath, usecols=wanted, dtype=str,
                             low_memory=False)

        elif suffix in (".dta",):
            # For Stata files, read all then select
            # Stata files can be large — use chunksize reading if needed
            if size_mb > 200:
                print(f"    Large file ({size_mb}MB) — reading in chunks...")
                chunks = []
                for chunk in pd.read_stata(filepath, chunksize=50000):
                    chunks.append(chunk)
                df = pd.concat(chunks, ignore_index=True)
            else:
                df = pd.read_stata(filepath)
            df = df.astype(str)

        else:
            print(f"    Unsupported format: {suffix}")
            return None

        df.columns = df.columns.str.upper()  # normalize to uppercase
        df["SURVEY_YEAR"] = year
        print(f"    -> {len(df):,} respondents, {len(df.columns)} columns")
        return df

    except Exception as e:
        print(f"    ERROR: {e}")
        return None


def compute_age_cliff(df: pd.DataFrame, year: str) -> pd.DataFrame:
    """
    Women % by age group for computing occupations (N2OCPRMG=1).
    Uses AGEGR (5-year groups: 20,25,30,35...) confirmed from epcg19.
    Weighted by WTSURVY.
    """
    sex_col = find_col(df, "sex") or "SEX"
    age_col = find_col(df, "age_group") or "AGEGR"
    occ_col = find_col(df, "occupation") or "N2OCPRMG"
    wt_col  = find_col(df, "weight") or "WTSURVY"

    missing = [v for v in [sex_col, occ_col] if v not in df.columns]
    if missing:
        print(f"    WARNING: Missing columns: {missing}")
        return pd.DataFrame()

    # Filter to computing occupations (N2OCPRMG == 1)
    comp_df = df[pd.to_numeric(df[occ_col], errors="coerce") == 1].copy()
    if len(comp_df) == 0:
        print(f"    WARNING: No N2OCPRMG=1 records. Unique values: {df[occ_col].unique()[:10]}")
        return pd.DataFrame()

    comp_df["is_woman"] = (comp_df[sex_col].astype(str).str.upper() == "F").astype(int)
    comp_df["wt"] = pd.to_numeric(comp_df[wt_col], errors="coerce").fillna(1) if wt_col in comp_df.columns else 1

    # Map AGEGR 5-yr codes to readable brackets
    if age_col in comp_df.columns:
        comp_df["agegr_num"] = pd.to_numeric(comp_df[age_col], errors="coerce")
        comp_df["age_bracket"] = comp_df["agegr_num"].map(AGE_GROUP_LABELS).fillna("Unknown")
    else:
        comp_df["age_bracket"] = "Unknown"

    records = []
    bracket_order = ["Under 25", "25-34", "35-44", "45-54", "55-64", "65+"]
    for bracket in bracket_order:
        grp = comp_df[comp_df["age_bracket"] == bracket]
        if len(grp) == 0:
            continue
        total_wt = grp["wt"].sum()
        women_wt = grp.loc[grp["is_woman"] == 1, "wt"].sum()
        records.append({
            "year":       int(year),
            "age_bracket": bracket,
            "total_n":    len(grp),
            "women_n":    int(grp["is_woman"].sum()),
            "total_wt":   round(total_wt, 0),
            "pct_women":  round(women_wt / total_wt * 100, 1) if total_wt > 0 else np.nan,
        })

    return pd.DataFrame(records)


def compute_field_trends(df: pd.DataFrame, year: str) -> pd.DataFrame:
    """Women % by field of bachelor's degree over time (pipeline entry)."""
    sex_col   = find_col(df, "sex")
    field_col = find_col(df, "field_ba")
    wt_col    = find_col(df, "weight")

    if not sex_col or not field_col:
        return pd.DataFrame()

    df = df.copy()
    df["is_woman"] = df[sex_col].astype(str).isin({str(v) for v in SEX_FEMALE}).astype(int)
    df["weight"]   = pd.to_numeric(df.get(wt_col, pd.Series(1, index=df.index)),
                                   errors="coerce").fillna(1)

    records = []
    for field, grp in df.groupby(field_col):
        total_wt = grp["weight"].sum()
        women_wt = grp.loc[grp["is_woman"] == 1, "weight"].sum()
        records.append({
            "year":          int(year),
            "field_code":    str(field),
            "total_n":       len(grp),
            "women_n":       int(grp["is_woman"].sum()),
            "pct_women":     round(women_wt / total_wt * 100, 1) if total_wt > 0 else np.nan,
        })

    return pd.DataFrame(records)


def compute_salary_gap(df: pd.DataFrame, year: str) -> pd.DataFrame:
    """Median salary gap between women and men in computing occupations."""
    sex_col    = find_col(df, "sex")
    occ_col    = find_col(df, "occupation")
    salary_col = find_col(df, "salary")

    if not all([sex_col, occ_col, salary_col]):
        return pd.DataFrame()

    df = df.copy()
    # Filter for computing occupation (N2OCPRMG == 1)
    comp_df = df[pd.to_numeric(df[occ_col], errors="coerce") == 1].copy()
    comp_df["is_woman"]  = comp_df[sex_col].astype(str).isin({str(v) for v in SEX_FEMALE})
    comp_df["salary_num"] = pd.to_numeric(comp_df[salary_col], errors="coerce")
    comp_df = comp_df[comp_df["salary_num"] > 0]

    records = []
    for sex, grp in comp_df.groupby("is_woman"):
        records.append({
            "year":        int(year),
            "sex":         "Women" if sex else "Men",
            "median_salary": grp["salary_num"].median(),
            "n":           len(grp),
        })

    result = pd.DataFrame(records)
    if len(result) == 2:
        women_sal = result.loc[result.sex == "Women", "median_salary"].values
        men_sal   = result.loc[result.sex == "Men",   "median_salary"].values
        if len(women_sal) and len(men_sal):
            result["salary_ratio"] = women_sal[0] / men_sal[0]

    return result


# ── Variable audit helper ─────────────────────────────────────────────────────
def write_variable_audit(df: pd.DataFrame, year: str, filepath: Path):
    """Write a summary of found columns for manual verification."""
    lines = [f"NSCG {year} — Variable Audit", "=" * 50]
    lines.append(f"Total columns: {len(df.columns)}")
    lines.append(f"Total rows: {len(df):,}")
    lines.append("")
    lines.append("KEY VARIABLE MAPPING:")
    for varname in VAR_ALIASES:
        col = find_col(df, varname)
        if col:
            sample = df[col].dropna().value_counts().head(5).to_dict()
            lines.append(f"  {varname:15s} -> {col:20s}  sample values: {sample}")
        else:
            lines.append(f"  {varname:15s} -> NOT FOUND")
    lines.append("")
    lines.append("ALL COLUMNS:")
    for c in sorted(df.columns):
        lines.append(f"  {c}")

    with open(filepath, "w") as f:
        f.write("\n".join(lines))
    print(f"    -> Variable audit: {filepath}")


# ── 2019 vs 2023 diff analysis ────────────────────────────────────────────────
def compute_wave_diff(age_cliff_all: pd.DataFrame) -> pd.DataFrame:
    """
    Compare 2019 -> 2023 pct_women change by age bracket.
    Negative = women's share shrank (bad). Positive = grew (good).
    This is the core pre/post-COVID leaky pipeline comparison.
    """
    if set(age_cliff_all["year"].unique()) < {2019, 2023}:
        return pd.DataFrame()

    y2019 = age_cliff_all[age_cliff_all["year"] == 2019].set_index("age_bracket")
    y2023 = age_cliff_all[age_cliff_all["year"] == 2023].set_index("age_bracket")

    diff = pd.DataFrame({
        "pct_women_2019": y2019["pct_women"],
        "pct_women_2023": y2023["pct_women"],
    }).dropna()
    diff["change_pp"] = (diff["pct_women_2023"] - diff["pct_women_2019"]).round(1)
    diff["direction"] = diff["change_pp"].apply(
        lambda x: "v worse" if x < -0.5 else ("^ better" if x > 0.5 else "-> flat")
    )
    return diff.reset_index()


def compute_intersectional_cliff(df: pd.DataFrame, year: str) -> pd.DataFrame:
    """
    Women % by age bracket AND race/ethnicity in computing.
    Reveals which groups drive the pipeline leak.
    """
    occ_col  = find_col(df, "occupation") or "N2OCPRMG"
    sex_col  = find_col(df, "sex") or "SEX"
    age_col  = find_col(df, "age_group") or "AGEGR"
    race_col = find_col(df, "race_eth") or "RACETHM"
    wt_col   = find_col(df, "weight") or "WTSURVY"

    if any(c not in df.columns for c in [occ_col, sex_col, race_col]):
        return pd.DataFrame()

    comp = df[pd.to_numeric(df[occ_col], errors="coerce") == 1].copy()
    comp["is_woman"]   = (comp[sex_col].astype(str).str.upper() == "F").astype(int)
    comp["wt"]         = pd.to_numeric(comp.get(wt_col, pd.Series(1, index=comp.index)),
                                       errors="coerce").fillna(1)
    comp["race_label"] = pd.to_numeric(comp[race_col], errors="coerce").map(RACE_LABELS)
    comp["agegr_num"]  = pd.to_numeric(comp[age_col], errors="coerce")
    comp["age_bracket"] = comp["agegr_num"].map(AGE_GROUP_LABELS).fillna("Unknown")

    records = []
    for race, rgrp in comp.groupby("race_label"):
        if len(rgrp) < 30:   # suppress small cells
            continue
        for bracket in ["Under 25", "25-34", "35-44", "45-54", "55-64", "65+"]:
            bgrp = rgrp[rgrp["age_bracket"] == bracket]
            if len(bgrp) < 15:
                continue
            tw = bgrp["wt"].sum()
            ww = bgrp.loc[bgrp["is_woman"] == 1, "wt"].sum()
            records.append({
                "year": int(year), "race": race, "age_bracket": bracket,
                "n": len(bgrp), "pct_women": round(ww / tw * 100, 1),
            })
    return pd.DataFrame(records)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("NSCG Public Use File — Preprocessing (2019 & 2023)")
    print("Two-wave panel: pre/post-COVID comparison")
    print("=" * 65)

    # Search for epcg CSVs anywhere under ncses_datasets/
    # Handles: ncses_datasets/epcg19.csv  OR  ncses_datasets/gss/epcg19.csv
    direct_csvs = sorted(RAW_DIR.rglob("epcg*.csv")) + \
                  sorted(RAW_DIR.rglob("EPCG*.csv"))
    direct_csvs = list(dict.fromkeys(direct_csvs))  # deduplicate

    if not direct_csvs:
        print(f"\nWARNING: No epcg*.csv files found under {RAW_DIR}/")
        print("  Expected: epcg19.csv and epcg23.csv")
        print("  Place them anywhere under ncses_datasets/ (subfolders OK)")
        return

    print(f"\n  Found {len(direct_csvs)} NSCG CSV files:")
    extracted = []
    for f in direct_csvs:
        stem = f.stem.lower().replace("epcg", "")
        year = f"20{stem}" if len(stem) == 2 else stem
        print(f"    {f.relative_to(RAW_DIR)}  -> year {year}")
        extracted.append((year, f))

    age_cliff_frames       = []
    field_trend_frames     = []
    salary_gap_frames      = []
    intersectional_frames  = []

    print(f"\n[2/5] Processing {len(extracted)} wave files...")
    for year, filepath in sorted(extracted):
        print(f"\n  [{year}]  {filepath.name}")
        df = load_nscg_file(filepath, year)
        if df is None:
            continue

        write_variable_audit(df, year, OUT_DIR / f"nscg_variable_audit_{year}.txt")

        age_cliff = compute_age_cliff(df, year)
        if not age_cliff.empty:
            age_cliff_frames.append(age_cliff)

        field_trend = compute_field_trends(df, year)
        if not field_trend.empty:
            field_trend_frames.append(field_trend)

        salary_gap = compute_salary_gap(df, year)
        if not salary_gap.empty:
            salary_gap_frames.append(salary_gap)

        intersect = compute_intersectional_cliff(df, year)
        if not intersect.empty:
            intersectional_frames.append(intersect)

    print(f"\n[3/5] Saving per-wave outputs...")

    if age_cliff_frames:
        age_cliff_all = pd.concat(age_cliff_frames, ignore_index=True)
        age_cliff_all.to_csv(OUT_DIR / "nscg_age_cliff_computing.csv", index=False)
        print(f"  -> nscg_age_cliff_computing.csv ({len(age_cliff_all)} rows)")

    if field_trend_frames:
        field_all = pd.concat(field_trend_frames, ignore_index=True)
        field_all.to_csv(OUT_DIR / "nscg_field_trends.csv", index=False)
        print(f"  -> nscg_field_trends.csv ({len(field_all)} rows)")

    if salary_gap_frames:
        sal_all = pd.concat(salary_gap_frames, ignore_index=True)
        sal_all.to_csv(OUT_DIR / "nscg_salary_gap_computing.csv", index=False)
        print(f"  -> nscg_salary_gap_computing.csv ({len(sal_all)} rows)")

    if intersectional_frames:
        int_all = pd.concat(intersectional_frames, ignore_index=True)
        int_all.to_csv(OUT_DIR / "nscg_intersectional_cliff.csv", index=False)
        print(f"  -> nscg_intersectional_cliff.csv ({len(int_all)} rows)")

    print(f"\n[4/5] 2019 -> 2023 diff analysis...")
    if len(age_cliff_frames) == 2:
        age_cliff_all = pd.concat(age_cliff_frames, ignore_index=True)
        diff = compute_wave_diff(age_cliff_all)
        if not diff.empty:
            diff.to_csv(OUT_DIR / "nscg_2019_2023_diff.csv", index=False)
            print(f"  -> nscg_2019_2023_diff.csv")
            print()
            print(f"  {'Age bracket':<12} {'2019':>6} {'2023':>6} {'Delta pp':>6}  {'':>10}")
            for _, row in diff.iterrows():
                print(f"  {row['age_bracket']:<12} "
                      f"{row['pct_women_2019']:>5.1f}% "
                      f"{row['pct_women_2023']:>5.1f}% "
                      f"{row['change_pp']:>+5.1f}pp  {row['direction']}")

    print(f"\n[5/5] Summary:")
    if age_cliff_frames:
        latest = max(age_cliff_frames, key=lambda d: d["year"].max())
        yr = latest["year"].max()
        print(f"\n  Computing workforce women % by age ({yr}):")
        for _, row in latest.sort_values("age_bracket").iterrows():
            bar = "#" * int(row["pct_women"] / 2)
            print(f"    {row['age_bracket']:<10}: {row['pct_women']:5.1f}%  {bar}")

    print(f"\nOK: Done. Outputs in {OUT_DIR}/")

    print(f"\nOK: Done. Outputs in {OUT_DIR}/")


if __name__ == "__main__":
    main()